import pytest

from models.tools.character import Character
from models.tools.pack import Pack


class TestCharacterPack:
    """Test the character pack property functionality."""

    def test_character_pack_default(self, db, new_user, species):
        """Test character pack property with default (empty) pack."""
        character = Character(
            name="Test Character", user_id=new_user.id, species_id=species.id, status="active"
        )
        db.session.add(character)
        db.session.commit()

        # Test default pack
        pack = character.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_character_pack_with_data(self, db, new_user, species):
        """Test character pack property with existing data."""
        # Create a pack first
        pack = Pack(
            items=[1, 2, 3],
            exotics=[1, 2],
            samples=[1, 2],
            medicaments=[1],
            energy_chits=100,
            completion={"character_sheet": True, "character_id_badge": True},
            is_generated=True,
        )

        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status="active",
        )
        character.pack = pack  # This will convert to JSON
        db.session.add(character)
        db.session.commit()

        # Test pack retrieval
        retrieved_pack = character.pack
        assert isinstance(retrieved_pack, Pack)
        assert retrieved_pack.items == [1, 2, 3]
        assert retrieved_pack.exotics == [1, 2]
        assert retrieved_pack.samples == [1, 2]
        assert retrieved_pack.medicaments == [1]
        assert retrieved_pack.energy_chits == 100
        assert retrieved_pack.completion == {"character_sheet": True, "character_id_badge": True}
        assert retrieved_pack.is_generated is True

    def test_character_pack_setter(self, db, new_user, species):
        """Test setting character pack property."""
        character = Character(
            name="Test Character", user_id=new_user.id, species_id=species.id, status="active"
        )
        db.session.add(character)
        db.session.commit()

        # Create a pack
        pack = Pack(
            items=[1, 2],
            exotics=[1],
            samples=[1],
            medicaments=[1],
            energy_chits=50,
            completion={"character_sheet": True, "character_id_badge": True},
            is_generated=True,
        )

        # Set the pack
        character.pack = pack
        db.session.commit()

        # Verify the pack was stored correctly
        db.session.refresh(character)
        assert character.character_pack is not None
        # character_pack should be JSON data (dict)
        pack_data = character.character_pack
        assert pack_data["items"] == [1, 2]
        assert pack_data["exotics"] == [1]
        assert pack_data["samples"] == [1]
        assert pack_data["medicaments"] == [1]
        assert pack_data["energy_chits"] == 50
        assert pack_data["completion"] == {"character_sheet": True, "character_id_badge": True}
        assert pack_data["is_generated"] is True

    def test_character_pack_none(self, db, new_user, species):
        """Test character pack property with None character_pack."""
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status="active",
            character_pack=None,
        )
        db.session.add(character)
        db.session.commit()

        # Test pack retrieval with None
        pack = character.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_character_pack_empty_dict(self, db, new_user, species):
        """Test character pack property with empty dictionary."""
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status="active",
        )
        # Set an empty pack
        character.pack = Pack()
        db.session.add(character)
        db.session.commit()

        # Test pack retrieval with empty dict
        pack = character.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_character_pack_modification(self, db, new_user, species):
        """Test modifying character pack through the property."""
        character = Character(
            name="Test Character", user_id=new_user.id, species_id=species.id, status="active"
        )
        db.session.add(character)
        db.session.commit()

        # Get the pack and modify it
        pack = character.pack
        pack.items.append(1)
        pack.energy_chits = 25
        pack.completion["character_sheet"] = True

        # Set the modified pack
        character.pack = pack
        db.session.commit()

        # Verify the modifications were saved
        db.session.refresh(character)
        new_pack = character.pack
        assert new_pack.items == [1]
        assert new_pack.energy_chits == 25
        assert new_pack.completion["character_sheet"] is True
