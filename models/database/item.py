import math

from models.extensions import db

item_mods_applied = db.Table(
    "item_mods_applied",
    db.Column("item_id", db.Integer, db.ForeignKey("item.id"), primary_key=True),
    db.Column("mod_id", db.Integer, db.ForeignKey("mods.id"), primary_key=True),
    db.Column("count", db.Integer, nullable=False, default=1),
)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blueprint_id = db.Column(db.Integer, db.ForeignKey("item_blueprints.id"), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    printed = db.Column(db.Boolean, nullable=False, default=False)

    blueprint = db.relationship("ItemBlueprint", back_populates="items")
    mods_applied = db.relationship("Mod", secondary=item_mods_applied, backref="items_applied")
    audit_logs = db.relationship("ItemAuditLog", back_populates="item")

    __table_args__ = (db.UniqueConstraint("blueprint_id", "item_id", name="uix_blueprint_itemid"),)

    def __repr__(self):
        return f"<Item {self.blueprint_id}-{self.item_id}>"

    @property
    def full_code(self):
        return f"{self.blueprint.full_code}-{self.item_id:03d}"

    @property
    def total_mods(self):
        # Count only applied mods
        rows = db.session.execute(
            item_mods_applied.select().where(item_mods_applied.c.item_id == self.id)
        ).fetchall()
        applied_mods = sum(row.count for row in rows)
        return applied_mods

    def base_cost_calc(self, additional_mods=0):
        if not self.blueprint or not self.blueprint.base_cost:
            return None
        cost = self.blueprint.base_cost * math.exp((self.total_mods + additional_mods) / 2.5)
        return math.ceil(cost)

    def get_maintenance_cost(self, additional_mods=0):
        return math.ceil(self.base_cost_calc(additional_mods) * 0.1)

    def get_modification_cost(self, additional_mods=0):
        return math.ceil(self.base_cost_calc(additional_mods) * 0.5)

    def is_expired(self):
        """Check if the item is expired based on current event number."""
        if self.expiry is None:
            return False

        from datetime import datetime

        from models.event import Event

        # Get the most recent event that has ended
        previous_event = (
            Event.query.filter(Event.end_date <= datetime.now())
            .order_by(Event.end_date.desc())
            .first()
        )

        if not previous_event:
            return False

        try:
            current_event_number = int(previous_event.event_number)
            return current_event_number > self.expiry
        except (ValueError, TypeError):
            return False

    def increment_version(self, editor_user_id, reason):
        """Increment the item version and mark as not printed."""
        self.version += 1
        self.printed = False

        # Create audit log
        from models.enums import ItemAuditAction

        audit_log = ItemAuditLog(
            item_id=self.id,
            editor_user_id=editor_user_id,
            action=ItemAuditAction.VERSION_INCREMENT.value,
            changes=f"Version incremented to {self.version}: {reason}",
        )
        db.session.add(audit_log)

    def mark_as_printed(self, editor_user_id):
        """Mark the item as printed."""
        self.printed = True

        # Create audit log
        from models.enums import ItemAuditAction

        audit_log = ItemAuditLog(
            item_id=self.id,
            editor_user_id=editor_user_id,
            action=ItemAuditAction.PRINTED.value,
            changes="Item marked as printed",
        )
        db.session.add(audit_log)


class ItemAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    editor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    action = db.Column(
        db.Enum(
            "create",
            "edit",
            "version_increment",
            "printed",
            "mods_changed",
            "expiry_changed",
            "blueprint_changed",
            name="itemauditaction",
            native_enum=False,
        ),
        nullable=False,
    )
    changes = db.Column(db.Text, nullable=True)

    item = db.relationship("Item", back_populates="audit_logs")
    editor = db.relationship("User")

    def __repr__(self):
        return f"<ItemAuditLog {self.action} by {self.editor.email}>"
