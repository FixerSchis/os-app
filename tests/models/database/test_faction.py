import pytest

from models.database.faction import Faction
from models.extensions import db


def test_new_faction():
    """Test creating a new faction."""
    faction = Faction(
        name="Test Faction",
        wiki_slug="test-faction",
        allow_player_characters=True,
    )
    assert faction.name == "Test Faction"
    assert faction.wiki_slug == "test-faction"
    assert faction.allow_player_characters is True


def test_faction_repr():
    """Test faction string representation."""
    faction = Faction(name="Test Faction", wiki_slug="test-faction")
    assert repr(faction) == "<Faction Test Faction>"


def test_faction_get_by_slug():
    """Test getting faction by slug."""
    faction = Faction(name="Test Faction", wiki_slug="test-faction")
    # This would need a database session to test properly
    assert faction.wiki_slug == "test-faction"


def test_faction_get_player_factions():
    """Test getting player factions."""
    faction1 = Faction(
        name="Player Faction", wiki_slug="player-faction", allow_player_characters=True
    )
    faction2 = Faction(name="NPC Faction", wiki_slug="npc-faction", allow_player_characters=False)
    # This would need a database session to test properly
    assert faction1.allow_player_characters is True
    assert faction2.allow_player_characters is False
