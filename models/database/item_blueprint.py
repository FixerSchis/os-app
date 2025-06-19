from models.extensions import db
from models.database.item_type import ItemType
from models.database.mods import Mod
from sqlalchemy.orm import validates
import re
import math

item_blueprint_mods = db.Table('item_blueprint_mods',
    db.Column('item_blueprint_id', db.Integer, db.ForeignKey('item_blueprints.id'), primary_key=True),
    db.Column('mod_id', db.Integer, db.ForeignKey('mods.id'), primary_key=True),
    db.Column('count', db.Integer, nullable=False, default=1)
)

class ItemBlueprint(db.Model):
    __tablename__ = 'item_blueprints'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_types.id'), nullable=False)
    blueprint_id = db.Column(db.Integer, nullable=False)
    base_cost = db.Column(db.Integer, nullable=False)
    purchaseable = db.Column(db.Boolean, nullable=False, default=True)

    item_type = db.relationship('ItemType', backref=db.backref('blueprints', lazy=True))
    mods_applied = db.relationship('Mod', secondary=item_blueprint_mods, backref=db.backref('item_blueprints', lazy='dynamic'))
    items = db.relationship('Item', back_populates='blueprint')

    __table_args__ = (
        db.UniqueConstraint('item_type_id', 'blueprint_id', name='uq_itemtype_blueprintid'),
    )

    @property
    def full_code(self):
        return f"{self.item_type.id_prefix}{self.blueprint_id:04d}"

    @validates('blueprint_id')
    def validate_blueprint_id(self, key, blueprint_id):
        # Ensure blueprint_id is an integer and unique for this item type
        if not isinstance(blueprint_id, int):
            raise ValueError('Blueprint ID must be an integer')
        if self.item_type_id and self.item_type:
            # Get the id_prefix of the current item type
            current_prefix = self.item_type.id_prefix
            # Find all item types with the same prefix
            same_prefix_types = ItemType.query.filter(ItemType.id_prefix == current_prefix).all()
            same_prefix_type_ids = [t.id for t in same_prefix_types]
            # Check uniqueness across all blueprints with the same prefix
            existing = ItemBlueprint.query.filter(
                ItemBlueprint.item_type_id.in_(same_prefix_type_ids),
                ItemBlueprint.blueprint_id == blueprint_id,
                ItemBlueprint.id != self.id
            ).first()
            if existing:
                raise ValueError('Blueprint ID must be unique for this item type prefix')
        return blueprint_id

    def __repr__(self):
        return f'<ItemBlueprint {self.name} ({self.full_code})>'

    def base_mods(self):
        # Return the number of mods applied to this blueprint
        return len(self.mods_applied) if self.mods_applied else 0

    def base_cost_calc(self, applied_mods=0):
        if self.base_cost is None:
            return None
        cost = self.base_cost * math.exp((applied_mods) / 2.5)
        return math.ceil(cost)

    def get_maintenance_cost(self, applied_mods=0):
        return math.ceil(self.base_cost_calc(applied_mods) * 0.1)

    def get_modification_cost(self, applied_mods=0):
        return math.ceil(self.base_cost_calc(applied_mods) * 0.5) 