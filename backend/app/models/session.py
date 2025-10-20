from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import uuid4
from app.db.session import Base

class MeetingSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    title: Mapped[str | None] = mapped_column(String(255))
    context: Mapped[str] = mapped_column(String(32), default="class")  # "class" | "meeting"
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    owner: Mapped["User"] = relationship(back_populates="sessions")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(back_populates="session", cascade="all,delete")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="session", cascade="all,delete")
