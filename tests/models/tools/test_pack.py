import pytest

from models.tools.pack import Pack


class TestPack:
    """Test the Pack class functionality."""

    def test_pack_creation(self):
        """Test creating a basic pack."""
        pack = Pack()
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_pack_with_data(self):
        """Test creating a pack with data."""
        pack = Pack(
            items=[1, 2, 3],
            exotics=[1, 2],
            samples=[1, 2],
            medicaments=[1],
            energy_chits=100,
            completion={"character_sheet": True, "character_id_badge": True},
            is_generated=True,
        )

        assert pack.items == [1, 2, 3]
        assert pack.exotics == [1, 2]
        assert pack.samples == [1, 2]
        assert pack.medicaments == [1]
        assert pack.energy_chits == 100
        assert pack.completion == {"character_sheet": True, "character_id_badge": True}
        assert pack.is_generated is True

    def test_pack_to_dict(self):
        """Test converting pack to dictionary."""
        pack = Pack(
            items=[1, 2],
            exotics=[1],
            samples=[1],
            medicaments=[1],
            energy_chits=50,
            completion={"character_sheet": True},
            is_generated=True,
        )

        pack_dict = pack.to_dict()

        assert pack_dict["items"] == [1, 2]
        assert pack_dict["exotics"] == [1]
        assert pack_dict["samples"] == [1]
        assert pack_dict["medicaments"] == [1]
        assert pack_dict["energy_chits"] == 50
        assert pack_dict["completion"] == {"character_sheet": True}
        assert pack_dict["is_generated"] is True

    def test_pack_from_json(self):
        """Test creating pack from JSON string."""
        pack_json = (
            '{"items": [1, 2, 3], "exotics": [1, 2], "samples": [1, 2], '
            '"medicaments": [1], "energy_chits": 75, "completion": {"character_sheet": true}, '
            '"is_generated": true}'
        )

        pack = Pack.from_json(pack_json)

        assert pack.items == [1, 2, 3]
        assert pack.exotics == [1, 2]
        assert pack.samples == [1, 2]
        assert pack.medicaments == [1]
        assert pack.energy_chits == 75
        assert pack.completion == {"character_sheet": True}
        assert pack.is_generated is True

    def test_pack_from_empty_json(self):
        """Test creating pack from empty JSON string."""
        pack = Pack.from_json("")
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_pack_from_none_json(self):
        """Test creating pack from None JSON string."""
        pack = Pack.from_json(None)
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False

    def test_pack_add_item(self):
        """Test adding items to pack."""
        pack = Pack()
        pack.add_item(1)
        pack.add_item(2)
        pack.add_item(1)  # Duplicate should not be added
        assert pack.items == [1, 2]

    def test_pack_remove_item(self):
        """Test removing items from pack."""
        pack = Pack(items=[1, 2, 3])
        assert pack.remove_item(2) is True
        assert pack.items == [1, 3]
        assert pack.remove_item(4) is False  # Item not in pack
        assert pack.items == [1, 3]

    def test_pack_has_item(self):
        """Test checking if pack has item."""
        pack = Pack(items=[1, 2, 3])
        assert pack.has_item(2) is True
        assert pack.has_item(4) is False

    def test_pack_add_exotic(self):
        """Test adding exotics to pack."""
        pack = Pack()
        pack.add_exotic(1)
        pack.add_exotic(2)
        pack.add_exotic(1)  # Duplicate should not be added
        assert pack.exotics == [1, 2]

    def test_pack_remove_exotic(self):
        """Test removing exotics from pack."""
        pack = Pack(exotics=[1, 2, 3])
        assert pack.remove_exotic(2) is True
        assert pack.exotics == [1, 3]
        assert pack.remove_exotic(4) is False  # Exotic not in pack
        assert pack.exotics == [1, 3]

    def test_pack_has_exotic(self):
        """Test checking if pack has exotic."""
        pack = Pack(exotics=[1, 2, 3])
        assert pack.has_exotic(2) is True
        assert pack.has_exotic(4) is False

    def test_pack_add_sample(self):
        """Test adding samples to pack."""
        pack = Pack()
        pack.add_sample(1)
        pack.add_sample(2)
        pack.add_sample(1)  # Duplicate should not be added
        assert pack.samples == [1, 2]

    def test_pack_remove_sample(self):
        """Test removing samples from pack."""
        pack = Pack(samples=[1, 2, 3])
        assert pack.remove_sample(2) is True
        assert pack.samples == [1, 3]
        assert pack.remove_sample(4) is False  # Sample not in pack
        assert pack.samples == [1, 3]

    def test_pack_has_sample(self):
        """Test checking if pack has sample."""
        pack = Pack(samples=[1, 2, 3])
        assert pack.has_sample(2) is True
        assert pack.has_sample(4) is False

    def test_pack_add_medicament(self):
        """Test adding medicaments to pack."""
        pack = Pack()
        pack.add_medicament(1)
        pack.add_medicament(2)
        pack.add_medicament(1)  # Duplicate should not be added
        assert pack.medicaments == [1, 2]

    def test_pack_remove_medicament(self):
        """Test removing medicaments from pack."""
        pack = Pack(medicaments=[1, 2, 3])
        assert pack.remove_medicament(2) is True
        assert pack.medicaments == [1, 3]
        assert pack.remove_medicament(4) is False  # Medicament not in pack
        assert pack.medicaments == [1, 3]

    def test_pack_has_medicament(self):
        """Test checking if pack has medicament."""
        pack = Pack(medicaments=[1, 2, 3])
        assert pack.has_medicament(2) is True
        assert pack.has_medicament(4) is False

    def test_pack_set_completion(self):
        """Test setting completion status."""
        pack = Pack()
        pack.set_completion("character_sheet", True)
        pack.set_completion("character_id_badge", False)
        assert pack.completion["character_sheet"] is True
        assert pack.completion["character_id_badge"] is False

    def test_pack_is_complete(self):
        """Test checking if pack is complete."""
        pack = Pack(
            items=[1],
            samples=[1],
            exotics=[1],
            medicaments=[1],
            energy_chits=50,
            completion={
                "character_sheet": True,
                "character_id_badge": True,
                "item_1": True,
                "sample_1": True,
                "exotic_1": True,
                "medicament_1": True,
                "energy_chits": True,
            },
        )
        assert pack.is_complete() is True

        # Test incomplete pack
        pack.completion["character_sheet"] = False
        assert pack.is_complete() is False

    def test_pack_is_completed_property(self):
        """Test the is_completed property."""
        pack = Pack(
            items=[1],
            samples=[1],
            exotics=[1],
            medicaments=[1],
            energy_chits=50,
            completion={
                "character_sheet": True,
                "character_id_badge": True,
                "item_1": True,
                "sample_1": True,
                "exotic_1": True,
                "medicament_1": True,
                "energy_chits": True,
            },
        )
        assert pack.is_completed is True

        # Test incomplete pack
        pack.completion["character_sheet"] = False
        assert pack.is_completed is False

    def test_pack_to_dict_error_handling(self):
        """Test to_dict error handling."""
        pack = Pack()
        # Simulate an error by making completion have non-string keys
        pack.completion = {1: True}  # Non-string key
        result = pack.to_dict()
        # Should return stringified key
        assert result["items"] == []
        assert result["exotics"] == []
        assert result["samples"] == []
        assert result["medicaments"] == []
        assert result["energy_chits"] == 0
        assert result["completion"] == {"1": True}

    def test_pack_from_json_error_handling(self):
        """Test from_json error handling."""
        # Invalid JSON
        pack = Pack.from_json("invalid json")
        assert pack.items == []
        assert pack.exotics == []
        assert pack.samples == []
        assert pack.medicaments == []
        assert pack.energy_chits == 0
        assert pack.completion == {}
        assert pack.is_generated is False
