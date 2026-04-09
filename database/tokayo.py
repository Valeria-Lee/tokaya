import uuid as uuid_pkg        
from datetime import datetime                               # ← ESTA es la que cambias
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID               # ← ESTA se queda IGUAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Tokayo(Base):
    """
    A Tokayo is a virtual creature owned by a user.
    Users are identified by their external user_id (auth is handled
    outside this application via API Gateway — no User table here).
    Stats: kindness, strength, happiness, luck track the creature's growth.
    Combat stats: destroyed_bases, tokayos_helped track arena activity.
    """

    __tablename__ = "tokayo"

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4
)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owned_by_user: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,  # one Tokayo per user
        index=True,
    )

    # Stats
    kindness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    happiness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    luck: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Arena tracking
    destroyed_bases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokayos_helped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="tokayo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tokayo uuid={self.uuid} name={self.name!r} owner={self.owned_by_user!r}>"
