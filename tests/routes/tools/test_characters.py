import pytest

from models.database.faction import Faction
from models.database.species import Species
from models.enums import CharacterStatus
from models.tools.character import Character
from models.tools.user import User


def test_activate_multiple_characters_for_npc(test_client, db):
    """
    GIVEN a user with the 'npc' role and multiple characters
    WHEN the user attempts to activate more than one character
    THEN all selected characters should become active
    """
    # Create an NPC user with proper role assignment
    npc_user = User(email="npc@example.com", first_name="NPC", surname="User")
    npc_user.set_password("password")
    npc_user.email_verified = True
    db.session.add(npc_user)
    db.session.commit()

    # Assign NPC role with permissions
    from tests.conftest import assign_role_to_user

    assign_role_to_user(npc_user, "npc", db.session)

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
    # Create an admin user with proper role assignment
    admin_user = User(email="admin@example.com", first_name="Admin", surname="User")
    admin_user.set_password("password")
    admin_user.email_verified = True
    db.session.add(admin_user)
    db.session.commit()

    # Assign admin role with permissions
    from tests.conftest import assign_role_to_user

    assign_role_to_user(admin_user, "admin", db.session)

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


def test_character_activation_with_starting_items(test_client, db, new_user):
    """Test that character activation creates starting items through the route."""
    from models.database.item import Item
    from models.database.item_blueprint import ItemBlueprint
    from models.database.item_type import ItemType
    from models.database.species import Ability, Species
    from models.enums import AbilityType, BodyHitsType, CharacterStatus

    # Create item type and blueprint
    item_type = ItemType(id=1, name="Test Weapon", id_prefix="TW")
    db.session.add(item_type)
    db.session.flush()

    blueprint = ItemBlueprint(
        id=1, name="Test Weapon Blueprint", item_type_id=item_type.id, blueprint_id=1, base_cost=100
    )
    db.session.add(blueprint)
    db.session.flush()

    # Create species with starting item ability
    species = Species(
        name="Test Species",
        wiki_page="test-species",
        permitted_factions_list=[1],
        body_hits_type=BodyHitsType.GLOBAL,
        body_hits=3,
        death_count=3,
    )
    db.session.add(species)
    db.session.flush()

    ability = Ability(
        name="Starting Weapon",
        description="This species starts with a weapon",
        type=AbilityType.STARTING_ITEM,
        species=species,
        starting_item_blueprint_id=blueprint.id,
    )
    db.session.add(ability)
    db.session.commit()

    # Create character
    character = Character(
        name="Test Character",
        user_id=new_user.id,
        species_id=species.id,
        status=CharacterStatus.DEVELOPING.value,
    )
    db.session.add(character)
    db.session.commit()

    # Give the user some character points
    new_user.character_points = 10
    db.session.commit()

    # Login as the character owner
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    # Activate character through the route
    test_client.post(f"/characters/{character.id}/activate", follow_redirects=True)

    # Verify the character was activated
    db.session.refresh(character)
    assert character.status == CharacterStatus.ACTIVE.value

    # Verify the starting item was created and added to the character's inventory
    from models.tools.character_inventory import CharacterItem

    character_items = CharacterItem.query.filter_by(character_id=character.id).all()
    assert len(character_items) == 1

    character_item = character_items[0]
    item = Item.query.get(character_item.item_id)
    assert item is not None
    assert item.blueprint_id == blueprint.id
    assert item.item_id == 1  # First item for this blueprint


def test_retire_character_uses_correct_id(test_client, authenticated_user, db):
    """Test that retiring a character uses the correct character ID."""
    # Give the user character.edit_all permission
    from tests.conftest import assign_role_to_user

    assign_role_to_user(authenticated_user, "admin", db.session)

    # Create a character for the user
    character = Character(
        user_id=authenticated_user.id,
        name="Test Character",
        status=CharacterStatus.ACTIVE.value,
        character_id=1,  # This is the character number, not the database ID
    )
    db.session.add(character)
    db.session.commit()

    # Store the database ID for verification
    db_character_id = character.id

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    # Retire the character
    response = test_client.post(f"/characters/{db_character_id}/retire", follow_redirects=True)
    assert response.status_code == 200

    # Verify the correct character was retired
    db.session.refresh(character)
    assert character.status == CharacterStatus.RETIRED.value
    assert character.id == db_character_id  # Should be the same database ID


def test_restore_retired_character_redirects(test_client, authenticated_user, db):
    """Restoring a retired character commits the status and returns a redirect."""
    from tests.conftest import assign_role_to_user

    assign_role_to_user(authenticated_user, "admin", db.session)

    character = Character(
        user_id=authenticated_user.id,
        name="Retired Character",
        status=CharacterStatus.RETIRED.value,
        character_id=1,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.post(f"/characters/{character.id}/restore")
    assert response.status_code == 302
    assert "/characters" in response.location

    db.session.refresh(character)
    assert character.status == CharacterStatus.ACTIVE.value


def test_restore_from_admin_context_returns_to_user(test_client, authenticated_user, db):
    """Restoring from the user admin page returns to that user."""
    from tests.conftest import assign_role_to_user

    assign_role_to_user(authenticated_user, "admin", db.session)

    owner = User(email="restore.owner@example.com", first_name="Rest", surname="Owner")
    owner.set_password("password")
    owner.email_verified = True
    db.session.add(owner)
    db.session.commit()

    character = Character(
        user_id=owner.id,
        name="Dead Character",
        status=CharacterStatus.DEAD.value,
        character_id=1,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    response = test_client.post(
        f"/characters/{character.id}/restore",
        data={"admin_context": "1"},
    )
    assert response.status_code == 302
    assert f"/users/user-management/user/{owner.id}" in response.location

    db.session.refresh(character)
    assert character.status == CharacterStatus.ACTIVE.value


def test_character_search_by_name_user_and_id(test_client, authenticated_user, db):
    """Search finds active characters by character name, user name, and player reference."""
    owner = User(email="owner.search@example.com", first_name="Ada", surname="Lovelace")
    owner.set_password("password")
    owner.email_verified = True
    other = User(email="other.search@example.com", first_name="Grace", surname="Hopper")
    other.set_password("password")
    db.session.add_all([owner, other])
    db.session.commit()

    named = Character(
        user_id=owner.id,
        name="Analytical Engine",
        status=CharacterStatus.ACTIVE.value,
        character_id=1,
    )
    by_user = Character(
        user_id=other.id,
        name="Compiler",
        status=CharacterStatus.ACTIVE.value,
        character_id=2,
    )
    developing = Character(
        user_id=owner.id,
        name="Analytical Draft",
        status=CharacterStatus.DEVELOPING.value,
        character_id=3,
    )
    db.session.add_all([named, by_user, developing])
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = authenticated_user.id
        session["_fresh"] = True

    by_name = test_client.get("/characters/api/search?q=Analytical")
    assert by_name.status_code == 200
    name_ids = [item["id"] for item in by_name.get_json()["items"]]
    assert named.id in name_ids
    assert developing.id not in name_ids

    by_surname = test_client.get("/characters/api/search?q=Hopper")
    assert by_user.id in [item["id"] for item in by_surname.get_json()["items"]]

    by_full_name = test_client.get("/characters/api/search?q=Ada Lovelace")
    full_name_ids = [item["id"] for item in by_full_name.get_json()["items"]]
    assert named.id in full_name_ids
    assert by_user.id not in full_name_ids

    by_reference = test_client.get(f"/characters/api/search?q={other.id}.2")
    reference_items = by_reference.get_json()["items"]
    assert [item["id"] for item in reference_items] == [by_user.id]
    assert reference_items[0]["player_reference"] == f"{other.id}.2"

    assert test_client.get("/characters/api/search?q=A").get_json()["items"] == []


def _button_form_owners(html):
    """Map button aria-labels to the form a browser would submit.

    Nested form start tags are ignored, and the next form end tag closes the open form.
    """
    import re

    def attr(attrs, name):
        match = re.search(rf'{name}="([^"]*)"', attrs or "", flags=re.IGNORECASE)
        return match.group(1) if match else None

    pattern = re.compile(r"<form\b([^>]*)>|</form>|<button\b([^>]*)>", re.IGNORECASE)
    owners = {}
    open_form_id = None
    for match in pattern.finditer(html):
        token = match.group(0).lower()
        if token.startswith("<form"):
            if open_form_id is None:
                open_form_id = attr(match.group(1), "id") or ""
        elif token.startswith("</form"):
            open_form_id = None
        else:
            label = attr(match.group(2), "aria-label")
            if not label:
                continue
            explicit = attr(match.group(2), "form")
            owners[label] = explicit if explicit is not None else open_form_id
    return owners


def test_admin_character_edit_save_stays_on_character_form(test_client, db):
    """Save Changes, conditions, and samples stay on the character form."""
    from tests.conftest import assign_role_to_user

    admin = User(email="save-form-admin@example.com", first_name="Save", surname="Admin")
    admin.set_password("password")
    admin.email_verified = True
    db.session.add(admin)
    db.session.commit()
    assign_role_to_user(admin, "admin", db.session)

    faction = Faction(name="Save Faction", wiki_slug="save-faction", allow_player_characters=True)
    db.session.add(faction)
    db.session.flush()
    species = Species(
        name="Save Species",
        wiki_page="save-species",
        body_hits_type="locational",
        body_hits=3,
        death_count=1,
        permitted_factions_list=[faction.id],
    )
    db.session.add(species)
    db.session.flush()
    character = Character(
        user_id=admin.id,
        name="Save Subject",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
    )
    db.session.add(character)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin.id
        session["_fresh"] = True

    response = test_client.get(f"/characters/{character.id}/edit")
    assert response.status_code == 200
    owners = _button_form_owners(response.get_data(as_text=True))
    assert owners["Save character changes"] == "character-edit-form"
    assert owners["Add condition to character"] == "character-edit-form"
    assert owners["Add sample to character"] == "character-edit-form"


def test_admin_character_edit_commits_conditions_and_points(test_client, db):
    """Saving the character form stores condition stage, duration, and base points."""
    from models.database.conditions import Condition, ConditionStage
    from models.tools.character import CharacterCondition
    from tests.conftest import assign_role_to_user

    admin = User(email="save-points-admin@example.com", first_name="Points", surname="Admin")
    admin.set_password("password")
    admin.email_verified = True
    db.session.add(admin)
    db.session.commit()
    assign_role_to_user(admin, "admin", db.session)

    faction = Faction(
        name="Points Faction", wiki_slug="points-faction", allow_player_characters=True
    )
    db.session.add(faction)
    db.session.flush()
    species = Species(
        name="Points Species",
        wiki_page="points-species",
        body_hits_type="locational",
        body_hits=3,
        death_count=1,
        permitted_factions_list=[faction.id],
    )
    db.session.add(species)
    db.session.flush()
    character = Character(
        user_id=admin.id,
        name="Points Subject",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
        base_character_points=10,
    )
    db.session.add(character)
    db.session.flush()

    condition = Condition(name="Lingering Chill")
    db.session.add(condition)
    db.session.flush()
    db.session.add_all(
        [
            ConditionStage(
                condition_id=condition.id,
                stage_number=1,
                rp_effect="Shivers",
                diagnosis="Cold",
                cure="Warmth",
                duration=3,
            ),
            ConditionStage(
                condition_id=condition.id,
                stage_number=2,
                rp_effect="Fever",
                diagnosis="Worse cold",
                cure="Rest",
                duration=1,
            ),
        ]
    )
    character_condition = CharacterCondition(
        character_id=character.id,
        condition_id=condition.id,
        current_stage=1,
        current_duration=3,
    )
    db.session.add(character_condition)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin.id
        session["_fresh"] = True

    response = test_client.post(
        f"/characters/{character.id}/edit",
        data={
            "name": "Points Subject",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "",
            "goals": "",
            "concept": "",
            "base_character_points": "25",
            f"condition_stage_{character_condition.id}": "2",
            f"condition_duration_{character_condition.id}": "1",
        },
    )
    assert response.status_code == 302

    db.session.refresh(character)
    db.session.refresh(character_condition)
    assert character.base_character_points == 25
    assert character_condition.current_stage == 2
    assert character_condition.current_duration == 1

    rejected = test_client.post(
        f"/characters/{character.id}/edit",
        data={
            "name": "Points Subject",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "base_character_points": "-3",
            f"condition_stage_{character_condition.id}": "1",
            f"condition_duration_{character_condition.id}": "0",
        },
        follow_redirects=True,
    )
    assert rejected.status_code == 200
    assert b"Base character points cannot be negative." in rejected.data
    db.session.refresh(character)
    db.session.refresh(character_condition)
    assert character.base_character_points == 25
    assert character_condition.current_stage == 2
    assert character_condition.current_duration == 1


def test_user_editor_sets_owner_earned_points_from_character_page(test_client, db):
    """Staff with user.edit set the owner's earned pool on the character form; players cannot."""
    from tests.conftest import assign_role_to_user

    admin = User(email="earned-admin@example.com", first_name="Earned", surname="Admin")
    admin.set_password("password")
    admin.email_verified = True
    player = User(email="earned-player@example.com", first_name="Earned", surname="Player")
    player.set_password("password")
    player.email_verified = True
    db.session.add_all([admin, player])
    db.session.commit()
    assign_role_to_user(admin, "admin", db.session)
    faction = Faction(name="Earned Faction", wiki_slug="earned", allow_player_characters=True)
    db.session.add(faction)
    db.session.flush()
    species = Species(
        name="Earned Species",
        wiki_page="earned-species",
        body_hits_type="locational",
        body_hits=3,
        death_count=1,
        permitted_factions_list=[faction.id],
    )
    db.session.add(species)
    db.session.flush()
    character = Character(
        user_id=player.id,
        name="Earned Subject",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
    )
    db.session.add(character)
    db.session.commit()
    form = {
        "name": "Earned Subject",
        "pronouns_subject": "they",
        "pronouns_object": "them",
        "faction": str(faction.id),
        "species_id": str(species.id),
        "base_character_points": "10",
    }

    with test_client.session_transaction() as session:
        session["_user_id"] = admin.id
        session["_fresh"] = True
    page = test_client.get(f"/characters/{character.id}/edit").get_data(as_text=True)
    assert 'name="earned_character_points"' in page

    test_client.post(
        f"/characters/{character.id}/edit", data={**form, "earned_character_points": "2.5"}
    )
    db.session.refresh(player)
    assert player.character_points == 2.5

    for bad, message in (
        ("-1", b"Earned character points cannot be negative."),
        ("1.25", b"Earned character points must be a whole or half point."),
    ):
        response = test_client.post(
            f"/characters/{character.id}/edit",
            data={**form, "earned_character_points": bad},
            follow_redirects=True,
        )
        assert message in response.data
    db.session.refresh(player)
    assert player.character_points == 2.5

    from flask import g

    # The fixture's app context outlives requests, so Flask-Login's cached user must go too.
    g.pop("_login_user", None)
    with test_client.session_transaction() as session:
        session["_user_id"] = player.id
        session["_fresh"] = True
    page = test_client.get(f"/characters/{character.id}/edit").get_data(as_text=True)
    assert 'name="earned_character_points"' not in page
    test_client.post(
        f"/characters/{character.id}/edit", data={**form, "earned_character_points": "50"}
    )
    db.session.refresh(player)
    assert player.character_points == 2.5


def test_create_character_page_has_no_character_abilities(test_client, db):
    """Character abilities are only edited on an existing character, even by staff."""
    from tests.conftest import assign_role_to_user

    admin = User(email="create-abilities@example.com", first_name="Create", surname="Admin")
    admin.set_password("password")
    admin.email_verified = True
    db.session.add(admin)
    db.session.commit()
    assign_role_to_user(admin, "admin", db.session)
    faction = Faction(
        name="Ability Faction", wiki_slug="ability-faction", allow_player_characters=True
    )
    db.session.add(faction)
    db.session.flush()
    species = Species(
        name="Ability Species",
        wiki_page="ability-species",
        body_hits_type="locational",
        body_hits=3,
        death_count=1,
        permitted_factions_list=[faction.id],
    )
    db.session.add(species)
    db.session.commit()
    with test_client.session_transaction() as session:
        session["_user_id"] = admin.id
        session["_fresh"] = True

    page = test_client.get("/characters/new").get_data(as_text=True)
    assert "Character Abilities" not in page
    assert "add-character-ability" not in page

    response = test_client.post(
        "/characters/new",
        data={
            "name": "No Abilities",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "character_ability_name_0": "Smuggled",
            "character_ability_description_0": "Should not be saved.",
        },
    )
    assert response.status_code == 302
    character = Character.query.filter_by(name="No Abilities").one()
    assert character.abilities == []


def _black_frost_species(db, prefix):
    from models.database.conditions import Condition, ConditionStage
    from models.database.species import Ability
    from models.enums import AbilityType

    faction = Faction(
        name=f"{prefix} Faction", wiki_slug=f"{prefix}-faction", allow_player_characters=True
    )
    db.session.add(faction)
    db.session.flush()
    species = Species(
        name=f"{prefix} Raegar",
        wiki_page=f"{prefix}-raegar",
        body_hits_type="locational",
        body_hits=2,
        death_count=300,
        permitted_factions_list=[faction.id],
    )
    condition = Condition(name=f"{prefix} Black Frost", progresses_naturally=False)
    condition.stage_sheet_values_list = [{"id": "will", "description": "Will Points", "value": 1}]
    db.session.add_all([species, condition])
    db.session.flush()
    for stage_number in range(1, 11):
        db.session.add(
            ConditionStage(
                condition_id=condition.id,
                stage_number=stage_number,
                rp_effect="Boils",
                diagnosis="Boils",
                cure="None",
                duration=0,
            )
        )
    db.session.add(
        Ability(
            species_id=species.id,
            name="Black Frost",
            description="Starts at a chosen stage.",
            type=AbilityType.STARTING_CONDITION,
            starting_condition_id=condition.id,
        )
    )
    db.session.commit()
    return faction, species, condition


def _login_player(test_client, db, email):
    user = User(email=email, first_name="Frost", surname="Player")
    user.set_password("password")
    user.email_verified = True
    db.session.add(user)
    db.session.commit()
    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True
    return user


def test_new_character_starts_with_chosen_condition_stage(test_client, db):
    """A Raegar starts Black Frost at the chosen stage, with 1 Will Point per stage."""
    from models.tools.character import CharacterCondition

    faction, species, condition = _black_frost_species(db, "Chosen")
    user = _login_player(test_client, db, "frost-chosen@example.com")
    field = f"starting_condition_stage_{condition.id}"
    base = {
        "name": "Tyyn Staiger",
        "pronouns_subject": "they",
        "pronouns_object": "them",
        "faction": str(faction.id),
        "species_id": str(species.id),
    }

    for bad_stage in ("", "0", "11"):
        response = test_client.post(
            "/characters/new", data={**base, field: bad_stage}, follow_redirects=True
        )
        assert b"Choose a Chosen Black Frost starting stage from 1 to 10." in response.data
    assert Character.query.filter_by(user_id=user.id).count() == 0

    response = test_client.post("/characters/new", data={**base, field: "4"})
    assert response.status_code == 302
    character = Character.query.filter_by(user_id=user.id).one()
    active = CharacterCondition.query.filter_by(character_id=character.id).one()
    assert active.condition_id == condition.id
    assert active.current_stage == 4
    assert character.get_character_sheet_values()["will"] == {"name": "Will Points", "value": 4}


def test_starting_stage_changes_only_while_developing(test_client, db):
    """The owner can change the chosen stage while developing, and not after activation."""
    from models.tools.character import CharacterCondition

    faction, species, condition = _black_frost_species(db, "Developing")
    user = _login_player(test_client, db, "frost-developing@example.com")
    field = f"starting_condition_stage_{condition.id}"
    base = {
        "name": "Tyyn Rask",
        "pronouns_subject": "they",
        "pronouns_object": "them",
        "faction": str(faction.id),
        "species_id": str(species.id),
    }
    test_client.post("/characters/new", data={**base, field: "2"})
    character = Character.query.filter_by(user_id=user.id).one()

    test_client.post(f"/characters/{character.id}/edit", data={**base, field: "7"})
    active = CharacterCondition.query.filter_by(character_id=character.id).one()
    assert active.current_stage == 7

    character.status = CharacterStatus.ACTIVE.value
    db.session.commit()
    test_client.post(f"/characters/{character.id}/edit", data={**base, field: "1"})
    db.session.refresh(active)
    assert active.current_stage == 7
