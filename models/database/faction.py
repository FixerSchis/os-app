from ..extensions import db


class Faction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    wiki_slug = db.Column(db.String(100), nullable=False, unique=True)
    allow_player_characters = db.Column(db.Boolean, default=False)

    # Relationships
    characters = db.relationship("Character", back_populates="faction")

    def __repr__(self):
        return f"<Faction {self.name}>"

    @classmethod
    def get_by_slug(cls, slug):
        return cls.query.filter_by(wiki_slug=slug).first()

    @classmethod
    def get_all(cls):
        return cls.query.order_by(cls.name).all()

    @classmethod
    def get_player_factions(cls):
        return cls.query.filter_by(allow_player_characters=True).order_by(cls.name).all()
