from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType

def get_sample_item():
    item_type = ItemType(id=1, name="Weapon", id_prefix="WE")
    blueprint = ItemBlueprint(id=1, name="Plasma Rifle", item_type=item_type, blueprint_id=1, base_cost=500, purchaseable=True)
    item = Item(id=1, blueprint=blueprint, item_id=1, expiry=None)
    return item 