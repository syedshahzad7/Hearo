from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:  # only for type hints; avoids import cycles at runtime
    from .user import User
    from .transcript import TranscriptChunk
    from .summary import Summary


def gen_uuid() -> str:
    return str(uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)

    title: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="student")  # or "professional"
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # upload / processing
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="created")  # created|uploaded|processing|done|failed

    # Relationships (names must match back_populates on the other side)
    owner: Mapped["User"] = relationship(back_populates="sessions")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(
        back_populates="session", cascade="all,delete"
    )
    summaries: Mapped[list["Summary"]] = relationship(
        back_populates="session", cascade="all,delete"
    )
