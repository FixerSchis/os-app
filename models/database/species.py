from ..extensions import db
from ..enums import BodyHitsType, AbilityType
import json

class Ability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(AbilityType, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=False)
    # For starting skills: list of skill IDs (JSON)
    starting_skills = db.Column(db.String, nullable=True)
    # For skill discounts: map of skill_id to discount (JSON)
    skill_discounts = db.Column(db.String, nullable=True)

    @property
    def starting_skills_list(self):
        return [str(s) for s in json.loads(self.starting_skills)] if self.starting_skills else []

    @starting_skills_list.setter
    def starting_skills_list(self, skills):
        self.starting_skills = json.dumps(skills) if skills else None

    @property
    def skill_discounts_dict(self):
        return json.loads(self.skill_discounts) if self.skill_discounts else {}

    @skill_discounts_dict.setter
    def skill_discounts_dict(self, discounts):
        self.skill_discounts = json.dumps(discounts) if discounts else None

class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wiki_page = db.Column(db.String(255), nullable=False)
    permitted_factions = db.Column(db.String, nullable=False)  # Stored as JSON string of faction IDs
    body_hits_type = db.Column(
        db.Enum(BodyHitsType, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False
    )
    body_hits = db.Column(db.Integer, nullable=False, default=0)
    death_count = db.Column(db.Integer, nullable=False, default=0)
    keywords = db.Column(db.String, nullable=True)  # Stored as JSON string of keywords

    # Relationships
    abilities = db.relationship('Ability', backref='species', cascade='all, delete-orphan')
    characters = db.relationship('Character', back_populates='species')

    def __repr__(self):
        return f'<Species {self.name}>'

    @property
    def body_hits_type_enum(self):
        return BodyHitsType(self.body_hits_type)

    @body_hits_type_enum.setter
    def body_hits_type_enum(self, hit_type):
        if isinstance(hit_type, BodyHitsType):
            self.body_hits_type = hit_type.value
        else:
            self.body_hits_type = hit_type

    @property
    def permitted_factions_list(self):
        return [int(f) for f in json.loads(self.permitted_factions)]

    @permitted_factions_list.setter
    def permitted_factions_list(self, factions):
        self.permitted_factions = json.dumps(factions)

    @property
    def keywords_list(self):
        return json.loads(self.keywords) if self.keywords else []

    @keywords_list.setter
    def keywords_list(self, keywords):
        self.keywords = json.dumps(keywords) if keywords else None 