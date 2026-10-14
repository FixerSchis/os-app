import uuid

from werkzeug.datastructures import MultiDict

from models.database.cybernetic import Cybernetic
from models.enums import ScienceType


def test_cybernetics_list_unauthorized(test_client):
    response = test_client.get("/db/cybernetics/")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_cybernetics_list_authorized(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/cybernetics/")
    assert response.status_code == 200
    assert b"Implants" in response.data


def test_cybernetics_create_get_authorized(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get("/db/cybernetics/new")
    assert response.status_code == 200
    assert b"Create Implant" in response.data


def test_cybernetics_create_post_authorized(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    unique_name = f"Cybernetic {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", unique_name),
            ("neural_shock_value", "7"),
            ("wiki_slug", f"cybernetic-{uuid.uuid4()}"),
            ("adds_engineering_mods", "1"),
            ("adds_engineering_downtime", "2"),
            ("adds_science_downtime", "3"),
            ("science_type", ScienceType.GENERIC.value),
            ("implant_type", "Bioware"),
            ("slot", "Skin"),
        ]
    )
    response = test_client.post(
        "/db/cybernetics/new",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Implant created" in response.data
    cyber = Cybernetic.query.filter_by(name=unique_name).first()
    assert cyber is not None
    assert cyber.neural_shock_value == 7
    assert cyber.implant_type == "Bioware"
    assert cyber.slot == "Skin"


def test_cybernetics_edit_get_authorized(test_client, rules_team_user, cybernetic):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.get(f"/db/cybernetics/{cybernetic.id}/edit")
    assert response.status_code == 200
    assert bytes(cybernetic.name, "utf-8") in response.data


def test_cybernetics_edit_post_authorized(test_client, rules_team_user, cybernetic, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    new_name = f"Updated Cybernetic {uuid.uuid4()}"
    post_data = MultiDict(
        [
            ("name", new_name),
            ("neural_shock_value", "9"),
            ("wiki_slug", f"cybernetic-{uuid.uuid4()}"),
            ("adds_engineering_mods", "2"),
            ("adds_engineering_downtime", "3"),
            ("adds_science_downtime", "4"),
            ("science_type", ScienceType.GENERIC.value),
            ("implant_type", "Cybernetic"),
            ("slot", "Spine"),
        ]
    )
    response = test_client.post(
        f"/db/cybernetics/{cybernetic.id}/edit",
        data=post_data,
        follow_redirects=True,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Implant updated" in response.data
    db.session.expire_all()
    updated = db.session.get(Cybernetic, cybernetic.id)
    assert updated.name == new_name
    assert updated.neural_shock_value == 9
    assert updated.implant_type == "Cybernetic"
    assert updated.slot == "Spine"


def test_implant_create_requires_type_and_slot(test_client, rules_team_user, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(
        "/db/cybernetics/new",
        data={
            "name": f"Bare Implant {uuid.uuid4()}",
            "neural_shock_value": "1",
            "wiki_slug": f"bare-implant-{uuid.uuid4()}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Type and slot are required." in response.data
    assert Cybernetic.query.filter(Cybernetic.name.like("Bare Implant %")).first() is None


def test_implant_type_reuses_existing_spelling(test_client, rules_team_user, db):
    existing = Cybernetic(
        name=f"Existing Bioware {uuid.uuid4()}",
        neural_shock_value=1,
        wiki_slug=f"existing-bioware-{uuid.uuid4()}",
        implant_type="Bioware",
        slot="Hands",
    )
    db.session.add(existing)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    unique_name = f"Matched Type {uuid.uuid4()}"
    response = test_client.post(
        "/db/cybernetics/new",
        data={
            "name": unique_name,
            "neural_shock_value": "2",
            "wiki_slug": f"matched-type-{uuid.uuid4()}",
            "implant_type": " bioware ",
            "slot": "spine",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    created = Cybernetic.query.filter_by(name=unique_name).first()
    assert created.implant_type == "Bioware"
    assert created.slot == "spine"


def test_slot_conflict_message_matches_ignoring_case():
    from models.database.cybernetic import slot_conflict_message

    first = Cybernetic(name="Cortex Weave", slot="Brain")
    second = Cybernetic(name="Neural Lace", slot=" brain ")
    other = Cybernetic(name="Dermal Plate", slot="Skin")
    blank = Cybernetic(name="Unplaced", slot="")

    assert slot_conflict_message([first, other, blank]) is None
    message = slot_conflict_message([first, second])
    assert "Neural Lace" in message
    assert "Cortex Weave" in message


def test_implant_slot_change_is_rejected_when_a_character_already_uses_it(
    test_client, rules_team_user, db, new_user, character
):
    from models.database.cybernetic import CharacterCybernetic

    brain = Cybernetic(
        name=f"Cortex Weave {uuid.uuid4()}",
        neural_shock_value=1,
        wiki_slug=f"cortex-{uuid.uuid4()}",
        implant_type="Bioware",
        slot="Brain",
    )
    hands = Cybernetic(
        name=f"Grip {uuid.uuid4()}",
        neural_shock_value=1,
        wiki_slug=f"grip-{uuid.uuid4()}",
        implant_type="Cybernetic",
        slot="Hands",
    )
    db.session.add_all([brain, hands])
    db.session.flush()
    db.session.add_all(
        [
            CharacterCybernetic(character_id=character.id, cybernetic_id=brain.id),
            CharacterCybernetic(character_id=character.id, cybernetic_id=hands.id),
        ]
    )
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(
        f"/db/cybernetics/{hands.id}/edit",
        data={
            "name": hands.name,
            "neural_shock_value": "1",
            "wiki_slug": hands.wiki_slug,
            "implant_type": "Cybernetic",
            "slot": "Brain",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already has" in response.data
    db.session.expire_all()
    updated = db.session.get(Cybernetic, hands.id)
    assert updated.slot == "Hands"


def test_downtime_confirm_rejects_an_occupied_implant_slot(
    test_client, db, new_user, character, downtime_period
):
    from models.database.cybernetic import CharacterCybernetic
    from models.enums import DowntimeTaskStatus
    from models.tools.downtime import DowntimePack

    installed = Cybernetic(
        name=f"Cortex Weave {uuid.uuid4()}",
        neural_shock_value=1,
        wiki_slug=f"installed-brain-{uuid.uuid4()}",
        implant_type="Bioware",
        slot="Brain",
    )
    incoming = Cybernetic(
        name=f"Neural Lace {uuid.uuid4()}",
        neural_shock_value=1,
        wiki_slug=f"incoming-brain-{uuid.uuid4()}",
        implant_type="Cybernetic",
        slot="Brain",
    )
    db.session.add_all([installed, incoming])
    db.session.flush()
    db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=installed.id))
    pack = DowntimePack(
        character_id=character.id,
        period_id=downtime_period.id,
        status=DowntimeTaskStatus.ENTER_PACK,
        cybernetics=[],
    )
    db.session.add(pack)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = new_user.id
        session["_fresh"] = True

    response = test_client.post(
        f"/downtime/enter-pack-contents/{downtime_period.id}/{character.id}",
        data={"cybernetics[]": [str(incoming.id)], "confirm_complete": "1", "credits": "0"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already installed" in response.data
    db.session.expire_all()
    saved_pack = db.session.get(DowntimePack, pack.id)
    assert saved_pack.status == DowntimeTaskStatus.ENTER_PACK
    installed_ids = {
        link.cybernetic_id
        for link in CharacterCybernetic.query.filter_by(character_id=character.id).all()
    }
    assert installed_ids == {installed.id}


def test_cybernetics_delete_authorized(test_client, rules_team_user, cybernetic, db):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True

    response = test_client.post(f"/db/cybernetics/{cybernetic.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    db.session.expire_all()
    deleted = db.session.get(Cybernetic, cybernetic.id)
    assert deleted is None
