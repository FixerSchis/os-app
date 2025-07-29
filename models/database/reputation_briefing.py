from datetime import datetime

from models.enums import ReputationBriefingStatus
from models.extensions import db


class ReputationBriefing(db.Model):
    __tablename__ = "reputation_briefings"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    faction_id = db.Column(db.Integer, db.ForeignKey("faction.id"), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(
            ReputationBriefingStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ReputationBriefingStatus.INCOMPLETE,
    )
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    event = db.relationship("Event")
    faction = db.relationship("Faction")
    created_by = db.relationship("User")
    levels = db.relationship(
        "ReputationBriefingLevel", back_populates="briefing", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ReputationBriefing {self.subject} ({self.status.value})>"

    @classmethod
    def get_by_status_order(cls):
        """Get all briefings ordered by status then by date (newest first)."""
        return cls.query.order_by(
            db.case(
                (cls.status == ReputationBriefingStatus.INCOMPLETE.value, 1),
                (cls.status == ReputationBriefingStatus.SUBMITTED.value, 2),
                (cls.status == ReputationBriefingStatus.DISCARDED.value, 3),
            ),
            cls.created_at.desc(),
        ).all()

    def can_edit(self, user):
        """Check if the user can edit this briefing."""
        if user.has_role("plot_team"):
            return self.status == ReputationBriefingStatus.INCOMPLETE
        return False

    def can_view(self, user):
        """Check if the user can view this briefing."""
        if user.has_role("plot_team"):
            return True
        return self.status == ReputationBriefingStatus.SUBMITTED

    def get_eligible_characters(self):
        """Get all active characters that meet the briefing criteria."""
        from models.tools.character import Character, CharacterStatus
        from models.tools.event_ticket import EventTicket

        if not self.levels:
            return []

        # Get the minimum reputation required
        min_reputation = min(level.reputation_required for level in self.levels)

        # Get characters with sufficient reputation in the faction
        eligible_characters = []
        for character in Character.query.filter_by(status=CharacterStatus.ACTIVE.value).all():
            character_reputation = character.get_reputation(self.faction_id)
            if character_reputation >= min_reputation:
                # Check if character has a ticket for this event
                ticket = EventTicket.query.filter_by(
                    event_id=self.event_id, character_id=character.id
                ).first()
                if ticket:
                    eligible_characters.append(character)

        return eligible_characters


class ReputationBriefingLevel(db.Model):
    __tablename__ = "reputation_briefing_levels"

    id = db.Column(db.Integer, primary_key=True)
    briefing_id = db.Column(db.Integer, db.ForeignKey("reputation_briefings.id"), nullable=False)
    reputation_required = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    briefing = db.relationship("ReputationBriefing", back_populates="levels")

    def __repr__(self):
        return f"<ReputationBriefingLevel {self.reputation_required} reputation>"

    @classmethod
    def get_by_briefing_ordered(cls, briefing_id):
        """Get all levels for a briefing ordered by reputation required (ascending)."""
        return (
            cls.query.filter_by(briefing_id=briefing_id)
            .order_by(cls.reputation_required.asc())
            .all()
        )

    def to_dict(self):
        return {
            "id": self.id,
            "briefing_id": self.briefing_id,
            "reputation_required": self.reputation_required,
            "content": self.content,
        }
