from sqlalchemy import Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4
from app.db.session import Base

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True, nullable=False)
    seq: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # chunk order
    speaker: Mapped[str | None]  # optional speaker label
    text: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["MeetingSession"] = relationship(back_populates="transcript_chunks")
