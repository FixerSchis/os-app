import pytest

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
