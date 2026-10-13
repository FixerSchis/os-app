import json

from models.extensions import db


class Medicament(db.Model):
    __tablename__ = "medicaments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wiki_slug = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(200), nullable=True)
    effect = db.Column(db.Text, nullable=True)
    modes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Medicament {self.name}>"

    @property
    def modes_list(self):
        """Each dose uses one mode, given as {"name": ..., "effect": ...}."""
        return json.loads(self.modes) if self.modes else []

    @modes_list.setter
    def modes_list(self, values):
        self.modes = json.dumps(values) if values else None
