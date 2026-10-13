import json

from ..enums import AbilityType, BodyHitsType
from ..extensions import db
from .rule_tag import ability_rule_tags


class Ability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey("species.id"), nullable=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(
        db.Enum(
            AbilityType,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
    )
    starting_skills = db.Column(db.String, nullable=True)
    starting_skill_choices = db.Column(db.String, nullable=True)
    skill_pairs = db.Column(db.String, nullable=True)
    rank_caps = db.Column(db.String, nullable=True)
    banned_skills = db.Column(db.String, nullable=True)
    skill_discounts = db.Column(db.String, nullable=True)
    additional_group_income = db.Column(db.Integer, nullable=True)
    condition_progress_rate = db.Column(db.Float, nullable=True)
    character_sheet_values = db.Column(db.String, nullable=True)
    starting_item_blueprint_id = db.Column(
        db.Integer, db.ForeignKey("item_blueprints.id"), nullable=True
    )
    starting_reputation_faction_id = db.Column(
        db.Integer, db.ForeignKey("faction.id"), nullable=True
    )
    starting_reputation_value = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "(species_id IS NOT NULL AND character_id IS NULL) OR "
            "(species_id IS NULL AND character_id IS NOT NULL)",
            name="ck_ability_one_owner",
        ),
    )

    # Relationships
    starting_reputation_faction = db.relationship(
        "Faction", foreign_keys=[starting_reputation_faction_id]
    )
    tags = db.relationship("RuleTag", secondary=ability_rule_tags, order_by="RuleTag.name")

    @property
    def character_sheet_values_list(self):
        return json.loads(self.character_sheet_values) if self.character_sheet_values else []

    @character_sheet_values_list.setter
    def character_sheet_values_list(self, values):
        self.character_sheet_values = json.dumps(values) if values else None

    @property
    def starting_skills_list(self):
        return [str(s) for s in json.loads(self.starting_skills)] if self.starting_skills else []

    @starting_skills_list.setter
    def starting_skills_list(self, skills):
        self.starting_skills = json.dumps(skills) if skills else None

    @property
    def starting_skill_choices_list(self):
        if not self.starting_skill_choices:
            return []
        return json.loads(self.starting_skill_choices)

    @starting_skill_choices_list.setter
    def starting_skill_choices_list(self, choices):
        self.starting_skill_choices = json.dumps(choices) if choices else None

    @property
    def skill_pairs_list(self):
        if not self.skill_pairs:
            return []
        return json.loads(self.skill_pairs)

    @skill_pairs_list.setter
    def skill_pairs_list(self, pairs):
        self.skill_pairs = json.dumps(pairs) if pairs else None

    @property
    def rank_caps_list(self):
        if not self.rank_caps:
            return []
        return json.loads(self.rank_caps)

    @rank_caps_list.setter
    def rank_caps_list(self, caps):
        self.rank_caps = json.dumps(caps) if caps else None

    @property
    def banned_skills_list(self):
        if not self.banned_skills:
            return []
        return [str(skill_id) for skill_id in json.loads(self.banned_skills)]

    @banned_skills_list.setter
    def banned_skills_list(self, skill_ids):
        self.banned_skills = (
            json.dumps([str(skill_id) for skill_id in skill_ids]) if skill_ids else None
        )

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
    permitted_factions = db.Column(
        db.String, nullable=False
    )  # Stored as JSON string of faction IDs
    body_hits_type = db.Column(
        db.Enum(
            BodyHitsType,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
    )
    body_hits = db.Column(db.Integer, nullable=False, default=0)
    extra_hits_per_toughness = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    death_count = db.Column(db.Integer, nullable=False, default=0)
    keywords = db.Column(db.String, nullable=True)  # Stored as JSON string of keywords

    # Relationships
    abilities = db.relationship(
        "Ability",
        backref="species",
        cascade="all, delete-orphan",
        foreign_keys="Ability.species_id",
    )
    characters = db.relationship("Character", back_populates="species")

    def __repr__(self):
        return f"<Species {self.name}>"

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
