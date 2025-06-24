import json

from models.extensions import db


class GroupType(db.Model):
    __tablename__ = "group_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    income_items = db.Column(db.String, nullable=True)  # JSON list of blueprint IDs
    income_items_discount = db.Column(db.Float, nullable=False, default=0.5)
    income_substances = db.Column(db.Boolean, nullable=False, default=False)
    income_substance_cost = db.Column(db.Integer, nullable=False, default=0)
    income_medicaments = db.Column(db.Boolean, nullable=False, default=False)
    income_medicament_cost = db.Column(db.Integer, nullable=False, default=0)
    income_distribution = db.Column(db.String, nullable=False)  # JSON dict with ratios
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    groups = db.relationship("Group", back_populates="group_type")

    def __repr__(self):
        return f"<GroupType {self.name}>"

    @property
    def income_items_list(self):
        return json.loads(self.income_items) if self.income_items else []

    @income_items_list.setter
    def income_items_list(self, items):
        self.income_items = json.dumps(items) if items else None

    @property
    def income_distribution_dict(self):
        return json.loads(self.income_distribution) if self.income_distribution else {}

    @income_distribution_dict.setter
    def income_distribution_dict(self, distribution):
        self.income_distribution = json.dumps(distribution) if distribution else "{}"
