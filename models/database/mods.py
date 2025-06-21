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
    item_types = db.relationship(
        "ItemType",
        secondary=mod_type_restrictions,
        backref=db.backref("mods", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Mod {self.name}>"
