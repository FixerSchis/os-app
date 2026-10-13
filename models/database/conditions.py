import json
from datetime import datetime, timezone

from models.database.rule_tag import condition_rule_tags
from models.extensions import db


class ConditionStage(db.Model):
    __tablename__ = "condition_stages"

    id = db.Column(db.Integer, primary_key=True)
    condition_id = db.Column(db.Integer, db.ForeignKey("conditions.id"), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)
    rp_effect = db.Column(db.String(500), nullable=False)
    diagnosis = db.Column(db.String(500), nullable=False)
    cure = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Number of events

    # Relationship
    condition = db.relationship("Condition", back_populates="stages")

    __table_args__ = (
        db.UniqueConstraint("condition_id", "stage_number", name="uix_condition_stage_number"),
    )

    def __repr__(self):
        return f"<ConditionStage {self.stage_number} of {self.condition.name}>"


class Condition(db.Model):
    __tablename__ = "conditions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    progresses_naturally = db.Column(
        db.Boolean, nullable=False, default=True, server_default=db.true()
    )
    stage_sheet_values = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # Relationship
    stages = db.relationship(
        "ConditionStage", back_populates="condition", cascade="all, delete-orphan"
    )
    tags = db.relationship("RuleTag", secondary=condition_rule_tags, order_by="RuleTag.name")

    def __repr__(self):
        return f"<Condition {self.name}>"

    @property
    def stage_sheet_values_list(self):
        """Character sheet values granted once per stage the character has reached."""
        return json.loads(self.stage_sheet_values) if self.stage_sheet_values else []

    @stage_sheet_values_list.setter
    def stage_sheet_values_list(self, values):
        self.stage_sheet_values = json.dumps(values) if values else None

    @property
    def max_stage(self):
        return max((stage.stage_number for stage in self.stages), default=0)
