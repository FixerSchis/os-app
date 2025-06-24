from sqlalchemy import JSON

from models.enums import GroupAuditAction
from models.extensions import db


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_type_id = db.Column(db.Integer, db.ForeignKey("group_types.id"), nullable=False)
    bank_account = db.Column(db.Integer, nullable=False, default=0)
    group_pack = db.Column(db.String, nullable=True)  # JSON string
    pack_complete = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    group_type = db.relationship("GroupType", back_populates="groups")
    characters = db.relationship("Character", back_populates="group", lazy=True)
    invites = db.relationship("GroupInvite", back_populates="group", cascade="all, delete-orphan")
    samples = db.relationship("Sample", back_populates="group", lazy="dynamic")
    audit_logs = db.relationship("GroupAuditLog", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"

    def add_funds(self, amount, editor_user_id, reason):
        """Add funds to the group's bank account with audit logging."""
        self.bank_account += amount

        # Create an audit log for the addition
        audit_log = GroupAuditLog(
            group_id=self.id,
            editor_user_id=editor_user_id,
            action=GroupAuditAction.FUNDS_ADDED,
            changes=f"Added {amount} for {reason}",
        )
        db.session.add(audit_log)

    def remove_funds(self, amount, editor_user_id, reason):
        """Remove funds from the group's bank account with audit logging."""
        if self.bank_account < amount:
            raise ValueError("Not enough funds")

        self.bank_account -= amount

        # Create an audit log for the removal
        audit_log = GroupAuditLog(
            group_id=self.id,
            editor_user_id=editor_user_id,
            action=GroupAuditAction.FUNDS_WITHDRAWN,
            changes=f"Removed {amount} for {reason}",
        )
        db.session.add(audit_log)

    def set_funds(self, new_balance, editor_user_id, reason):
        """Set the group's bank account to a specific value with audit logging."""
        old_balance = self.bank_account
        self.bank_account = new_balance
        audit_log = GroupAuditLog(
            group_id=self.id,
            editor_user_id=editor_user_id,
            action=GroupAuditAction.FUNDS_SET,
            changes=f"Funds set from {old_balance} to {new_balance} for {reason}",
        )
        db.session.add(audit_log)

    @property
    def pack(self):
        from models.tools.pack import Pack

        return Pack.from_json(self.group_pack)

    @pack.setter
    def pack(self, pack):
        self.group_pack = pack.to_json()
        self.pack_complete = pack.is_complete()


class GroupInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    group = db.relationship("Group", back_populates="invites")
    character = db.relationship("Character")

    __table_args__ = (
        db.UniqueConstraint("group_id", "character_id", name="uix_group_character_invite"),
    )

    def __repr__(self):
        return f"<GroupInvite {self.group.name} -> {self.character.name}>"


class GroupAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    editor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    action = db.Column(
        db.Enum(
            GroupAuditAction,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
    )
    changes = db.Column(db.Text, nullable=True)

    group = db.relationship("Group", back_populates="audit_logs")
    editor = db.relationship("User")

    def __repr__(self):
        return f"<GroupAuditLog {self.action} by {self.editor.email}>"
