from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Text, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .session import Session


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True, nullable=False)

    style: Mapped[str] = mapped_column(String(32), default="student")  # "student" | "professional"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Must match Session.summaries back_populates="session"
    session: Mapped["Session"] = relationship(back_populates="summaries")
