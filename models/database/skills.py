import json
from datetime import datetime, timezone

from models.database.faction import Faction
from models.database.species import Species
from models.tools.character import CharacterTag

from ..enums import ScienceType
from ..extensions import db


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    skill_type = db.Column(db.String(50))
    adds_engineering_mods = db.Column(db.Integer, default=0)
    adds_engineering_downtime = db.Column(db.Integer, default=0)
    adds_science_downtime = db.Column(db.Integer, default=0)
    science_type = db.Column(
        db.Enum(
            ScienceType,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=True,
    )  # Only used if adds_science_downtime > 0
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    base_cost = db.Column(db.Integer, nullable=False)
    can_purchase_multiple = db.Column(db.Boolean, nullable=False, default=False)
    cost_increases = db.Column(db.Boolean, nullable=False, default=False)
    character_sheet_values = db.Column(db.String, nullable=True)  # Stored as JSON string

    # Foreign keys for requirements
    required_skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=True)
    required_factions = db.Column(
        db.String, nullable=True
    )  # Stored as JSON string of faction values
    required_species = db.Column(db.String, nullable=True)  # Stored as JSON string of species IDs
    required_tags = db.Column(db.String, nullable=True)  # Stored as JSON string of tag IDs

    # Relationships
    required_skill = db.relationship("Skill", remote_side=[id], backref="prerequisites")

    def __repr__(self):
        return f"<Skill {self.name}>"

    @property
    def character_sheet_values_list(self):
        return json.loads(self.character_sheet_values) if self.character_sheet_values else []

    @character_sheet_values_list.setter
    def character_sheet_values_list(self, values):
        self.character_sheet_values = json.dumps(values) if values else None

    @property
    def required_factions_list(self):
        return json.loads(self.required_factions) if self.required_factions else []

    @required_factions_list.setter
    def required_factions_list(self, factions):
        self.required_factions = json.dumps(factions) if factions else None

    @property
    def required_species_list(self):
        return json.loads(self.required_species) if self.required_species else []

    @required_species_list.setter
    def required_species_list(self, species_ids):
        self.required_species = json.dumps(species_ids) if species_ids else None

    @property
    def required_tags_list(self):
        return json.loads(self.required_tags) if self.required_tags else []

    @required_tags_list.setter
    def required_tags_list(self, tag_ids):
        self.required_tags = json.dumps(tag_ids) if tag_ids else None

    @classmethod
    def get_all_skill_types(cls):
        """Get a list of all unique skill types in the database."""
        return db.session.query(cls.skill_type).distinct().order_by(cls.skill_type).all()

    @classmethod
    def get_engineering_skills(cls):
        """Get all engineering skills."""
        return cls.query.filter_by(skill_type="ENGINEERING").all()

    @classmethod
    def get_science_skills(cls, science_type=None):
        """Get all science skills, optionally filtered by type."""
        query = cls.query.filter_by(skill_type="SCIENCE")
        if science_type:
            query = query.filter_by(science_type=science_type)
        return query.all()

    def get_required_factions(self):
        if not self.required_factions_list:
            return []
        return Faction.query.filter(Faction.id.in_(self.required_factions_list)).all()

    def get_required_species(self):
        if not self.required_species_list:
            return []
        return Species.query.filter(Species.id.in_(self.required_species_list)).all()

    def get_required_tags(self):
        if not self.required_tags_list:
            return []
        return CharacterTag.query.filter(CharacterTag.id.in_(self.required_tags_list)).all()

    def character_meets_requirements(self, character):
        """Check if a character meets all requirements to learn this skill."""
        # Check faction requirements
        if self.required_factions_list and character.faction_id not in self.required_factions_list:
            return False

        # Check species requirements
        if self.required_species_list and character.species_id not in self.required_species_list:
            return False

        # Check tag requirements
        if self.required_tags_list:
            character_tag_ids = {tag.id for tag in character.tags}
            if not any(tag_id in character_tag_ids for tag_id in self.required_tags_list):
                return False

        # Check skill prerequisites
        if self.required_skill_id:
            # Check if character has the required skill
            has_prerequisite = any(
                skill.skill_id == self.required_skill_id for skill in character.character_skills
            )
            if not has_prerequisite:
                return False

        return True

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type,
            "adds_engineering_mods": self.adds_engineering_mods,
            "adds_engineering_downtime": self.adds_engineering_downtime,
            "adds_science_downtime": self.adds_science_downtime,
            "science_type": self.science_type,
            "character_sheet_values": self.character_sheet_values_list,
        }

    @staticmethod
    def get_science_types():
        return [
            "biology",
            "chemistry",
            "physics",
            "psychology",
            "sociology",
            "xenobiology",
            "xenotechnology",
        ]
