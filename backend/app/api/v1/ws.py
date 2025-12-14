# backend/app/api/v1/ws.py
from __future__ import annotations

import os
import asyncio
import subprocess
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from faster_whisper import WhisperModel

from app.core.config import Settings
from app.db.session import get_db
from app.models.session import Session
from app.models.transcript import TranscriptChunk

router = APIRouter()
settings = Settings()

# Load Whisper once per process
_whisper_model = WhisperModel(
    settings.WHISPER_MODEL,
    device=settings.WHISPER_DEVICE,
    compute_type=settings.WHISPER_COMPUTE_TYPE,
)


def _get_user_id_from_token(token: str) -> Optional[str]:
    """Return user id (sub) if token is valid, else None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None


async def _acquire_db() -> tuple[AsyncSession, any]:
    """Get AsyncSession from get_db() dependency generator."""
    agen = get_db()
    db = await agen.__anext__()
    return db, agen


def _ffmpeg_to_wav(input_webm: str, output_wav: str) -> None:
    """
    Convert webm/opus -> 16k mono wav (Whisper-friendly).
    Requires ffmpeg in PATH.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_webm,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        output_wav,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "ffmpeg failed")


def _transcribe_segments(wav_path: str) -> list[str]:
    """Returns list of segment texts from Whisper."""
    segments, _info = _whisper_model.transcribe(wav_path, vad_filter=True)
    out: list[str] = []
    for s in segments:
        t = (s.text or "").strip()
        if t:
            out.append(t)
    return out


@router.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket):
    """
    Connect:
      ws://127.0.0.1:8000/api/v1/ws/transcribe?session_id=...&token=ACCESS_TOKEN

    Client sends:
      - binary frames (MediaRecorder chunks: webm/opus)
      - text "end" to finish (recommended)
      - optional "ping" keepalive

    Server:
      - writes uploads/<user_id>/<session_id>/live_capture.webm
      - on end: converts to live_capture.wav, transcribes, stores TranscriptChunk rows
      - ALSO streams back transcript chunks:
          {"type":"partial","seq":1,"text":"..."}
    """
    await websocket.accept()

    token = websocket.query_params.get("token")
    session_id = websocket.query_params.get("session_id")
    user_id = _get_user_id_from_token(token) if token else None

    if not user_id or not session_id:
        await websocket.close(code=4403)
        return

    db, agen = await _acquire_db()
    try:
        # Verify session belongs to user
        result = await db.execute(
            select(Session).where(Session.id == session_id, Session.owner_id == user_id)
        )
        sess: Session | None = result.scalar_one_or_none()
        if not sess:
            await websocket.close(code=4404)
            return

        # Prepare output paths
        user_dir = os.path.join(settings.UPLOAD_DIR, user_id, session_id)
        os.makedirs(user_dir, exist_ok=True)

        webm_path = os.path.join(user_dir, "live_capture.webm")
        wav_path = os.path.join(user_dir, "live_capture.wav")

        # Overwrite each run
        f = open(webm_path, "wb")

        await websocket.send_json({"type": "ready", "session_id": session_id})

        ended_normally = False

        try:
            while True:
                message = await websocket.receive()

                # client disconnect
                if message.get("type") == "websocket.disconnect":
                    break

                # text control
                txt = message.get("text")
                if txt is not None:
                    if txt == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue
                    if txt == "end":
                        ended_normally = True
                        break
                    continue

                # binary audio chunk
                b = message.get("bytes")
                if b is not None:
                    f.write(b)
                    f.flush()
                    continue

        except WebSocketDisconnect:
            pass
        finally:
            try:
                f.close()
            except Exception:
                pass

        # If nothing was written, bail early
        if not os.path.exists(webm_path) or os.path.getsize(webm_path) == 0:
            try:
                await websocket.send_json({"type": "error", "message": "empty_capture"})
            except Exception:
                pass
            return

        # Update session -> processing
        await db.execute(
            update(Session).where(Session.id == session_id).values(status="processing")
        )
        await db.commit()

        try:
            await websocket.send_json({"type": "status", "value": "processing"})
        except Exception:
            pass

        # Convert and transcribe OFF the event loop
        def _work() -> list[str]:
            _ffmpeg_to_wav(webm_path, wav_path)
            return _transcribe_segments(wav_path)

        try:
            texts: list[str] = await asyncio.to_thread(_work)
        except Exception as e:
            await db.execute(
                update(Session).where(Session.id == session_id).values(status="failed")
            )
            await db.commit()
            try:
                await websocket.send_json(
                    {"type": "error", "message": "transcribe_failed", "detail": str(e)}
                )
            except Exception:
                pass
            return

        # Replace transcript chunks for this session to avoid duplicates
        await db.execute(delete(TranscriptChunk).where(TranscriptChunk.session_id == session_id))

        # Save to DB AND stream partials to frontend
        seq = 1
        for t in texts:
            db.add(TranscriptChunk(session_id=session_id, seq=seq, speaker=None, text=t))
            # stream to client so it appears in UI
            try:
                await websocket.send_json({"type": "partial", "seq": seq, "text": t})
            except Exception:
                # if client disconnected mid-way, still continue saving
                pass
            seq += 1

        # Set audio_path to WAV and status to done
        await db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(audio_path=wav_path, status="done")
        )
        await db.commit()

        # Done
        try:
            await websocket.send_json(
                {"type": "done", "chunks": len(texts), "ended": ended_normally}
            )
        except Exception:
            pass

    finally:
        try:
            await agen.aclose()
        except Exception:
            pass
