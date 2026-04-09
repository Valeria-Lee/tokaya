import uuid
from sqlalchemy import Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class InventoryItem(Base):
    """
    Inventory items owned by a Tokayo.
    
    Ownership chain: User → Tokayo → InventoryItem.
    The `user_id` column is kept as a denormalized convenience field so that
    queries like "give me all items for user X" don't require a join,
    but the authoritative ownership FK is `tokayo_id`.

    equipped — whether this item slot is currently active on the Tokayo
               (e.g. a hat being worn, a hammer being held).
    """

    __tablename__ = "inventory_item"

    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Denormalized for convenience — mirrors Tokayo.owned_by_user
    user_id: Mapped[str] = mapped_column(
        # Not a FK — user lives outside this app (auth handled by API Gateway)
        nullable=False,
        index=True,
    )

    # Authoritative ownership: inventory belongs to a Tokayo
    tokayo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tokayo.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    equipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    tokayo: Mapped["Tokayo"] = relationship("Tokayo", back_populates="inventory_items")

    def __repr__(self) -> str:
        return (
            f"<InventoryItem uuid={self.uuid} tokayo_id={self.tokayo_id} "
            f"qty={self.quantity} equipped={self.equipped}>"
        )
