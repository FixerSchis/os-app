import pytest

from models.tools.pack import Pack, PackDowntimeResult, PackExotic, PackMessage


class TestPack:
    """Test the Pack class functionality."""

    def test_pack_creation(self):
        """Test creating a basic pack."""
        pack = Pack()
        assert pack.items == []
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}

    def test_pack_with_data(self):
        """Test creating a pack with data."""
        pack = Pack(
            items=[1, 2, 3],
            exotic_substances=[PackExotic(id=1, amount=5), PackExotic(id=2, amount=3)],
            samples=[1, 2],
            chits=100,
            messages=[PackMessage(type="sms", content="Test message")],
            downtime_results={"pack1": [PackDowntimeResult(message="Test result")]},
            metadata={"key": "value"},
        )

        assert pack.items == [1, 2, 3]
        assert len(pack.exotic_substances) == 2
        assert pack.exotic_substances[0].id == 1
        assert pack.exotic_substances[0].amount == 5
        assert pack.samples == [1, 2]
        assert pack.chits == 100
        assert len(pack.messages) == 1
        assert pack.messages[0].type == "sms"
        assert pack.messages[0].content == "Test message"
        assert "pack1" in pack.downtime_results
        assert len(pack.downtime_results["pack1"]) == 1
        assert pack.downtime_results["pack1"][0].message == "Test result"
        assert pack.metadata["key"] == "value"

    def test_pack_to_dict(self):
        """Test converting pack to dictionary."""
        pack = Pack(
            items=[1, 2],
            exotic_substances=[PackExotic(id=1, amount=5)],
            samples=[1],
            chits=50,
            messages=[PackMessage(type="email", content="Test email")],
            downtime_results={"pack1": [PackDowntimeResult(message="Success")]},
            metadata={"test": "data"},
        )

        pack_dict = pack.to_dict()

        assert pack_dict["items"] == [1, 2]
        assert pack_dict["exotic_substances"] == [{"id": 1, "amount": 5}]
        assert pack_dict["samples"] == [1]
        assert pack_dict["chits"] == 50
        assert pack_dict["messages"] == [{"type": "email", "content": "Test email"}]
        assert pack_dict["downtime_results"] == {"pack1": [{"message": "Success"}]}
        assert pack_dict["metadata"] == {"test": "data"}

    def test_pack_from_dict(self):
        """Test creating pack from dictionary."""
        pack_dict = {
            "items": [1, 2, 3],
            "exotic_substances": [{"id": 1, "amount": 5}, {"id": 2, "amount": 3}],
            "samples": [1, 2],
            "chits": 75,
            "messages": [{"type": "sms", "content": "Test SMS"}],
            "downtime_results": {"pack1": [{"message": "Test result"}]},
            "metadata": {"key": "value"},
        }

        pack = Pack.from_dict(pack_dict)

        assert pack.items == [1, 2, 3]
        assert len(pack.exotic_substances) == 2
        assert pack.exotic_substances[0].id == 1
        assert pack.exotic_substances[0].amount == 5
        assert pack.samples == [1, 2]
        assert pack.chits == 75
        assert len(pack.messages) == 1
        assert pack.messages[0].type == "sms"
        assert pack.messages[0].content == "Test SMS"
        assert "pack1" in pack.downtime_results
        assert len(pack.downtime_results["pack1"]) == 1
        assert pack.downtime_results["pack1"][0].message == "Test result"
        assert pack.metadata["key"] == "value"

    def test_pack_from_empty_dict(self):
        """Test creating pack from empty dictionary."""
        pack = Pack.from_dict({})
        assert pack.items == []
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}

    def test_pack_from_none(self):
        """Test creating pack from None."""
        pack = Pack.from_dict(None)
        assert pack.items == []
        assert pack.exotic_substances == []
        assert pack.samples == []
        assert pack.chits == 0
        assert pack.messages == []
        assert pack.downtime_results == {}
        assert pack.metadata == {}


class TestPackExotic:
    """Test the PackExotic class."""

    def test_pack_exotic_creation(self):
        """Test creating a PackExotic."""
        exotic = PackExotic(id=1, amount=5)
        assert exotic.id == 1
        assert exotic.amount == 5

    def test_pack_exotic_default_amount(self):
        """Test creating a PackExotic with default amount."""
        exotic = PackExotic(id=1)
        assert exotic.id == 1
        assert exotic.amount == 1


class TestPackMessage:
    """Test the PackMessage class."""

    def test_pack_message_creation(self):
        """Test creating a PackMessage."""
        message = PackMessage(type="sms", content="Test message")
        assert message.type == "sms"
        assert message.content == "Test message"


class TestPackDowntimeResult:
    """Test the PackDowntimeResult class."""

    def test_pack_downtime_result_creation(self):
        """Test creating a PackDowntimeResult."""
        result = PackDowntimeResult(message="Test result")
        assert result.message == "Test result"
