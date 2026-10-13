import json

from models.extensions import db
from utils.description_format import format_rank_description

mod_type_restrictions = db.Table(
    "mod_type_restrictions",
    db.Column("mod_id", db.Integer, db.ForeignKey("mods.id"), primary_key=True),
    db.Column("item_type_id", db.Integer, db.ForeignKey("item_types.id"), primary_key=True),
)


def _load_id_list(raw):
    if not raw:
        return []
    return [int(item) for item in json.loads(raw)]


def _dump_id_list(skill_ids):
    cleaned = sorted({int(item) for item in skill_ids or []})
    return json.dumps(cleaned) if cleaned else None


def _character_skill_ids(character):
    return {row.skill_id for row in character.skills}


class Mod(db.Model):
    __tablename__ = "mods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wiki_slug = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # JSON lists of skill IDs. A character needs one of required_skills to learn the mod.
    # An engineer with one of granted_by_skills knows the mod without spending a mod slot.
    required_skills = db.Column(db.String, nullable=True)
    granted_by_skills = db.Column(db.String, nullable=True)
    item_types = db.relationship(
        "ItemType",
        secondary=mod_type_restrictions,
        backref=db.backref("mods", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Mod {self.name}>"

    @property
    def required_skills_list(self):
        return _load_id_list(self.required_skills)

    @required_skills_list.setter
    def required_skills_list(self, skill_ids):
        self.required_skills = _dump_id_list(skill_ids)

    @property
    def granted_by_skills_list(self):
        return _load_id_list(self.granted_by_skills)

    @granted_by_skills_list.setter
    def granted_by_skills_list(self, skill_ids):
        self.granted_by_skills = _dump_id_list(skill_ids)

    def get_required_skills(self):
        from models.database.skills import Skill

        if not self.required_skills_list:
            return []
        return Skill.query.filter(Skill.id.in_(self.required_skills_list)).all()

    def get_granted_by_skills(self):
        from models.database.skills import Skill

        if not self.granted_by_skills_list:
            return []
        return Skill.query.filter(Skill.id.in_(self.granted_by_skills_list)).all()

    def character_meets_requirements(self, character):
        """True when the character has a skill this mod needs before it can be learned."""
        required = self.required_skills_list
        if not required:
            return True
        owned = _character_skill_ids(character)
        return any(skill_id in owned for skill_id in required)

    def is_granted_to(self, character):
        """True when the character knows this mod from a skill rather than a mod slot."""
        granted_by = self.granted_by_skills_list
        if not granted_by:
            return False
        if character.get_available_engineering_mod_slots() <= 0:
            return False
        owned = _character_skill_ids(character)
        return any(skill_id in owned for skill_id in granted_by)

    def format_applied(self, count):
        """Format the description when the mod is applied to an item."""
        if not self.description:
            return f"{self.name} ({count})"
        return format_rank_description(self.description, count)

    def format_unapplied(self):
        """Format the description when the mod is not applied to an item."""
        if not self.description:
            return f"{self.name}"
        return format_rank_description(self.description, 1, per_rank=True)
