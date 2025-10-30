from __future__ import annotations

import os
from typing import Iterable, List, Tuple

from faster_whisper import WhisperModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models.session import Session
from app.models.transcript import TranscriptChunk

# Lazy singleton model (loaded on first use)
_model: WhisperModel | None = None

def get_model(settings: Settings) -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _model

async def transcribe_session_audio(db: AsyncSession, session_id: str, settings: Settings) -> None:
    """
    Loads the session + audio file, runs STT with faster-whisper,
    writes TranscriptChunk rows, and updates session.status.
    """
    # Load session & ensure we have an audio_path
    result = await db.execute(
        select(Session).options(selectinload(Session.transcript_chunks)).where(Session.id == session_id)
    )
    s: Session | None = result.scalar_one_or_none()
    if not s or not s.audio_path or not os.path.isfile(s.audio_path):
        return  # nothing to do (or session deleted)

    # mark processing
    s.status = "processing"
    await db.commit()

    try:
        model = get_model(settings)

        # Run transcription (segments yields text + timestamps)
        segments, _info = model.transcribe(
            s.audio_path,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Clear any previous chunks (idempotency for re-run)
        if s.transcript_chunks:
            for tc in s.transcript_chunks:
                await db.delete(tc)
            await db.flush()

        seq = 0
        to_add: list[TranscriptChunk] = []
        for seg in segments:  # type: ignore
            text = (seg.text or "").strip()
            if not text:
                continue
            seq += 1
            to_add.append(
                TranscriptChunk(
                    session_id=s.id,
                    seq=seq,
                    speaker=None,
                    text=text,
                )
            )

        db.add_all(to_add)
        s.status = "done"
        await db.commit()

    except Exception:
        # don’t crash server: mark failed
        s.status = "failed"
        await db.commit()
