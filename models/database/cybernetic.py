from models.extensions import db
from models.enums import ScienceType

class Cybernetic(db.Model):
    __tablename__ = 'cybernetics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    neural_shock_value = db.Column(db.Integer, nullable=False)
    adds_engineering_mods = db.Column(db.Integer, default=0)
    adds_engineering_downtime = db.Column(db.Integer, default=0)
    adds_science_downtime = db.Column(db.Integer, default=0)
    science_type = db.Column(db.Enum(ScienceType, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=True)
    wiki_slug = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Cybernetic {self.name}>'

class CharacterCybernetic(db.Model):
    __tablename__ = 'character_cybernetics'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    cybernetic_id = db.Column(db.Integer, db.ForeignKey('cybernetics.id'), nullable=False)
    
    character = db.relationship('Character', back_populates='cybernetics_link')
    cybernetic = db.relationship('Cybernetic', backref='character_links') 