import pytest

from models.database.faction import Faction
from models.database.species import Species
from models.enums import CharacterStatus, Role
from models.tools.character import Character
from models.tools.user import User


def test_activate_multiple_characters_for_npc(test_client, db):
    """
    GIVEN a user with the 'npc' role and multiple characters
    WHEN the user attempts to activate more than one character
    THEN all selected characters should become active
    """
    # Create an NPC user
    npc_user = User(email="npc@example.com", first_name="NPC", surname="User")
    npc_user.set_password("password")
    npc_user.email_verified = True
    npc_user.add_role(Role.NPC.value)
    db.session.add(npc_user)
    db.session.commit()

    # Create characters for the NPC
    char1 = Character(
        user_id=npc_user.id, name="NPC Char 1", status=CharacterStatus.DEVELOPING.value
    )
    char2 = Character(
        user_id=npc_user.id, name="NPC Char 2", status=CharacterStatus.DEVELOPING.value
    )
    db.session.add_all([char1, char2])
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = npc_user.id
        session["_fresh"] = True

    # Activate both characters
    test_client.post(f"/characters/{char1.id}/activate")
    test_client.post(f"/characters/{char2.id}/activate")

    db.session.refresh(char1)
    db.session.refresh(char2)

    assert char1.status == CharacterStatus.ACTIVE.value
    assert char2.status == CharacterStatus.ACTIVE.value


def test_activate_single_character_for_normal_user(test_client, db):
    """
    GIVEN a standard user with multiple characters
    WHEN the user activates one character, and then another
    THEN only the second character should be active
    """
    # Create a standard user
    normal_user = User(email="player@example.com", first_name="Normal", surname="Player")
    normal_user.set_password("password")
    normal_user.email_verified = True
    db.session.add(normal_user)
    db.session.commit()

    # Create characters for the user
    char1 = Character(
        user_id=normal_user.id, name="Player Char 1", status=CharacterStatus.DEVELOPING.value
    )
    char2 = Character(
        user_id=normal_user.id, name="Player Char 2", status=CharacterStatus.DEVELOPING.value
    )
    db.session.add_all([char1, char2])
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = normal_user.id
        session["_fresh"] = True

    # Activate the first character
    test_client.post(f"/characters/{char1.id}/activate")
    db.session.refresh(char1)
    assert char1.status == CharacterStatus.ACTIVE.value

    # Try to activate the second character - this should fail for a normal user
    response = test_client.post(f"/characters/{char2.id}/activate", follow_redirects=True)
    db.session.refresh(char1)
    db.session.refresh(char2)

    # The first character should still be active, and the second should still be in development
    assert response.status_code == 200
    assert b"You already have an active character." in response.data
    assert char1.status == CharacterStatus.ACTIVE.value
    assert char2.status == CharacterStatus.DEVELOPING.value


def test_species_faction_validation_on_character_creation(test_client, db):
    """
    GIVEN a user creating a character
    WHEN they select a species that is not permitted for the chosen faction
    THEN the creation should fail with an appropriate error message
    """
    # Create a standard user
    user = User(email="player@example.com", first_name="Normal", surname="Player")
    user.set_password("password")
    user.email_verified = True
    db.session.add(user)
    db.session.commit()

    # Create factions
    faction1 = Faction(name="Faction 1", wiki_slug="faction-1", allow_player_characters=True)
    faction2 = Faction(name="Faction 2", wiki_slug="faction-2", allow_player_characters=True)
    db.session.add_all([faction1, faction2])
    db.session.commit()

    # Create species - species1 only allowed in faction1, species2 only allowed in faction2
    species1 = Species(
        name="Species 1",
        wiki_page="/wiki/species1",
        permitted_factions="[1]",  # Only faction1
        body_hits_type="global",
        body_hits=3,
        death_count=0,
    )
    species2 = Species(
        name="Species 2",
        wiki_page="/wiki/species2",
        permitted_factions="[2]",  # Only faction2
        body_hits_type="global",
        body_hits=3,
        death_count=0,
    )
    db.session.add_all([species1, species2])
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True

    # Try to create character with species1 and faction2 (should fail)
    response = test_client.post(
        "/characters/new",
        data={
            "name": "Test Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction2.id),  # Faction 2
            "species_id": str(species1.id),  # Species 1 (only allowed in Faction 1)
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Selected species is not permitted for the chosen faction." in response.data

    # Try to create character with species1 and faction1 (should succeed)
    response = test_client.post(
        "/characters/new",
        data={
            "name": "Test Character 2",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction1.id),  # Faction 1
            "species_id": str(species1.id),  # Species 1 (allowed in Faction 1)
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect to character list on success
    assert b"Character created successfully!" in response.data


def test_admin_bypasses_species_faction_validation(test_client, db):
    """
    GIVEN an admin user creating a character
    WHEN they select a species that is not permitted for the chosen faction
    THEN the creation should succeed (admin bypass)
    """
    # Create an admin user
    admin_user = User(email="admin@example.com", first_name="Admin", surname="User")
    admin_user.set_password("password")
    admin_user.email_verified = True
    admin_user.add_role(Role.USER_ADMIN.value)
    db.session.add(admin_user)
    db.session.commit()

    # Create factions
    faction1 = Faction(name="Faction 1", wiki_slug="faction-1", allow_player_characters=True)
    faction2 = Faction(name="Faction 2", wiki_slug="faction-2", allow_player_characters=True)
    db.session.add_all([faction1, faction2])
    db.session.commit()

    # Create species - species1 only allowed in faction1
    species1 = Species(
        name="Species 1",
        wiki_page="/wiki/species1",
        permitted_factions="[1]",  # Only faction1
        body_hits_type="global",
        body_hits=3,
        death_count=0,
    )
    db.session.add(species1)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    # Admin should be able to create character with species1 and faction2
    response = test_client.post(
        "/characters/new",
        data={
            "name": "Admin Test Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction2.id),  # Faction 2
            "species_id": str(species1.id),  # Species 1 (not normally allowed in Faction 2)
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Character created successfully!" in response.data
