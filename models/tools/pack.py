from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PackExotic:
    """Represents an exotic substance in a pack."""

    id: int
    amount: int = 1


@dataclass
class PackMessage:
    """Represents a message in a pack."""

    type: str
    content: str


@dataclass
class PackDowntimeResult:
    """Represents a downtime result entry."""

    message: str


@dataclass
class Pack:
    """A structured pack object for storing character and group pack data."""

    # Basic pack contents
    items: List[int] = field(default_factory=list)  # List of item IDs
    exotic_substances: List[PackExotic] = field(
        default_factory=list
    )  # List of exotic IDs and amounts
    samples: List[int] = field(default_factory=list)  # List of sample IDs
    chits: int = 0

    # Messages and results
    messages: List[PackMessage] = field(default_factory=list)
    downtime_results: Dict[str, List[PackDowntimeResult]] = field(default_factory=dict)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the pack to a dictionary for JSON storage."""
        return {
            "items": self.items,
            "exotic_substances": [
                {"id": exotic.id, "amount": exotic.amount} for exotic in self.exotic_substances
            ],
            "samples": self.samples,
            "chits": self.chits,
            "messages": [{"type": msg.type, "content": msg.content} for msg in self.messages],
            "downtime_results": {
                pack_id: [{"message": result.message} for result in results]
                for pack_id, results in self.downtime_results.items()
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pack":
        """Create a pack from a dictionary."""
        if not data:
            return cls()

        pack = cls()

        # Convert items (simple list of IDs)
        pack.items = data.get("items", [])

        # Convert exotic substances
        for exotic_data in data.get("exotic_substances", []):
            pack.exotic_substances.append(
                PackExotic(id=exotic_data["id"], amount=exotic_data["amount"])
            )

        # Convert samples (simple list of IDs)
        pack.samples = data.get("samples", [])

        # Set chits
        pack.chits = data.get("chits", 0)

        # Convert messages
        for msg_data in data.get("messages", []):
            pack.messages.append(PackMessage(type=msg_data["type"], content=msg_data["content"]))

        # Convert downtime results
        for pack_id, results_data in data.get("downtime_results", {}).items():
            pack.downtime_results[pack_id] = []
            for result_data in results_data:
                pack.downtime_results[pack_id].append(
                    PackDowntimeResult(message=result_data["message"])
                )

        # Set metadata
        pack.metadata = data.get("metadata", {})

        return pack

    def add_item(self, item_id: int) -> None:
        """Add an item ID to the pack. No duplicates."""
        if item_id not in self.items:
            self.items.append(item_id)

    def add_exotic(self, exotic_id: int, amount: int) -> None:
        """Add an exotic substance to the pack. If already exists, increase amount."""
        for exotic in self.exotic_substances:
            if exotic.id == exotic_id:
                exotic.amount += amount
                return

        # If not found, add new
        self.exotic_substances.append(PackExotic(id=exotic_id, amount=amount))

    def add_sample(self, sample_id: int) -> None:
        """Add a sample ID to the pack. No duplicates."""
        if sample_id not in self.samples:
            self.samples.append(sample_id)

    def add_message(self, message_type: str, content: str) -> None:
        """Add a message to the pack."""
        self.messages.append(PackMessage(type=message_type, content=content))

    def add_downtime_result(self, pack_id: str, message: str) -> None:
        """Add a downtime result message."""
        if pack_id not in self.downtime_results:
            self.downtime_results[pack_id] = []
        self.downtime_results[pack_id].append(PackDowntimeResult(message=message))

    def has_item(self, item_id: int) -> bool:
        """Check if the pack has a specific item."""
        return item_id in self.items

    def has_exotic(self, exotic_id: int) -> bool:
        """Check if the pack has a specific exotic substance."""
        return any(exotic.id == exotic_id for exotic in self.exotic_substances)

    def has_sample(self, sample_id: int) -> bool:
        """Check if the pack has a specific sample."""
        return sample_id in self.samples

    def get_exotic_amount(self, exotic_id: int) -> int:
        """Get the amount of a specific exotic substance in the pack."""
        for exotic in self.exotic_substances:
            if exotic.id == exotic_id:
                return exotic.amount
        return 0

    def remove_item(self, item_id: int) -> bool:
        """Remove an item from the pack by ID."""
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def remove_exotic(self, exotic_id: int, amount: int = None) -> bool:
        """Remove an exotic substance from the pack by ID.
        If amount specified, reduce by that amount."""
        for i, exotic in enumerate(self.exotic_substances):
            if exotic.id == exotic_id:
                if amount is None or exotic.amount <= amount:
                    # Remove completely
                    del self.exotic_substances[i]
                else:
                    # Reduce amount
                    exotic.amount -= amount
                return True
        return False

    def remove_sample(self, sample_id: int) -> bool:
        """Remove a sample from the pack by ID."""
        if sample_id in self.samples:
            self.samples.remove(sample_id)
            return True
        return False
