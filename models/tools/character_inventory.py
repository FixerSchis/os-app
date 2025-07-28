from datetime import datetime, timezone
from enum import Enum

from models.extensions import db
from models.tools.character import Character


class ItemTransferStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class CharacterItem(db.Model):
    """Model for items assigned to characters."""

    __tablename__ = "character_items"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    character = db.relationship("Character", back_populates="inventory_items")
    item = db.relationship("Item")
    assigned_by = db.relationship("User")

    __table_args__ = (db.UniqueConstraint("character_id", "item_id", name="uix_character_item"),)

    def __repr__(self):
        return f"<CharacterItem {self.character.name} -> {self.item.full_code}>"


class ItemTransferRequest(db.Model):
    """Model for item transfer requests between characters."""

    __tablename__ = "item_transfer_requests"

    id = db.Column(db.Integer, primary_key=True)
    requesting_character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    target_character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    status = db.Column(
        db.Enum(
            ItemTransferStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ItemTransferStatus.PENDING,
    )
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    requesting_character = db.relationship("Character", foreign_keys=[requesting_character_id])
    target_character = db.relationship("Character", foreign_keys=[target_character_id])
    processed_by = db.relationship("User")
    items = db.relationship(
        "ItemTransferRequestItem", back_populates="transfer_request", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ItemTransferRequest {self.requesting_character.name} -> "
            f"{self.target_character.name}>"
        )


class ItemTransferRequestItem(db.Model):
    """Model for items included in transfer requests."""

    __tablename__ = "item_transfer_request_items"

    id = db.Column(db.Integer, primary_key=True)
    transfer_request_id = db.Column(
        db.Integer, db.ForeignKey("item_transfer_requests.id"), nullable=False
    )
    character_item_id = db.Column(db.Integer, db.ForeignKey("character_items.id"), nullable=False)

    # Relationships
    transfer_request = db.relationship("ItemTransferRequest", back_populates="items")
    character_item = db.relationship("CharacterItem")

    def __repr__(self):
        return f"<ItemTransferRequestItem {self.character_item.item.full_code}>"
