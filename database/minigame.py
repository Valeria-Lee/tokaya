import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Minigame(Base):
    """
    A Tiki Toka minigame session record.

    exp_date    — when this minigame session expires (client must complete before this).
    completed   — whether the player finished the game.
    won         — whether the player met the score_goal.
    score_goal  — the target score to beat; sent to the client at session start
                  and validated server-side on completion.
    """

    __tablename__ = "minigame"

    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    exp_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    won: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score_goal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<Minigame uuid={self.uuid} name={self.name!r} "
            f"completed={self.completed} won={self.won}>"
        )
