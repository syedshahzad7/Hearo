import os
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import Settings
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.transcript import TranscriptChunk
from app.services.transcribe import transcribe_session_audio

router = APIRouter(prefix="/sessions", tags=["sessions"])
settings = Settings()


@router.post("", response_model=dict)
async def create_session(
    title: str | None = None,
    role: str = "student",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new session record."""
    s = Session(owner_id=current_user.id, title=title, role=role, status="created")
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {
        "id": s.id,
        "title": s.title,
        "role": s.role,
        "status": s.status,
        "created_at": s.created_at,
    }


@router.post("/{session_id}/upload", response_model=dict)
async def upload_audio(
    session_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an audio file and trigger background transcription."""
    # verify session ownership
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.owner_id == current_user.id)
    )
    s: Session | None = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # ensure upload directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    user_dir = os.path.join(settings.UPLOAD_DIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)

    # save file
    ext = os.path.splitext(file.filename or "")[1] or ".webm"
    fname = f"{uuid4()}{ext}"
    dest = os.path.join(user_dir, fname)

    with open(dest, "wb") as f:
        f.write(await file.read())

    # update DB
    s.audio_path = dest
    s.status = "uploaded"
    await db.commit()

    # trigger background transcription
    background.add_task(transcribe_session_audio, db, s.id, settings)

    return {"id": s.id, "audio_path": s.audio_path, "status": s.status}


@router.get("", response_model=list[dict])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all sessions for the current user."""
    result = await db.execute(
        select(Session)
            .where(Session.owner_id == current_user.id)
            .order_by(Session.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "role": r.role,
            "status": r.status,
            "created_at": str(r.created_at),
            "has_audio": bool(r.audio_path),
        }
        for r in rows
    ]


@router.get("/{session_id}/transcript", response_model=list[dict])
async def get_transcript(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return transcript chunks for a session owned by the current user."""
    # Optionally ensure the session exists & belongs to user (cheap guard)
    sess_q = await db.execute(
        select(Session.id).where(Session.id == session_id, Session.owner_id == current_user.id)
    )
    if not sess_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(TranscriptChunk)
            .where(TranscriptChunk.session_id == session_id)
            .order_by(TranscriptChunk.seq.asc())
    )
    rows = result.scalars().all()
    return [{"seq": r.seq, "speaker": r.speaker, "text": r.text} for r in rows]
