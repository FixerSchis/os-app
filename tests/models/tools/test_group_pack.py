import pytest

from models.database.group_type import GroupType
from models.tools.group import Group
from models.tools.pack import Pack


class TestGroupPack:
    """Test the group pack property functionality."""

    def test_group_pack_default(self, db):
        """Test group pack property with default (empty) pack."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        # Test default pack
        pack = group.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_group_pack_set_and_get(self, db):
        """Test setting and getting group pack."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        # Create a pack with some data
        test_pack = Pack(
            items=[1, 2, 3],
            exotics=[1, 2],
            samples=[1],
            medicaments=[1, 2, 3],
            energy_chits=100,
            completion={"item_1": True, "energy_chits": True},
            is_generated=True,
        )

        # Set the pack
        group.pack = test_pack
        db.session.commit()

        # Get the pack back
        retrieved_pack = group.pack
        assert retrieved_pack.items == [1, 2, 3]
        assert retrieved_pack.exotics == [1, 2]
        assert retrieved_pack.samples == [1]
        assert retrieved_pack.medicaments == [1, 2, 3]
        assert retrieved_pack.energy_chits == 100
        assert retrieved_pack.completion == {"item_1": True, "energy_chits": True}
        assert retrieved_pack.is_generated is True

    def test_group_pack_json_serialization(self, db):
        """Test that pack is properly serialized to JSON in database."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        test_pack = Pack(
            items=[1, 2],
            exotics=[1],
            samples=[1, 2, 3],
            medicaments=[1],
            energy_chits=50,
            completion={"item_1": True},
            is_generated=False,
        )

        group.pack = test_pack
        db.session.commit()

        # Check that the JSON string is stored correctly
        assert group.group_pack is not None
        assert isinstance(group.group_pack, str)

        # Verify pack_complete is set correctly
        assert group.pack_complete == test_pack.is_complete()

    def test_group_pack_from_json(self, db):
        """Test creating pack from JSON string."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        # Set JSON string directly
        json_data = (
            '{"items": [1, 2], "exotics": [1], "samples": [], "medicaments": [1], '
            '"energy_chits": 25, "completion": {"item_1": true}, "is_generated": true}'
        )
        group.group_pack = json_data
        db.session.commit()

        # Get pack through property
        pack = group.pack
        assert pack.items == [1, 2]
        assert pack.exotics == [1]
        assert pack.samples == []
        assert pack.medicaments == [1]
        assert pack.energy_chits == 25
        assert pack.completion == {"item_1": True}
        assert pack.is_generated is True

    def test_group_pack_none_json(self, db):
        """Test handling of None JSON string."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        group.group_pack = None
        db.session.commit()

        pack = group.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_group_pack_invalid_json(self, db):
        """Test handling of invalid JSON string."""
        # Create a group type first
        group_type = GroupType(
            name="Test Group Type",
            description="A test group type",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        # Create a group
        group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
        db.session.add(group)
        db.session.commit()

        group.group_pack = "invalid json"
        db.session.commit()

        # Should create empty pack on invalid JSON
        pack = group.pack
        assert isinstance(pack, Pack)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False
