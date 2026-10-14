from models.enums import ScienceType
from models.extensions import db


def normalize_label(value):
    """Trim a free-text type or slot. Blank stays blank."""
    return (value or "").strip()


def slot_key(value):
    """Compare slots without caring about case or surrounding spaces."""
    return normalize_label(value).casefold()


def canonical_label(value, existing):
    """Use an existing type or slot's spelling when the text matches one."""
    cleaned = normalize_label(value)
    if not cleaned:
        return ""
    folded = cleaned.casefold()
    for item in existing:
        if item and item.casefold() == folded:
            return item
    return cleaned


def distinct_labels(column):
    """Existing non-blank values for a type or slot field, in display order."""
    rows = (
        db.session.query(column)
        .filter(column.isnot(None), column != "")
        .distinct()
        .order_by(column)
        .all()
    )
    return [row[0] for row in rows]


def slot_conflict_message(implants):
    """Explain when two implants would share a slot. Blank slots do not conflict."""
    seen = {}
    for implant in implants:
        key = slot_key(implant.slot)
        if not key:
            continue
        if key in seen:
            other = seen[key]
            slot_label = normalize_label(implant.slot) or normalize_label(other.slot)
            return (
                f"{implant.name} cannot be installed in the {slot_label} slot. "
                f"{other.name} is already installed there."
            )
        seen[key] = implant
    return None


def implants_by_ids(raw_ids):
    """Load implants for submitted ids, skipping blanks, duplicates, and unknown ids."""
    implants = []
    seen = set()
    for raw in raw_ids:
        if not str(raw).isdigit():
            continue
        implant_id = int(raw)
        if implant_id in seen:
            continue
        seen.add(implant_id)
        implant = db.session.get(Cybernetic, implant_id)
        if implant is not None:
            implants.append(implant)
    return implants


def occupied_slots(character):
    """Map each filled slot on a character to the implant id installed there."""
    occupied = {}
    for link in character.cybernetics_link:
        key = slot_key(link.cybernetic.slot)
        if key:
            occupied[key] = link.cybernetic_id
    return occupied


def adding_conflict_message(character, raw_ids):
    """Conflict from installing submitted implants on top of those already present."""
    existing = [link.cybernetic for link in character.cybernetics_link]
    existing_ids = {implant.id for implant in existing}
    incoming = [implant for implant in implants_by_ids(raw_ids) if implant.id not in existing_ids]
    return slot_conflict_message(existing + incoming)


def slot_change_conflict_message(implant, new_slot):
    """Reject a slot edit that would put two implants in one slot for someone."""
    new_key = slot_key(new_slot)
    if not new_key or new_key == slot_key(implant.slot):
        return None
    for link in implant.character_links:
        for other_link in link.character.cybernetics_link:
            if other_link.cybernetic_id == implant.id:
                continue
            if slot_key(other_link.cybernetic.slot) != new_key:
                continue
            return (
                f"Cannot use the {normalize_label(new_slot)} slot. "
                f"{link.character.name} already has {other_link.cybernetic.name} "
                "installed there."
            )
    return None


class Cybernetic(db.Model):
    __tablename__ = "cybernetics"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    neural_shock_value = db.Column(db.Integer, nullable=False)
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
    )
    wiki_slug = db.Column(db.String(100), nullable=False)
    implant_type = db.Column(db.String(100), nullable=True)
    slot = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Cybernetic {self.name}>"

    @property
    def choice_label(self):
        """Name plus type and slot, for pickers that need to show where it installs."""
        details = [part for part in (self.implant_type, self.slot) if part]
        if details:
            return f"{self.name} ({', '.join(details)})"
        return self.name


class CharacterCybernetic(db.Model):
    __tablename__ = "character_cybernetics"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    cybernetic_id = db.Column(db.Integer, db.ForeignKey("cybernetics.id"), nullable=False)

    character = db.relationship("Character", back_populates="cybernetics_link")
    cybernetic = db.relationship("Cybernetic", backref="character_links")
