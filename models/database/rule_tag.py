from models.extensions import db

condition_rule_tags = db.Table(
    "condition_rule_tags",
    db.Column(
        "condition_id",
        db.Integer,
        db.ForeignKey("conditions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "rule_tag_id",
        db.Integer,
        db.ForeignKey("rule_tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

ability_rule_tags = db.Table(
    "ability_rule_tags",
    db.Column(
        "ability_id",
        db.Integer,
        db.ForeignKey("ability.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "rule_tag_id",
        db.Integer,
        db.ForeignKey("rule_tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

skill_rule_tags = db.Table(
    "skill_rule_tags",
    db.Column(
        "skill_id",
        db.Integer,
        db.ForeignKey("skill.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "rule_tag_id",
        db.Integer,
        db.ForeignKey("rule_tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class RuleTag(db.Model):
    """Shared tag for conditions, abilities, and skills that change condition timing."""

    __tablename__ = "rule_tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    def __repr__(self):
        return f"<RuleTag {self.name}>"

    @staticmethod
    def normalize(raw):
        return " ".join(str(raw or "").split())

    @classmethod
    def get_or_create(cls, raw):
        """Return the tag for an id or name, creating it when the name is new."""
        text = cls.normalize(raw)
        if not text:
            return None
        if text.isdigit():
            existing = db.session.get(cls, int(text))
            if existing is not None:
                return existing
        found = cls.query.filter(cls.name.ilike(text)).first()
        if found is not None:
            return found
        tag = cls(name=text[:64])
        db.session.add(tag)
        db.session.flush()
        return tag

    @classmethod
    def resolve_list(cls, values):
        tags = []
        seen = set()
        for value in values or []:
            tag = cls.get_or_create(value)
            if tag is None or tag.id in seen:
                continue
            seen.add(tag.id)
            tags.append(tag)
        return tags
