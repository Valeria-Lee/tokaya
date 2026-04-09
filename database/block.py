import uuid as uuid_pkg     
from datetime import datetime                                  # ← ESTA es la que cambias
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID               # ← ESTA se queda IGUAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Block(Base):
    """
    Block catalog — available block types that can be placed in a Tokayo's
    base (Tokarena) or purchased from the store.

    x_pos / y_pos describe the block's default or catalog position
    (actual placed positions are stored in a separate placed_blocks join table
    when implementing Tokarena grid logic).

    durability  — how many hits the block can take before being destroyed.
    price       — cost in internal points from the store.
    """

    __tablename__ = "block"

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4
)  
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    # Grid / catalog position
    x_pos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    y_pos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Combat stats
    durability: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Store price in internal points
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<Block uuid={self.uuid} name={self.name!r} "
            f"durability={self.durability} price={self.price}>"
        )
