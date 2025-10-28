import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.session import get_db
from app.core.config import Settings
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.session import Session

settings = Settings()
router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=dict)
async def create_session(
    title: Annotated[str | None, Form()] = None,
    role: Annotated[str, Form()] = "student",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = Session(owner_id=user.id, title=title, role=role, status="created")
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": s.id, "title": s.title, "role": s.role, "status": s.status}

@router.post("/{session_id}/upload", response_model=dict)
async def upload_audio(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Ensure session exists and belongs to user
    result = await db.execute(select(Session).where(Session.id == session_id, Session.owner_id == user.id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save file
    upload_dir = Path(settings.UPLOAD_DIR) / user.id / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    # keep original extension
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    dest = upload_dir / f"audio{ext}"

    # write in chunks
    with dest.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    # update session
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(audio_path=str(dest), status="uploaded")
    )
    await db.commit()

    return {"id": session_id, "audio_path": str(dest), "status": "uploaded"}

@router.get("", response_model=list[dict])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Session).where(Session.owner_id == user.id).order_by(Session.created_at.desc()))
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
