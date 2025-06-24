import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Pack:
    items: List[int] = field(default_factory=list)
    samples: List[int] = field(default_factory=list)
    exotics: List[int] = field(default_factory=list)
    medicaments: List[int] = field(default_factory=list)
    energy_chits: int = 0
    completion: Dict[str, bool] = field(default_factory=dict)
    is_generated: bool = False

    def is_complete(self) -> bool:
        required_items = ["character_sheet", "character_id_badge"]
        required_items += [f"item_{item_id}" for item_id in self.items if self.has_item(item_id)]
        required_items += [
            f"sample_{sample_id}" for sample_id in self.samples if self.has_sample(sample_id)
        ]
        required_items += [
            f"exotic_{exotic_id}" for exotic_id in self.exotics if self.has_exotic(exotic_id)
        ]
        required_items += [
            f"medicament_{medicament_id}"
            for medicament_id in self.medicaments
            if self.has_medicament(medicament_id)
        ]
        if self.energy_chits > 0:
            required_items.append("energy_chits")
        return all(self.completion.get(item, False) for item in required_items)

    def add_item(self, item_id: int) -> None:
        if item_id not in self.items:
            self.items.append(item_id)

    def remove_item(self, item_id: int) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def has_item(self, item_id: int) -> bool:
        return item_id in self.items

    def add_exotic(self, exotic_id: int) -> None:
        if exotic_id not in self.exotics:
            self.exotics.append(exotic_id)

    def remove_exotic(self, exotic_id: int) -> bool:
        if exotic_id in self.exotics:
            self.exotics.remove(exotic_id)
            return True
        return False

    def has_exotic(self, exotic_id: int) -> bool:
        return exotic_id in self.exotics

    def add_sample(self, sample_id: int) -> None:
        if sample_id not in self.samples:
            self.samples.append(sample_id)

    def remove_sample(self, sample_id: int) -> bool:
        if sample_id in self.samples:
            self.samples.remove(sample_id)
            return True
        return False

    def has_sample(self, sample_id: int) -> bool:
        return sample_id in self.samples

    def add_medicament(self, medicament_id: int) -> None:
        if medicament_id not in self.medicaments:
            self.medicaments.append(medicament_id)

    def remove_medicament(self, medicament_id: int) -> bool:
        if medicament_id in self.medicaments:
            self.medicaments.remove(medicament_id)
            return True
        return False

    def has_medicament(self, medicament_id: int) -> bool:
        return medicament_id in self.medicaments

    def set_completion(self, key: str, value: bool) -> None:
        self.completion[key] = value

    @property
    def is_completed(self) -> bool:
        # All required items must be checked in completion
        required_keys = []

        # Only require energy_chits if there are energy chits in the pack
        if self.energy_chits > 0:
            required_keys.append("energy_chits")

        # Always require character sheet and ID badge
        required_keys.append("character_sheet")
        required_keys.append("character_id_badge")

        # Add items, samples, exotics, and medicaments that are in the pack
        required_keys += [f"item_{item_id}" for item_id in self.items]
        required_keys += [f"sample_{sample_id}" for sample_id in self.samples]
        required_keys += [f"exotic_{exotic_id}" for exotic_id in self.exotics]
        required_keys += [f"medicament_{medicament_id}" for medicament_id in self.medicaments]

        return all(self.completion.get(key, False) for key in required_keys)

    def to_dict(self) -> Dict:
        try:
            # Ensure completion dict only contains boolean values
            clean_completion = {}
            for key, value in self.completion.items():
                if isinstance(key, str) and isinstance(value, bool):
                    clean_completion[key] = value
                else:
                    # Convert non-boolean values to boolean and ensure key is string
                    clean_completion[str(key)] = bool(value)

            result = {
                "items": self.items,
                "samples": self.samples,
                "exotics": self.exotics,
                "medicaments": self.medicaments,
                "energy_chits": self.energy_chits,
                "completion": clean_completion,
                "is_generated": self.is_generated,
            }

            return result
        except Exception:
            # Return a safe default if there's an error
            return {
                "items": [],
                "samples": [],
                "exotics": [],
                "medicaments": [],
                "energy_chits": 0,
                "completion": {},
            }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, data: str) -> "Pack":
        if not data:
            return cls()
        try:
            d = json.loads(data)
            # Filter out computed properties that are not constructor parameters
            d.pop("is_completed", None)
            is_generated = d.pop("is_generated", False)
            pack = cls(**d)
            pack.is_generated = is_generated
            return pack
        except Exception:
            # Return a default pack if there's an error
            return cls()
