from models.extensions import db

# Association table for many-to-many relationship between Character and Sample
character_samples = db.Table(
    "character_samples",
    db.Column("character_id", db.Integer, db.ForeignKey("character.id"), primary_key=True),
    db.Column("sample_id", db.Integer, db.ForeignKey("sample.id"), primary_key=True),
)
