import operator
import re

from models.extensions import db

mod_type_restrictions = db.Table(
    "mod_type_restrictions",
    db.Column("mod_id", db.Integer, db.ForeignKey("mods.id"), primary_key=True),
    db.Column("item_type_id", db.Integer, db.ForeignKey("item_types.id"), primary_key=True),
)


class Mod(db.Model):
    __tablename__ = "mods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wiki_slug = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    item_types = db.relationship(
        "ItemType",
        secondary=mod_type_restrictions,
        backref=db.backref("mods", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Mod {self.name}>"

    def format_applied(self, count):
        """Format the description when the mod is applied to an item."""
        if not self.description:
            return f"{self.name} ({count})"

        # Replace {num} with the actual count
        formatted = self.description.replace("{num}", str(count))

        # Handle mathematical operations like {num * 30}
        pattern = r"\{num\s*([*+\-/\s]\s*\d+)\}"

        def replace_math(match):
            try:
                # Safe mathematical evaluation
                operation = match.group(1).strip()
                if "*" in operation:
                    parts = operation.split("*")
                    if len(parts) == 2:
                        result = count * int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "+" in operation:
                    parts = operation.split("+")
                    if len(parts) == 2:
                        result = count + int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "-" in operation:
                    parts = operation.split("-")
                    if len(parts) == 2:
                        result = count - int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "/" in operation:
                    parts = operation.split("/")
                    if len(parts) == 2:
                        result = count // int(parts[1].strip())
                    else:
                        return match.group(0)
                else:
                    return match.group(0)
                return str(result)
            except (ValueError, SyntaxError):
                return match.group(0)

        formatted = re.sub(pattern, replace_math, formatted)
        return formatted

    def format_unapplied(self):
        """Format the description when the mod is not applied to an item."""
        if not self.description:
            return f"{self.name}"

        # Replace {num} with "1" for unapplied display
        formatted = self.description.replace("{num}", "1")

        # Handle mathematical operations like {num * 30}
        pattern = r"\{num\s*([*+\-/\s]\s*\d+)\}"

        def replace_math(match):
            try:
                # Safe mathematical evaluation
                operation = match.group(1).strip()
                if "*" in operation:
                    parts = operation.split("*")
                    if len(parts) == 2:
                        result = 1 * int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "+" in operation:
                    parts = operation.split("+")
                    if len(parts) == 2:
                        result = 1 + int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "-" in operation:
                    parts = operation.split("-")
                    if len(parts) == 2:
                        result = 1 - int(parts[1].strip())
                    else:
                        return match.group(0)
                elif "/" in operation:
                    parts = operation.split("/")
                    if len(parts) == 2:
                        result = 1 // int(parts[1].strip())
                    else:
                        return match.group(0)
                else:
                    return match.group(0)
                return str(result)
            except (ValueError, SyntaxError):
                return match.group(0)

        formatted = re.sub(pattern, replace_math, formatted)
        return formatted
