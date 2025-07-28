"""Test starting item ability functionality."""

import pytest

from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.species import Ability, Species
from models.enums import AbilityType, BodyHitsType, CharacterStatus
from models.tools.character import Character


class TestSpeciesStartingItem:
    """Test the starting item ability functionality."""

    def test_ability_with_starting_item(self, db):
        """Test creating an ability with starting item blueprint."""
        # Create item type and blueprint
        item_type = ItemType(id=1, name="Test Weapon", id_prefix="TW")
        db.session.add(item_type)
        db.session.flush()

        blueprint = ItemBlueprint(
            id=1,
            name="Test Weapon Blueprint",
            item_type_id=item_type.id,
            blueprint_id=1,
            base_cost=100,
        )
        db.session.add(blueprint)
        db.session.flush()

        # Create species with starting item ability
        species = Species(
            name="Test Species",
            wiki_page="test-species",
            permitted_factions_list=[1],
            body_hits_type=BodyHitsType.GLOBAL,
            body_hits=3,
            death_count=3,
        )
        db.session.add(species)
        db.session.flush()

        ability = Ability(
            name="Starting Weapon",
            description="This species starts with a weapon",
            type=AbilityType.STARTING_ITEM,
            species=species,
            starting_item_blueprint_id=blueprint.id,
        )
        db.session.add(ability)
        db.session.commit()

        # Verify the ability was created correctly
        assert ability.starting_item_blueprint_id == blueprint.id
        # The type field returns the enum object, so compare with the enum
        assert ability.type == AbilityType.STARTING_ITEM

    def test_character_activation_with_starting_item(self, db, new_user):
        """Test that character activation creates starting items."""
        # Create item type and blueprint
        item_type = ItemType(id=1, name="Test Weapon", id_prefix="TW")
        db.session.add(item_type)
        db.session.flush()

        blueprint = ItemBlueprint(
            id=1,
            name="Test Weapon Blueprint",
            item_type_id=item_type.id,
            blueprint_id=1,
            base_cost=100,
        )
        db.session.add(blueprint)
        db.session.flush()

        # Create species with starting item ability
        species = Species(
            name="Test Species",
            wiki_page="test-species",
            permitted_factions_list=[1],
            body_hits_type=BodyHitsType.GLOBAL,
            body_hits=3,
            death_count=3,
        )
        db.session.add(species)
        db.session.flush()

        ability = Ability(
            name="Starting Weapon",
            description="This species starts with a weapon",
            type=AbilityType.STARTING_ITEM,
            species=species,
            starting_item_blueprint_id=blueprint.id,
        )
        db.session.add(ability)
        db.session.commit()

        # Create character
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status=CharacterStatus.DEVELOPING.value,
        )
        db.session.add(character)
        db.session.commit()

        # Activate character using the same logic as the route
        character.status = CharacterStatus.ACTIVE.value

        # Handle starting items from species abilities (same logic as the route)
        if character.species:
            for ability in character.species.abilities:
                if ability.type == AbilityType.STARTING_ITEM and ability.starting_item_blueprint_id:
                    # Create item from blueprint
                    blueprint = ItemBlueprint.query.get(ability.starting_item_blueprint_id)
                    if blueprint:
                        # Get the next item ID for this blueprint
                        max_item = (
                            Item.query.filter_by(blueprint_id=blueprint.id)
                            .order_by(Item.item_id.desc())
                            .first()
                        )
                        next_item_id = (max_item.item_id + 1) if max_item else 1

                        # Create the item
                        item = Item(
                            blueprint_id=blueprint.id,
                            item_id=next_item_id,
                            expiry=None,  # Starting items don't expire
                        )
                        db.session.add(item)
                        db.session.flush()

                        # Create a new pack with the item
                        new_pack = character.pack
                        new_pack.add_item(item.id)

                        # Save the modified pack back to the character
                        character.pack = new_pack

        db.session.commit()

        # Refresh character to get updated pack
        db.session.refresh(character)

        # Verify the item was created and added to character's pack
        assert len(character.pack.items) == 1
        item_id = character.pack.items[0]
        item = Item.query.get(item_id)
        assert item is not None
        assert item.blueprint_id == blueprint.id
        assert item.item_id == 1  # First item for this blueprint
