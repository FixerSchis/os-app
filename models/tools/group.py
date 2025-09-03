from sqlalchemy import JSON

from models.enums import GroupAuditAction
from models.extensions import db


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_type_id = db.Column(db.Integer, db.ForeignKey("group_types.id"), nullable=False)
    faction_id = db.Column(db.Integer, db.ForeignKey("faction.id"), nullable=False)
    bank_account = db.Column(db.Integer, nullable=False, default=0)
    group_pack = db.Column(db.String, nullable=True)  # JSON string
    pack_complete = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Group background fields
    background = db.Column(db.Text, nullable=True)
    objective = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)

    # Relationships
    group_type = db.relationship("GroupType", back_populates="groups")
    faction = db.relationship("Faction")
    characters = db.relationship("Character", back_populates="group", lazy=True)
    invites = db.relationship("GroupInvite", back_populates="group", cascade="all, delete-orphan")
    samples = db.relationship("Sample", back_populates="group", lazy="dynamic")
    audit_logs = db.relationship("GroupAuditLog", back_populates="group")
    backgrounds = db.relationship("GroupBackground", back_populates="group", lazy="dynamic")
    join_requests = db.relationship(
        "GroupJoinRequest", back_populates="group", cascade="all, delete-orphan"
    )

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

    def deactivate(self, editor_user_id, reason):
        """Deactivate the group with audit logging."""
        self.is_active = False
        audit_log = GroupAuditLog(
            group_id=self.id,
            editor_user_id=editor_user_id,
            action=GroupAuditAction.DEACTIVATED,
            changes=f"Group deactivated: {reason}",
        )
        db.session.add(audit_log)

    def activate(self, editor_user_id, reason):
        """Activate the group with audit logging."""
        self.is_active = True
        audit_log = GroupAuditLog(
            group_id=self.id,
            editor_user_id=editor_user_id,
            action=GroupAuditAction.ACTIVATED,
            changes=f"Group activated: {reason}",
        )
        db.session.add(audit_log)

    @property
    def pack(self):
        from models.tools.pack import Pack

        return Pack.from_json(self.group_pack)

    @pack.setter
    def pack(self, pack):
        self.group_pack = pack.to_json()
        self.pack_complete = pack.is_completed


class GroupBackground(db.Model):
    __tablename__ = "group_backgrounds"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    background = db.Column(db.Text, nullable=True)
    objective = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    needs_review = db.Column(db.Boolean, nullable=False, default=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    group = db.relationship("Group", back_populates="backgrounds")
    reviewed_by = db.relationship("User")

    def __repr__(self):
        return f"<GroupBackground {self.group.name} - Review: {self.needs_review}>"

    @classmethod
    def get_or_create_for_group(cls, group_id):
        """Get existing background or create a new one for the group."""
        background = cls.query.filter_by(group_id=group_id).first()
        if not background:
            background = cls(group_id=group_id)
        return background

    def mark_for_review(self):
        """Mark this background as needing review."""
        self.needs_review = True
        self.reviewed_at = None
        self.reviewed_by_user_id = None

    def mark_as_reviewed(self, reviewer_user_id):
        """Mark this background as reviewed."""
        self.needs_review = False
        self.reviewed_at = db.func.now()
        self.reviewed_by_user_id = reviewer_user_id


class GroupJoinRequest(db.Model):
    __tablename__ = "group_join_requests"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, approved, denied
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    group = db.relationship("Group", back_populates="join_requests")
    character = db.relationship("Character")
    reviewed_by = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("group_id", "character_id", name="uix_group_character_join_request"),
    )

    def __repr__(self):
        return f"<GroupJoinRequest {self.group.name} <- {self.character.name} ({self.status})>"

    def approve(self, reviewer_user_id):
        """Approve the join request."""
        self.status = "approved"
        self.reviewed_at = db.func.now()
        self.reviewed_by_user_id = reviewer_user_id
        # Add character to group
        self.character.group_id = self.group.id

    def deny(self, reviewer_user_id):
        """Deny the join request."""
        self.status = "denied"
        self.reviewed_at = db.func.now()
        self.reviewed_by_user_id = reviewer_user_id


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
