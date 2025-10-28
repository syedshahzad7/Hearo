from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Text, Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .session import Session


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True, nullable=False)

    seq: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # chunk order
    speaker: Mapped[str | None]  # optional speaker label
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Must match Session.transcript_chunks back_populates="session"
    session: Mapped["Session"] = relationship(back_populates="transcript_chunks")
