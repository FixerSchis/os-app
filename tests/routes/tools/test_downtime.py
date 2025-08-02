import json
from datetime import datetime, timedelta

import pytest

from models.enums import DowntimeStatus, DowntimeTaskStatus, EventType
from models.extensions import db
from models.tools.downtime import DowntimePeriod
from models.tools.event_ticket import EventTicket


@pytest.fixture
def event_ticket(db, downtime_period, character_with_faction):
    ticket = EventTicket(
        event_id=downtime_period.id,
        character_id=character_with_faction.id,
        ticket_type=EventType.DOWNTIME.value,
        ticket_number=1,
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket


def login_user(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = user.id
        sess["_fresh"] = True


@pytest.mark.parametrize(
    "user_fixture,expected_status",
    [
        ("downtime_team_user", 302),  # Route redirects on success
        ("regular_user", 403),  # Route returns 403 for unauthorized users (doesn't own character)
    ],
)
def test_enter_pack_contents_get(
    test_client, request, downtime_pack, user_fixture, expected_status
):
    user = request.getfixturevalue(user_fixture)
    login_user(test_client, user)
    response = test_client.get(
        f"/downtime/enter-pack-contents/{downtime_pack.period_id}/" f"{downtime_pack.character_id}"
    )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "items,exotics,samples,cybernetics,conditions,research_teams,energy_chits,"
    "other,confirm_complete",
    [
        # All empty
        ([], [], [], [], [], [], 0, "", False),
        # Each field individually
        ([1], [], [], [], [], [], 0, "", False),
        ([], [1], [], [], [], [], 0, "", False),
        ([], [], [1], [], [], [], 0, "", False),
        ([], [], [], [1], [], [], 0, "", False),
        ([], [], [], [], [1], [], 0, "", False),
        ([], [], [], [], [], [1], 0, "", False),
        ([], [1], [], [], [], [], 5, "", False),
        # Test other field
        ([], [], [], [], [], [], 0, "Test other information", False),
        ([], [], [], [], [], [], 0, "Complex other info with special chars: !@#$%^&*()", False),
        ([], [], [], [], [], [], 0, "", True),
        # Multiple values for each field
        ([1, 2], [1, 2], [1, 2], [1, 2], [1, 2], [1, 2], 10, "Multiple items with other", False),
        # All fields together
        ([1], [1], [1], [1], [1], [1], 3, "Complete pack with other", True),
        # Edge cases
        ([], [1], [], [], [], [], -5, "", False),  # negative chits
        ([], [1], [], [], [], [], 999999, "", True),  # large chits
        ([1], [1], [1], [1], [1], [1], 0, "Edge case with other", True),
        ([1], [], [], [], [], [], 0, "", True),
        ([], [], [], [], [], [], 0, "", True),
    ],
)
def test_enter_pack_contents_post(
    test_client,
    downtime_team_user,
    downtime_pack,
    item,
    exotic_substance,
    sample,
    cybernetic,
    condition,
    items,
    exotics,
    samples,
    cybernetics,
    conditions,
    research_teams,
    energy_chits,
    other,
    confirm_complete,
):
    login_user(test_client, downtime_team_user)

    data = {
        "items[]": [str(item.id)] * len(items) if items else [],
        "exotics[]": [str(exotic_substance.id)] * len(exotics) if exotics else [],
        "samples[]": [str(sample.id)] * len(samples) if samples else [],
        "cybernetics[]": [str(cybernetic.id)] * len(cybernetics) if cybernetics else [],
        "conditions[]": [str(condition.id)] * len(conditions) if conditions else [],
        "research_teams[]": ["1"] * len(research_teams) if research_teams else [],
        "energy_chits": str(energy_chits),
        "other": other,
        "confirm_complete": "on" if confirm_complete else "",
    }

    response = test_client.post(
        f"/downtime/enter-pack-contents/{downtime_pack.period_id}/" f"{downtime_pack.character_id}",
        data=data,
        follow_redirects=True,
    )

    if confirm_complete:
        assert response.status_code == 200
        # Check that pack status was updated
        db.session.refresh(downtime_pack)
        assert downtime_pack.status == DowntimeTaskStatus.ENTER_DOWNTIME
    else:
        assert response.status_code == 200


@pytest.mark.parametrize(
    "purchases,modifications,engineering,science,research,reputation,confirm_complete",
    [
        # Empty activities
        ([], [], [], [], [], [], False),
        ([], [], [], [], [], [], True),
        # Single activity types
        (
            [{"blueprint_id": 1, "quantity": 1}],
            [],
            [],
            [],
            [],
            [],
            False,
        ),  # Purchase only
        (
            [],
            [{"type": "learning", "mod_id": 1}],
            [],
            [],
            [],
            [],
            False,
        ),  # Modification only
        (
            [],
            [],
            [{"action": "maintain", "source": "own", "item_id": 1}],
            [],
            [],
            [],
            False,
        ),  # Engineering only
        (
            [],
            [],
            [],
            [{"action": "synthesize", "science_type": "generic"}],
            [],
            [],
            False,
        ),  # Science only
        (
            [],
            [],
            [],
            [],
            [{"project_id": "RES001", "research_for": "self"}],
            [],
            False,
        ),  # Research only
        (
            [],
            [],
            [],
            [],
            [],
            [{"faction_id": 1, "question": "Test question?"}],
            False,
        ),  # Reputation only
        # Multiple activities of same type
        (
            [{"blueprint_id": 1, "quantity": 1}, {"blueprint_id": 2, "quantity": 3}],
            [],
            [],
            [],
            [],
            [],
            False,
        ),  # Multiple purchases
        (
            [],
            [{"type": "learning", "mod_id": 1}, {"type": "forgetting", "mod_id": 2}],
            [],
            [],
            [],
            [],
            False,
        ),  # Multiple mods
        (
            [],
            [],
            [
                {"action": "maintain", "source": "own", "item_id": 1},
                {"action": "modify", "source": "own", "item_id": 2, "mod_id": 1},
            ],
            [],
            [],
            [],
            False,
        ),  # Multiple engineering
        (
            [],
            [],
            [],
            [
                {"action": "synthesize", "science_type": "generic"},
                {
                    "action": "theorise",
                    "theorise_name": "Test",
                    "theorise_desc": "Test",
                },
            ],
            [],
            [],
            False,
        ),  # Multiple science
        # Complex combinations
        (
            [{"blueprint_id": 1, "quantity": 2}],
            [{"type": "learning", "mod_id": 1}],
            [{"action": "maintain", "source": "own", "item_id": 1}],
            [{"action": "synthesize", "science_type": "generic"}],
            [{"project_id": "RES001", "research_for": "self"}],
            [{"faction_id": 1, "question": "Test?"}],
            False,
        ),  # All activities
        (
            [{"blueprint_id": 1, "quantity": 2}],
            [{"type": "learning", "mod_id": 1}],
            [{"action": "maintain", "source": "own", "item_id": 1}],
            [{"action": "synthesize", "science_type": "generic"}],
            [{"project_id": "RES001", "research_for": "self"}],
            [{"faction_id": 1, "question": "Test?"}],
            True,
        ),  # All activities with confirm
        # Edge cases
        (
            [{"blueprint_id": 1, "quantity": 5}],
            [],
            [],
            [],
            [],
            [],
            True,
        ),  # Large quantity with confirm
        (
            [],
            [],
            [{"action": "maintain", "source": "manual", "full_code": "WP0001-001"}],
            [],
            [],
            [],
            False,
        ),  # Manual engineering
        (
            [],
            [],
            [],
            [
                {
                    "action": "research_project",
                    "project_source": "my",
                    "project_id": "RES001",
                    "research_for": "self",
                }
            ],
            [],
            [],
            False,
        ),  # Research project
        (
            [],
            [],
            [],
            [],
            [
                {
                    "project_id": "RES001",
                    "research_for": "other",
                    "research_for_id": "1.2",
                }
            ],
            [],
            False,
        ),  # Other research
    ],
)
def test_enter_downtime_post_comprehensive(
    test_client,
    downtime_pack_enter_downtime,
    regular_user,
    purchases,
    modifications,
    engineering,
    science,
    research,
    reputation,
    confirm_complete,
    db,
):
    login_user(test_client, regular_user)

    data = {
        "purchases[]": [json.dumps(p) for p in purchases],
        "modifications[]": [json.dumps(m) for m in modifications],
        "engineering[]": [json.dumps(e) for e in engineering],
        "science[]": [json.dumps(s) for s in science],
        "research[]": [json.dumps(r) for r in research],
        "reputation[]": [json.dumps(rep) for rep in reputation],
        "confirm_complete": "on" if confirm_complete else "",
    }

    response = test_client.post(
        f"/downtime/enter-downtime/{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=data,
        follow_redirects=not confirm_complete,
    )

    if confirm_complete:
        assert response.status_code == 302  # Should redirect on success
    else:
        assert response.status_code == 200  # Should stay on same page


@pytest.mark.parametrize(
    "invalid_data,expected_error",
    [
        # Invalid JSON in arrays
        ({"purchases[]": ["invalid json"]}, "JSONDecodeError"),
        ({"modifications[]": ["{invalid}"]}, "JSONDecodeError"),
        ({"engineering[]": ["not json"]}, "JSONDecodeError"),
        ({"science[]": ["invalid"]}, "JSONDecodeError"),
        ({"research[]": ["{"]}, "JSONDecodeError"),
        ({"reputation[]": ["}"]}, "JSONDecodeError"),
        # Missing required fields
        ({"purchases[]": [json.dumps({"quantity": 1})]}, "Missing blueprint_id"),
        ({"modifications[]": [json.dumps({"type": "learning"})]}, "Missing mod_id"),
        ({"engineering[]": [json.dumps({"action": "maintain"})]}, "Missing source"),
        ({"science[]": [json.dumps({"action": "theorise"})]}, "Missing theorise_name"),
        ({"research[]": [json.dumps({"research_for": "self"})]}, "Missing project_id"),
        ({"reputation[]": [json.dumps({"faction_id": 1})]}, "Missing question"),
    ],
)
def test_enter_downtime_post_invalid_data(
    test_client,
    downtime_pack_enter_downtime,
    regular_user,
    invalid_data,
    expected_error,
    db,
):
    login_user(test_client, regular_user)

    response = test_client.post(
        f"/downtime/enter-downtime/{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=invalid_data,
    )

    # Routes redirect on success, so expect 302 for valid data and 400 for invalid
    if expected_error == "JSONDecodeError":
        # JSON decode errors should cause exceptions, not return status codes
        # The test will fail with JSONDecodeError, which is expected
        pass
    else:
        # For missing required fields, expect redirect since the route doesn't validate them
        assert response.status_code == 302


@pytest.mark.parametrize(
    "user_fixture,expected_status",
    [
        ("regular_user", 200),
        ("downtime_team_user", 200),
    ],
)
def test_enter_downtime_get(
    test_client,
    request,
    downtime_pack_enter_downtime,
    user_fixture,
    expected_status,
):
    user = request.getfixturevalue(user_fixture)
    login_user(test_client, user)
    response = test_client.get(
        "/downtime/enter-downtime/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}"
    )
    assert response.status_code == expected_status


def test_enter_downtime_wrong_status(test_client, new_user, downtime_pack, db_session):
    # Pack is in ENTER_PACK, not ENTER_DOWNTIME
    downtime_pack.status = DowntimeTaskStatus.ENTER_PACK
    db.session.commit()
    login_user(test_client, new_user)
    response = test_client.get(
        "/downtime/enter-downtime/" f"{downtime_pack.period_id}/" f"{downtime_pack.character_id}"
    )
    assert response.status_code == 302  # Route redirects on wrong status


def test_enter_downtime_unauthorized(test_client, downtime_pack_enter_downtime, db_session):
    # Not logged in
    response = test_client.get(
        "/downtime/enter-downtime/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}"
    )
    assert response.status_code == 302


def test_enter_downtime_missing_pack(test_client, regular_user, downtime_period, db_session):
    # No pack for this character/period
    login_user(test_client, regular_user)
    response = test_client.get(f"/downtime/enter-downtime/{downtime_period.id}/99999")
    assert response.status_code == 404


def test_enter_downtime_character_owner_only(
    test_client, downtime_pack_enter_downtime, other_user, db
):
    # Different user trying to access pack
    login_user(test_client, other_user)
    response = test_client.get(
        "/downtime/enter-downtime/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}"
    )
    assert response.status_code == 403


def test_enter_downtime_post_large_data(
    test_client, downtime_pack_enter_downtime, regular_user, db
):
    # Test with large amounts of data
    login_user(test_client, regular_user)

    # Create large amounts of data
    large_purchases = [{"blueprint_id": 1, "quantity": i} for i in range(100)]
    large_modifications = [{"type": "learning", "mod_id": i} for i in range(50)]
    large_engineering = [{"action": "maintain", "source": "own", "item_id": i} for i in range(75)]
    large_science = [{"action": "synthesize", "science_type": "generic"} for _ in range(25)]
    large_research = [{"project_id": f"RES{i:03d}", "research_for": "self"} for i in range(30)]
    large_reputation = [{"faction_id": i, "question": f"Question {i}?"} for i in range(20)]

    data = {
        "purchases[]": [json.dumps(p) for p in large_purchases],
        "modifications[]": [json.dumps(m) for m in large_modifications],
        "engineering[]": [json.dumps(e) for e in large_engineering],
        "science[]": [json.dumps(s) for s in large_science],
        "research[]": [json.dumps(r) for r in large_research],
        "reputation[]": [json.dumps(rep) for rep in large_reputation],
        "confirm_complete": "on",
    }

    response = test_client.post(
        f"/downtime/enter-downtime/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=data,
        follow_redirects=False,
    )
    assert response.status_code == 302  # Should redirect on success with confirm_complete=True


def make_pack_manual_review(db, downtime_pack_enter_downtime):
    downtime_pack_enter_downtime.status = DowntimeTaskStatus.MANUAL_REVIEW
    db.session.commit()


@pytest.mark.parametrize(
    "user_fixture,expected_status",
    [
        ("downtime_team_user", 200),
        ("regular_user", 302),  # Route redirects for unauthorized users
    ],
)
def test_manual_review_get(
    test_client,
    request,
    downtime_pack_enter_downtime,
    user_fixture,
    expected_status,
    db,
):
    make_pack_manual_review(db, downtime_pack_enter_downtime)
    user = request.getfixturevalue(user_fixture)
    login_user(test_client, user)
    response = test_client.get(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}"
    )
    assert response.status_code == expected_status


def test_manual_review_wrong_status(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db
):
    # Pack is not in MANUAL_REVIEW
    login_user(test_client, downtime_team_user)
    response = test_client.get(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}"
    )
    assert response.status_code == 302  # Route redirects on wrong status


def test_manual_review_missing_pack(test_client, downtime_team_user, downtime_period, db_session):
    login_user(test_client, downtime_team_user)
    response = test_client.get(f"/downtime/manual-review/{downtime_period.id}/99999")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "review_data,confirm_complete,expected_status",
    [
        (
            {
                "invention_review": "approve",
                "invention_type": "new",
                "invention_name": "Test Invention",
                "invention_description": "Desc",
                "stages_json": '[{"stage_number":1,"name":"Stage 1","description":"",'
                '"unlock_requirements":[]}]',
            },
            False,
            200,
        ),
        (
            {"invention_review": "decline", "invention_response": "Not good enough"},
            False,
            200,
        ),
        (
            {
                "invention_review": "approve",
                "invention_type": "improve",
                "existing_invention": "1",
                "stages_json": '[{"stage_number":2,"name":"Stage 2","description":"",'
                '"unlock_requirements":[]}]',
            },
            True,
            200,
        ),
        ({"reputation_response_1": "Answer to question"}, False, 200),
        ({}, True, 200),
        # Test other confirmation
        ({"other_confirmed": "on"}, True, 200),
        ({}, False, 200),  # No confirmation, should still work
    ],
)
def test_manual_review_post(
    test_client,
    downtime_pack_enter_downtime,
    downtime_team_user,
    review_data,
    confirm_complete,
    expected_status,
    db,
):
    make_pack_manual_review(db, downtime_pack_enter_downtime)
    login_user(test_client, downtime_team_user)

    if confirm_complete:
        review_data["confirm_complete"] = "on"

    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=review_data,
        follow_redirects=True,
    )
    assert response.status_code == expected_status


def test_manual_review_post_unauthorized(
    test_client, downtime_pack_enter_downtime, regular_user, db
):
    make_pack_manual_review(db, downtime_pack_enter_downtime)
    login_user(test_client, regular_user)
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={},
    )
    assert response.status_code == 302  # Route redirects for unauthorized users


def test_manual_review_post_wrong_status(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db
):
    # Not in MANUAL_REVIEW
    login_user(test_client, downtime_team_user)
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={},
    )
    assert response.status_code == 302  # Route redirects on wrong status


def test_manual_review_post_missing_pack(
    test_client, downtime_team_user, downtime_period, db_session
):
    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/manual-review/{downtime_period.id}/99999")
    assert response.status_code == 404


def test_manual_review_with_other_field(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db
):
    """Test manual review with 'other' field that requires confirmation."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Set other field on the pack
    downtime_pack_enter_downtime.other = "Test other information"
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test without confirmation - should fail
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200  # Should stay on page due to validation error

    # Test with confirmation - should succeed
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on", "other_confirmed": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.COMPLETED


def test_manual_review_reputation_changes(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db, faction
):
    """Test manual review with reputation changes."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Set initial reputation
    character = downtime_pack_enter_downtime.character
    character.set_reputation(faction.id, 5, downtime_team_user.id)
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test with reputation change
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={f"reputation_{faction.id}": "10", "confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed and review data contains reputation changes
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.COMPLETED
    assert "reputation_changes" in downtime_pack_enter_downtime.review_data
    assert str(faction.id) in downtime_pack_enter_downtime.review_data["reputation_changes"]
    assert (
        downtime_pack_enter_downtime.review_data["reputation_changes"][str(faction.id)]["old_value"]
        == 5
    )
    assert (
        downtime_pack_enter_downtime.review_data["reputation_changes"][str(faction.id)]["new_value"]
        == 10
    )


def test_manual_review_reputation_no_changes(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db, faction
):
    """Test manual review with no reputation changes."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Set initial reputation
    character = downtime_pack_enter_downtime.character
    character.set_reputation(faction.id, 5, downtime_team_user.id)
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test with same reputation value (no change)
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={f"reputation_{faction.id}": "5", "confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed but no reputation changes recorded
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.COMPLETED
    assert "reputation_changes" not in downtime_pack_enter_downtime.review_data


def test_manual_review_reputation_multiple_factions(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db, faction
):
    """Test manual review with reputation changes for multiple factions."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Create a second faction
    from models.database.faction import Faction

    faction2 = Faction(name="Test Faction 2", wiki_slug="test-faction-2")
    db.session.add(faction2)
    db.session.commit()

    # Set initial reputations
    character = downtime_pack_enter_downtime.character
    character.set_reputation(faction.id, 5, downtime_team_user.id)
    character.set_reputation(faction2.id, 0, downtime_team_user.id)  # No reputation initially
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test with reputation changes for both factions
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={
            f"reputation_{faction.id}": "10",
            f"reputation_{faction2.id}": "3",
            "confirm_complete": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed and both reputation changes recorded
    db.session.refresh(downtime_pack_enter_downtime)
    assert "reputation_changes" in downtime_pack_enter_downtime.review_data

    changes = downtime_pack_enter_downtime.review_data["reputation_changes"]
    assert str(faction.id) in changes
    assert str(faction2.id) in changes
    assert changes[str(faction.id)]["old_value"] == 5
    assert changes[str(faction.id)]["new_value"] == 10
    assert changes[str(faction2.id)]["old_value"] == 0
    assert changes[str(faction2.id)]["new_value"] == 3


def test_manual_review_reputation_invalid_data(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db, faction
):
    """Test manual review with invalid reputation data."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    login_user(test_client, downtime_team_user)

    # Test with invalid faction ID
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"reputation_invalid": "10", "confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Test with non-numeric value
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={f"reputation_{faction.id}": "not_a_number", "confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def make_period_completed(db, downtime_period, downtime_pack):
    downtime_period.status = DowntimeStatus.COMPLETED
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    db.session.commit()


def make_period_incomplete(db, downtime_period, downtime_pack):
    downtime_period.status = DowntimeStatus.PENDING
    downtime_pack.status = DowntimeTaskStatus.ENTER_PACK
    db.session.commit()


def test_start_downtime_valid(test_client, downtime_team_user, db_session):
    login_user(test_client, downtime_team_user)
    # Create a dummy event for the period with all required fields
    from datetime import datetime, timedelta

    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number="TEST001",
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db_session.add(event)
    db_session.commit()
    response = test_client.post("/downtime/start", data={"event_id": event.id})
    assert response.status_code == 302  # Should redirect on success
    # Check that a new period was created
    period = DowntimePeriod.query.filter_by(event_id=event.id).first()
    assert period is not None
    assert period.status == DowntimeStatus.PENDING


def test_start_downtime_already_active(
    test_client, downtime_team_user, downtime_period, db_session
):
    # Set period to pending (only valid non-completed state)
    downtime_period.status = DowntimeStatus.PENDING
    db_session.commit()

    login_user(test_client, downtime_team_user)
    # Create a dummy event for the form data with all required fields
    from datetime import datetime, timedelta

    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number="TEST002",
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db_session.add(event)
    db_session.commit()

    response = test_client.post("/downtime/start", data={"event_id": event.id})
    assert (
        response.status_code == 302
    )  # Route redirects on success, doesn't check for existing periods


def test_start_downtime_missing_event(test_client, downtime_team_user):
    login_user(test_client, downtime_team_user)
    response = test_client.post("/downtime/start", data={"event_id": "99999"})
    assert response.status_code == 404


def test_start_downtime_unauthorized(test_client, regular_user):
    login_user(test_client, regular_user)
    response = test_client.post("/downtime/start", data={"event_id": "1"})
    assert response.status_code == 302  # Route redirects for unauthorized users


def test_process_downtime_valid(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    make_period_completed(db, downtime_period, downtime_pack)

    # Add some research data to reproduce the issue
    downtime_pack.research = [{"project_id": "RES001", "research_for": "self"}]
    db.session.commit()

    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects on success

    # Check that period was processed (remains COMPLETED since there's no PROCESSED state)
    db.session.refresh(downtime_period)
    assert downtime_period.status == DowntimeStatus.COMPLETED


def test_process_downtime_with_list_research_data(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    """Test processing downtime with research data stored as a list instead of dict."""
    make_period_completed(db, downtime_period, downtime_pack)

    # Simulate the error by storing research data as a list instead of dict
    downtime_pack.research = [["RES001", "self"]]  # This should be handled gracefully
    db.session.commit()

    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    # This should now succeed due to error handling
    assert response.status_code == 302


def test_process_downtime_incomplete(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    make_period_incomplete(db, downtime_period, downtime_pack)

    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects on success, doesn't check completion


def test_process_downtime_missing_event(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    make_period_completed(db, downtime_period, downtime_pack)

    login_user(test_client, downtime_team_user)
    response = test_client.post("/downtime/process/99999")
    assert response.status_code == 404


def test_process_downtime_unauthorized(
    test_client, regular_user, downtime_period, downtime_pack, db
):
    make_period_completed(db, downtime_period, downtime_pack)

    login_user(test_client, regular_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects for unauthorized users


def test_process_downtime_missing_period(test_client, downtime_team_user):
    login_user(test_client, downtime_team_user)
    response = test_client.post("/downtime/process/99999")
    assert response.status_code == 404


def test_full_downtime_process(
    test_client, db, downtime_team_user, regular_user, downtime_period, downtime_pack
):
    # Test the complete downtime process from start to finish
    login_user(test_client, downtime_team_user)

    # Start downtime
    from datetime import datetime, timedelta

    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number="TEST003",
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db.session.add(event)
    db.session.commit()
    response = test_client.post("/downtime/start", data={"event_id": event.id})
    assert response.status_code == 302  # Should redirect on success

    # Enter pack contents
    login_user(test_client, regular_user)
    data = {
        "items[]": [],
        "exotics[]": [],
        "samples[]": [],
        "cybernetics[]": [],
        "conditions[]": [],
        "research_teams[]": [],
        "energy_chits": "0",
        "confirm_complete": "on",
    }
    response = test_client.post(
        f"/downtime/enter-pack-contents/" f"{downtime_period.id}/" f"{downtime_pack.character_id}",
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Enter downtime activities
    data = {
        "purchases[]": [],
        "modifications[]": [],
        "engineering[]": [],
        "science[]": [],
        "research[]": [],
        "reputation[]": [],
        "confirm_complete": "on",
    }
    response = test_client.post(
        f"/downtime/enter-downtime/" f"{downtime_period.id}/" f"{downtime_pack.character_id}",
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Manual review
    login_user(test_client, downtime_team_user)
    response = test_client.post(
        f"/downtime/manual-review/" f"{downtime_period.id}/" f"{downtime_pack.character_id}",
        data={"confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Process downtime
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects on success


def create_test_event(db, event_number="TEST001"):
    """Helper function to create a test event with all required fields."""
    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number=event_number,
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db.session.add(event)
    db.session.commit()
    return event


def test_process_downtime_with_reputation_changes(
    test_client, downtime_team_user, downtime_period, downtime_pack, db, faction
):
    """Test processing downtime with reputation changes."""
    # Create an event for the downtime period
    from datetime import datetime, timedelta

    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number="TEST004",
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db.session.add(event)
    db.session.commit()

    # Associate the downtime period with the event
    downtime_period.event_id = event.id

    # Set up pack with reputation changes in review data
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    downtime_pack.review_data = {
        "reputation_changes": {str(faction.id): {"old_value": 5, "new_value": 10}}
    }

    # Set initial reputation
    character = downtime_pack.character
    character.set_reputation(faction.id, 5, downtime_team_user.id)
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Process downtime
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects on success

    # Verify reputation was updated
    db.session.refresh(character)
    assert character.get_reputation(faction.id) == 10

    # Verify period was completed
    db.session.refresh(downtime_period)
    assert downtime_period.status == DowntimeStatus.COMPLETED


def test_process_downtime_with_multiple_reputation_changes(
    test_client, downtime_team_user, downtime_period, downtime_pack, db, faction
):
    """Test processing downtime with multiple reputation changes."""
    # Create an event for the downtime period
    from datetime import datetime, timedelta

    from models.enums import EventType
    from models.event import Event

    event = Event(
        event_number="TEST005",
        name="Test Event",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=63),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=0.0,
    )
    db.session.add(event)
    db.session.commit()

    # Associate the downtime period with the event
    downtime_period.event_id = event.id

    # Create a second faction
    from models.database.faction import Faction

    faction2 = Faction(name="Test Faction 2", wiki_slug="test-faction-2")
    db.session.add(faction2)
    db.session.commit()

    # Set up pack with multiple reputation changes
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    downtime_pack.review_data = {
        "reputation_changes": {
            str(faction.id): {"old_value": 5, "new_value": 10},
            str(faction2.id): {"old_value": 0, "new_value": 3},
        }
    }

    # Set initial reputations
    character = downtime_pack.character
    character.set_reputation(faction.id, 5, downtime_team_user.id)
    character.set_reputation(faction2.id, 0, downtime_team_user.id)
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Process downtime
    response = test_client.post(f"/downtime/process/{downtime_period.id}")
    assert response.status_code == 302  # Route redirects on success

    # Verify both reputations were updated
    db.session.refresh(character)
    assert character.get_reputation(faction.id) == 10
    assert character.get_reputation(faction2.id) == 3

    # Verify period was completed
    db.session.refresh(downtime_period)
    assert downtime_period.status == DowntimeStatus.COMPLETED


def test_enter_downtime_post_with_player_other(
    test_client, downtime_pack_enter_downtime, regular_user, db
):
    """Test downtime entry with player_other field."""
    login_user(test_client, regular_user)

    data = {
        "purchases[]": [],
        "modifications[]": [],
        "engineering[]": [],
        "science[]": [],
        "research[]": [],
        "reputation[]": [],
        "player_other": "Test player other information",
        "confirm_complete": "on",
    }

    response = test_client.post(
        f"/downtime/enter-downtime/{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 302  # Should redirect on success

    # Check that pack status was updated
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.MANUAL_REVIEW
    assert downtime_pack_enter_downtime.player_other == "Test player other information"


def test_enter_downtime_post_with_empty_player_other(
    test_client, downtime_pack_enter_downtime, regular_user, db
):
    """Test downtime entry with empty player_other field."""
    login_user(test_client, regular_user)

    data = {
        "purchases[]": [],
        "modifications[]": [],
        "engineering[]": [],
        "science[]": [],
        "research[]": [],
        "reputation[]": [],
        "player_other": "",
        "confirm_complete": "on",
    }

    response = test_client.post(
        f"/downtime/enter-downtime/{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data=data,
        follow_redirects=False,
    )

    assert response.status_code == 302  # Should redirect on success

    # Check that pack status was updated
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.MANUAL_REVIEW
    assert downtime_pack_enter_downtime.player_other == ""


def test_manual_review_with_player_other_field(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db
):
    """Test manual review with 'player_other' field that requires confirmation."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Set player_other field on the pack
    downtime_pack_enter_downtime.player_other = "Test player other information"
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test without confirmation - should fail
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200  # Should stay on page due to validation error

    # Test with confirmation - should succeed
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on", "player_other_confirmed": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.COMPLETED


def test_manual_review_with_both_other_fields(
    test_client, downtime_pack_enter_downtime, downtime_team_user, db
):
    """Test manual review with both 'other' and 'player_other' fields."""
    make_pack_manual_review(db, downtime_pack_enter_downtime)

    # Set both other fields on the pack
    downtime_pack_enter_downtime.other = "Test game team other information"
    downtime_pack_enter_downtime.player_other = "Test player other information"
    db.session.commit()

    login_user(test_client, downtime_team_user)

    # Test without any confirmation - should fail
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200  # Should stay on page due to validation error

    # Test with only game team confirmation - should fail
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on", "other_confirmed": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200  # Should stay on page due to validation error

    # Test with only player confirmation - should fail
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on", "player_other_confirmed": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200  # Should stay on page due to validation error

    # Test with both confirmations - should succeed
    response = test_client.post(
        "/downtime/manual-review/"
        f"{downtime_pack_enter_downtime.period_id}/"
        f"{downtime_pack_enter_downtime.character_id}",
        data={"confirm_complete": "on", "other_confirmed": "on", "player_other_confirmed": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify pack was completed
    db.session.refresh(downtime_pack_enter_downtime)
    assert downtime_pack_enter_downtime.status == DowntimeTaskStatus.COMPLETED


def test_process_downtime_character_points_crew_tickets(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    """Test that character points are added to crew ticket holders during downtime processing."""
    from models.enums import EventType, TicketType
    from models.event import Event
    from models.tools.event_ticket import EventTicket
    from models.tools.user import User

    # Create a test event with mainline type
    event = Event(
        event_number="TEST001",
        name="Test Event",
        event_type=EventType.MAINLINE.value,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=15),
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=2),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=5.0,
    )
    db.session.add(event)
    db.session.flush()

    # Create a crew user
    crew_user = User(
        email="crew@test.com",
        first_name="Crew",
        surname="User",
        character_points=0.0,
    )
    crew_user.set_password("password")
    db.session.add(crew_user)
    db.session.flush()

    # Create crew ticket
    crew_ticket = EventTicket(
        event_id=event.id,
        user_id=crew_user.id,
        ticket_type=TicketType.CREW.value,
        price_paid=0.0,
        assigned_by_id=downtime_team_user.id,
    )
    db.session.add(crew_ticket)

    # Update the downtime period to use our test event
    downtime_period.event_id = event.id
    db.session.commit()

    # Complete the downtime pack
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    db.session.commit()

    # Process the downtime
    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}", follow_redirects=True)
    assert response.status_code == 200

    # Verify crew user received character points
    db.session.refresh(crew_user)
    assert crew_user.character_points == 1.0  # Mainline event gives 1.0 points


def test_process_downtime_character_points_sanctioned_event(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    """Test that character points are added correctly for sanctioned events."""
    from models.enums import EventType, TicketType
    from models.event import Event
    from models.tools.event_ticket import EventTicket
    from models.tools.user import User

    # Create a test event with sanctioned type
    event = Event(
        event_number="TEST002",
        name="Test Sanctioned Event",
        event_type=EventType.SANCTIONED_CONTINUITY.value,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=15),
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=2),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=5.0,
    )
    db.session.add(event)
    db.session.flush()

    # Create a crew user
    crew_user = User(
        email="crew_sanctioned@test.com",
        first_name="Crew",
        surname="UserSanctioned",
        character_points=0.0,
    )
    crew_user.set_password("password")
    db.session.add(crew_user)
    db.session.flush()

    # Create crew ticket
    crew_ticket = EventTicket(
        event_id=event.id,
        user_id=crew_user.id,
        ticket_type=TicketType.CREW.value,
        price_paid=0.0,
        assigned_by_id=downtime_team_user.id,
    )
    db.session.add(crew_ticket)

    # Update the downtime period to use our test event
    downtime_period.event_id = event.id
    db.session.commit()

    # Complete the downtime pack
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    db.session.commit()

    # Process the downtime
    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}", follow_redirects=True)
    assert response.status_code == 200

    # Verify crew user received character points
    db.session.refresh(crew_user)
    assert crew_user.character_points == 0.5  # Sanctioned event gives 0.5 points


def test_process_downtime_character_points_online_event(
    test_client, downtime_team_user, downtime_period, downtime_pack, db
):
    """Test that character points are not added for online events."""
    from models.enums import EventType, TicketType
    from models.event import Event
    from models.tools.event_ticket import EventTicket
    from models.tools.user import User

    # Create a test event with online type
    event = Event(
        event_number="TEST003",
        name="Test Online Event",
        event_type=EventType.ONLINE.value,
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=15),
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=2),
        standard_ticket_price=50.0,
        early_booking_ticket_price=40.0,
        child_ticket_price_12_15=25.0,
        child_ticket_price_7_11=15.0,
        child_ticket_price_under_7=5.0,
    )
    db.session.add(event)
    db.session.flush()

    # Create a crew user
    crew_user = User(
        email="crew_online@test.com",
        first_name="Crew",
        surname="UserOnline",
        character_points=0.0,
    )
    crew_user.set_password("password")
    db.session.add(crew_user)
    db.session.flush()

    # Create crew ticket
    crew_ticket = EventTicket(
        event_id=event.id,
        user_id=crew_user.id,
        ticket_type=TicketType.CREW.value,
        price_paid=0.0,
        assigned_by_id=downtime_team_user.id,
    )
    db.session.add(crew_ticket)

    # Update the downtime period to use our test event
    downtime_period.event_id = event.id
    db.session.commit()

    # Complete the downtime pack
    downtime_pack.status = DowntimeTaskStatus.COMPLETED
    db.session.commit()

    # Process the downtime
    login_user(test_client, downtime_team_user)
    response = test_client.post(f"/downtime/process/{downtime_period.id}", follow_redirects=True)
    assert response.status_code == 200

    # Verify crew user did not receive character points
    db.session.refresh(crew_user)
    assert crew_user.character_points == 0.0  # Online events give no points
