import pytest
from models.database.item import Item
from models.database.item_type import ItemType
from models.database.item_blueprint import ItemBlueprint
from models.database.mods import Mod

def test_item_hierarchy(db):
    """Test the full hierarchy from ItemType -> ItemBlueprint -> Item."""
    # 1. Create an ItemType
    item_type = ItemType(name="Weapon", id_prefix="WP")
    db.session.add(item_type)
    db.session.commit()

    # 2. Create a Mod
    mod = Mod(name="Scope", wiki_slug="scope")
    db.session.add(mod)
    db.session.commit()

    # 3. Create an ItemBlueprint
    blueprint = ItemBlueprint(
        name="Laser Pistol",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100,
        mods_applied=[mod]
    )
    db.session.add(blueprint)
    db.session.commit()
    
    # 4. Create an Item
    item = Item(
        blueprint_id=blueprint.id,
        item_id=1,
        expiry=10
    )
    db.session.add(item)
    db.session.commit()
    
    # 5. Retrieve and assert
    retrieved_item = Item.query.get(item.id)
    assert retrieved_item is not None
    assert retrieved_item.expiry == 10
    
    # Assert blueprint relationship
    retrieved_blueprint = retrieved_item.blueprint
    assert retrieved_blueprint is not None
    assert retrieved_blueprint.name == "Laser Pistol"
    assert retrieved_blueprint.base_cost == 100
    
    # Assert item type relationship
    retrieved_type = retrieved_blueprint.item_type
    assert retrieved_type is not None
    assert retrieved_type.name == "Weapon"
    
    # Assert mods relationship on blueprint
    assert len(retrieved_blueprint.mods_applied) == 1
    assert retrieved_blueprint.mods_applied[0].name == "Scope"
    
    # Assert full codes
    assert retrieved_blueprint.full_code == "WP0001"
    assert retrieved_item.full_code == "WP0001-001" 
