from models.extensions import db
import math
from models.database.item_blueprint import item_blueprint_mods

item_mods_applied = db.Table(
    'item_mods_applied',
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True),
    db.Column('mod_id', db.Integer, db.ForeignKey('mods.id'), primary_key=True),
    db.Column('count', db.Integer, nullable=False, default=1)
)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blueprint_id = db.Column(db.Integer, db.ForeignKey('item_blueprints.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.Integer, nullable=True)

    blueprint = db.relationship('ItemBlueprint', back_populates='items')
    mods_applied = db.relationship('Mod', secondary=item_mods_applied, backref='items_applied')

    __table_args__ = (
        db.UniqueConstraint('blueprint_id', 'item_id', name='uix_blueprint_itemid'),
    )

    def __repr__(self):
        return f'<Item {self.blueprint_id}-{self.item_id}>'

    @property
    def full_code(self):
        return f"{self.blueprint.full_code}-{self.item_id:03d}"

    @property
    def total_mods(self):
        # Count only applied mods
        rows = db.session.execute(
            item_mods_applied.select().where(item_mods_applied.c.item_id == self.id)
        ).fetchall()
        applied_mods = sum(row.count for row in rows)
        return applied_mods

    def base_cost_calc(self, additional_mods=0):
        if not self.blueprint or not self.blueprint.base_cost:
            return None
        cost = self.blueprint.base_cost * math.exp((self.total_mods + additional_mods) / 2.5)
        return math.ceil(cost)

    def get_maintenance_cost(self, additional_mods=0):
        return math.ceil(self.base_cost_calc(additional_mods) * 0.1)

    def get_modification_cost(self, additional_mods=0):
        return math.ceil(self.base_cost_calc(additional_mods) * 0.5) 