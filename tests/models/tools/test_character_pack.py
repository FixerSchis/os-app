import pytest

from models.tools.character import Character
from models.tools.pack import Pack, PackDowntimeResult, PackExotic, PackMessage


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
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}

    def test_character_pack_with_data(self, db, new_user, species):
        """Test character pack property with existing data."""
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status="active",
            character_pack={
                "items": [1, 2, 3],
                "exotic_substances": [{"id": 1, "amount": 5}],
                "samples": [1, 2],
                "chits": 100,
                "messages": [{"type": "sms", "content": "Test message"}],
                "downtime_results": {"pack1": [{"message": "Test result"}]},
                "metadata": {"key": "value"},
            },
        )
        db.session.add(character)
        db.session.commit()

        # Test pack retrieval
        pack = character.pack
        assert isinstance(pack, Pack)
        assert pack.items == [1, 2, 3]
        assert len(pack.exotic_substances) == 1
        assert pack.exotic_substances[0].id == 1
        assert pack.exotic_substances[0].amount == 5
        assert pack.samples == [1, 2]
        assert pack.chits == 100
        assert len(pack.messages) == 1
        assert pack.messages[0].type == "sms"
        assert pack.messages[0].content == "Test message"
        assert "pack1" in pack.downtime_results
        assert pack.metadata["key"] == "value"

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
            exotic_substances=[PackExotic(id=1, amount=3)],
            samples=[1],
            chits=50,
            messages=[PackMessage(type="email", content="Test email")],
            downtime_results={"pack1": [PackDowntimeResult(message="Success")]},
            metadata={"test": "data"},
        )

        # Set the pack
        character.pack = pack
        db.session.commit()

        # Verify the pack was stored correctly
        db.session.refresh(character)
        assert character.character_pack is not None
        assert character.character_pack["items"] == [1, 2]
        assert character.character_pack["exotic_substances"] == [{"id": 1, "amount": 3}]
        assert character.character_pack["samples"] == [1]
        assert character.character_pack["chits"] == 50
        assert character.character_pack["messages"] == [{"type": "email", "content": "Test email"}]
        assert character.character_pack["downtime_results"] == {"pack1": [{"message": "Success"}]}
        assert character.character_pack["metadata"] == {"test": "data"}

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
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}

    def test_character_pack_empty_dict(self, db, new_user, species):
        """Test character pack property with empty dictionary."""
        character = Character(
            name="Test Character",
            user_id=new_user.id,
            species_id=species.id,
            status="active",
            character_pack={},
        )
        db.session.add(character)
        db.session.commit()

        # Test pack retrieval with empty dict
        pack = character.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}

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
        pack.chits = 25
        pack.messages.append(PackMessage(type="sms", content="New message"))

        # Set the modified pack
        character.pack = pack
        db.session.commit()

        # Verify the modifications were saved
        db.session.refresh(character)
        new_pack = character.pack
        assert new_pack.items == [1]
        assert new_pack.chits == 25
        assert len(new_pack.messages) == 1
        assert new_pack.messages[0].type == "sms"
        assert new_pack.messages[0].content == "New message"
