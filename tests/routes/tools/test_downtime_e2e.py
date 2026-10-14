"""One downtime period for a cast of characters who share skills, gear, and research.

The run goes through the real downtime routes: start, pack contents, activities,
manual review, and process. It checks the results those characters should come
away with, including item cards that still need printing before the next event.
"""

import json
import uuid
from datetime import datetime, timedelta

from models.database.conditions import Condition, ConditionStage
from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.group_type import GroupType
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.database.sample import Sample, SampleTag
from models.database.skills import Skill
from models.database.species import Species
from models.enums import (
    CharacterStatus,
    DowntimeStatus,
    DowntimeTaskStatus,
    EventType,
    ResearchRequirementType,
    ScienceType,
    TicketType,
)
from models.event import Event
from models.extensions import db
from models.tools.character import Character, CharacterSkill
from models.tools.character_inventory import CharacterItem
from models.tools.downtime import DowntimePack, DowntimePeriod
from models.tools.event_ticket import EventTicket
from models.tools.group import Group
from models.tools.research import (
    CharacterResearch,
    CharacterResearchStage,
    Research,
    ResearchStage,
    ResearchStageRequirement,
)
from models.tools.user import User
from routes.tools.downtime import (
    get_available_engineering_slots_with_sources,
    get_available_science_slots_with_sources,
)


def login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = user.id
        sess["_fresh"] = True


def make_user(name):
    token = uuid.uuid4().hex
    user = User(
        email=f"{name}.{token}@example.com",
        first_name=name,
        surname="Player",
        email_verified=True,
        notify_downtime_pack_enter=False,
        notify_downtime_completed=False,
    )
    user.set_password("password")
    db.session.add(user)
    db.session.flush()
    return user


def make_character(user, name, species, faction, group=None, bank=0):
    character = Character(
        user_id=user.id,
        character_id=1,
        name=name,
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
        group_id=group.id if group else None,
        bank_account=bank,
    )
    db.session.add(character)
    db.session.flush()
    return character


def give_skill(character, buyer, times_purchased=1, **skill_fields):
    skill = Skill(base_cost=1, skill_type="GENERAL", **skill_fields)
    db.session.add(skill)
    db.session.flush()
    db.session.add(
        CharacterSkill(
            character_id=character.id,
            skill_id=skill.id,
            times_purchased=times_purchased,
            purchased_by_user_id=buyer.id,
        )
    )
    db.session.flush()
    return skill


def make_item(blueprint, owner, editor, printed=True, expiry=40, item_number=1):
    item = Item(
        blueprint_id=blueprint.id,
        item_id=item_number,
        expiry=expiry,
        printed=printed,
    )
    db.session.add(item)
    db.session.flush()
    db.session.add(
        CharacterItem(
            character_id=owner.id,
            item_id=item.id,
            assigned_by_user_id=editor.id,
        )
    )
    db.session.flush()
    return item


def add_stage(research, number, name, requirements):
    stage = ResearchStage(
        research_id=research.id,
        stage_number=number,
        name=name,
        description=name,
    )
    db.session.add(stage)
    db.session.flush()
    for requirement in requirements:
        db.session.add(ResearchStageRequirement(stage_id=stage.id, **requirement))
    db.session.flush()
    return stage


def finish_current_stage(character_research):
    stage = character_research.get_current_stage()
    for requirement in stage.requirement_progress:
        requirement.progress = requirement.requirement.amount
    stage.stage_completed = True
    character_research.advance_stage()


def post_pack(client, period, character, **fields):
    data = {
        "credits": str(fields.get("credits", 0)),
        "other": fields.get("other", ""),
        "confirm_complete": "on",
    }
    for key in (
        "item_ids",
        "exotic_ids",
        "samples",
        "cybernetics",
        "condition_ids",
        "research_teams",
    ):
        values = fields.get(key) or []
        if values:
            data[f"{key}[]"] = [str(value) for value in values]
    for exotic_id, amount in (fields.get("exotic_amounts") or {}).items():
        data[f"exotic_amount_{exotic_id}"] = str(amount)
    for condition_id, duration in (fields.get("condition_durations") or {}).items():
        data[f"condition_duration_{condition_id}"] = str(duration)
    return client.post(
        f"/downtime/enter-pack-contents/{period.id}/{character.id}",
        data=data,
        follow_redirects=True,
    )


def post_activities(client, period, character, **fields):
    data = {"player_other": fields.get("player_other", ""), "confirm_complete": "on"}
    for key in (
        "purchases",
        "modifications",
        "engineering",
        "science",
        "research",
        "reputation",
    ):
        entries = fields.get(key) or []
        if entries:
            data[f"{key}[]"] = [json.dumps(entry) for entry in entries]
    return client.post(
        f"/downtime/enter-downtime/{period.id}/{character.id}",
        data=data,
        follow_redirects=True,
    )


def post_review(client, period, character, **fields):
    data = dict(fields)
    data["confirm_complete"] = "on"
    return client.post(
        f"/downtime/manual-review/{period.id}/{character.id}",
        data=data,
        follow_redirects=True,
    )


def messages(character):
    raw = character.character_pack or {}
    return raw.get("messages") or []


def downtime_text(character, pack):
    return "\n".join(character.pack.downtime_results.get(str(pack.id), []))


def test_downtime_period_applies_every_character_interaction(test_client, downtime_team_user):
    token = uuid.uuid4().hex[:8]
    concord = Faction(
        name=f"Concord {token}",
        wiki_slug=f"concord-{token}",
        allow_player_characters=True,
    )
    meridian = Faction(
        name=f"Meridian {token}",
        wiki_slug=f"meridian-{token}",
        allow_player_characters=True,
    )
    db.session.add_all([concord, meridian])
    db.session.flush()

    species = Species(
        name=f"Human {token}",
        wiki_page=f"human-{token}",
        permitted_factions=f"[{concord.id}]",
        body_hits_type="locational",
        body_hits=5,
        death_count=3,
    )
    group_type = GroupType(
        name=f"Cell {token}",
        description="A field cell",
        income_items_discount=0.5,
        income_distribution_dict={"items": 50, "chits": 50},
    )
    device_type = ItemType(name=f"Device {token}", id_prefix="DV")
    component_type = ItemType(name=f"Component {token}", id_prefix="CP")
    db.session.add_all([species, group_type, device_type, component_type])
    db.session.flush()

    field_team = Group(
        name=f"Field Team {token}",
        group_type_id=group_type.id,
        faction_id=concord.id,
        bank_account=100,
    )
    db.session.add(field_team)
    db.session.flush()

    rig_blueprint = ItemBlueprint(
        name=f"Field Rig {token}",
        item_type_id=device_type.id,
        blueprint_id=1,
        base_cost=20,
    )
    device_blueprint = ItemBlueprint(
        name=f"Hand Scanner {token}",
        item_type_id=device_type.id,
        blueprint_id=2,
        base_cost=10,
    )
    component_blueprint = ItemBlueprint(
        name=f"Coil {token}",
        item_type_id=component_type.id,
        blueprint_id=1,
        base_cost=5,
    )
    expensive_blueprint = ItemBlueprint(
        name=f"Orbital Array {token}",
        item_type_id=device_type.id,
        blueprint_id=3,
        base_cost=10000,
    )
    db.session.add_all([rig_blueprint, device_blueprint, component_blueprint, expensive_blueprint])
    db.session.flush()

    vita = ExoticSubstance(
        name=f"Vita Gel {token}",
        type=ScienceType.LIFE,
        wiki_slug=f"vita-{token}",
    )
    reagent = ExoticSubstance(
        name=f"Reagent {token}",
        type=ScienceType.GENERIC,
        wiki_slug=f"reagent-{token}",
    )
    spore_tag = SampleTag(name=f"spore-{token}")
    db.session.add_all([vita, reagent, spore_tag])
    db.session.flush()

    fever = Condition(name=f"Low Fever {token}", progresses_naturally=True)
    burnout = Condition(name=f"Burnout {token}", progresses_naturally=True)
    db.session.add_all([fever, burnout])
    db.session.flush()
    db.session.add_all(
        [
            ConditionStage(
                condition_id=fever.id,
                stage_number=1,
                rp_effect="Tired",
                diagnosis="A low fever",
                cure="Rest",
                duration=2,
            ),
            ConditionStage(
                condition_id=burnout.id,
                stage_number=1,
                rp_effect="Exhausted",
                diagnosis="Burnout",
                cure="Time off",
                duration=1,
            ),
        ]
    )

    tool_arm = Cybernetic(
        name=f"Tool Arm {token}",
        neural_shock_value=1,
        wiki_slug=f"tool-arm-{token}",
        adds_engineering_downtime=1,
    )
    analyzer = Cybernetic(
        name=f"Analyzer {token}",
        neural_shock_value=1,
        wiki_slug=f"analyzer-{token}",
        adds_science_downtime=1,
        science_type=ScienceType.GENERIC,
    )
    plating = Mod(name=f"Plating {token}", wiki_slug=f"plating-{token}")
    scope = Mod(name=f"Scope {token}", wiki_slug=f"scope-{token}")
    calibration = Mod(name=f"Calibration {token}", wiki_slug=f"calibration-{token}")
    db.session.add_all([tool_arm, analyzer, plating, scope, calibration])
    db.session.flush()

    iona_user = make_user("iona")
    sera_user = make_user("sera")
    nia_user = make_user("nia")
    pax_user = make_user("pax")
    theo_user = make_user("theo")
    wynn_user = make_user("wynn")
    pip_user = make_user("pip")
    crew_user = make_user("crew")
    lark_user = make_user("lark")

    iona = make_character(iona_user, "Iona", species, concord, field_team, bank=8)
    sera = make_character(sera_user, "Sera", species, concord, field_team)
    nia = make_character(nia_user, "Nia", species, concord, field_team)
    pax = make_character(pax_user, "Pax", species, concord, field_team)
    theo = make_character(theo_user, "Theo", species, concord)
    wynn = make_character(wynn_user, "Wynn", species, meridian)
    pip = make_character(pip_user, "Pip", species, concord)
    lark = make_character(lark_user, "Lark", species, concord)

    field_engineering = give_skill(
        iona,
        downtime_team_user,
        name=f"Field Engineering {token}",
        adds_engineering_downtime=1,
    )
    give_skill(
        iona,
        downtime_team_user,
        name=f"Workshop Practice {token}",
        adds_engineering_downtime=1,
    )
    give_skill(
        iona,
        downtime_team_user,
        name=f"Mod Training {token}",
        adds_engineering_mods=1,
    )
    scope.required_skills_list = [field_engineering.id]
    iona.known_modifications = [plating.id]

    give_skill(
        sera,
        downtime_team_user,
        name=f"Life Analysis {token}",
        adds_science_downtime=1,
        science_type=ScienceType.LIFE,
    )
    give_skill(
        theo,
        downtime_team_user,
        name=f"Instruction {token}",
        adds_science_downtime=1,
        times_purchased=2,
    )
    give_skill(
        wynn,
        downtime_team_user,
        name=f"Bench Science {token}",
        adds_science_downtime=1,
        times_purchased=2,
    )

    iona_device = make_item(device_blueprint, iona, downtime_team_user)
    shared_device = make_item(device_blueprint, pax, downtime_team_user, expiry=41, item_number=2)
    component = make_item(component_blueprint, pax, downtime_team_user)
    maintain_cost = iona_device.get_maintenance_cost()
    new_mod_cost = rig_blueprint.get_modification_cost(0)
    group_mod_cost = shared_device.get_modification_cost()

    contested = Sample(name=f"Contested culture {token}", type=ScienceType.GENERIC)
    spore = Sample(name=f"Spore {token}", type=ScienceType.LIFE, tags=[spore_tag])
    culture = Sample(name=f"Bench culture {token}", type=ScienceType.GENERIC)
    db.session.add_all([contested, spore, culture])
    db.session.flush()
    lark.samples.append(contested)
    nia.samples.append(spore)
    wynn.samples.append(culture)

    stabiliser = Research(project_name=f"Stabiliser {token}", type="artefact")
    lesson = Research(project_name=f"Field Method {token}", type="invention")
    lens = Research(project_name=f"Field Lens {token}", type="invention")
    db.session.add_all([stabiliser, lesson, lens])
    db.session.flush()

    add_stage(
        stabiliser,
        1,
        "Prototype",
        [
            {
                "requirement_type": ResearchRequirementType.SCIENCE,
                "science_type": ScienceType.LIFE,
                "amount": 1,
            },
            {
                "requirement_type": ResearchRequirementType.EXOTIC,
                "exotic_substance_id": reagent.id,
                "amount": 1,
            },
            {
                "requirement_type": ResearchRequirementType.ITEM,
                "item_type": str(component_type.id),
                "amount": 1,
            },
            {
                "requirement_type": ResearchRequirementType.SAMPLE,
                "sample_tag": spore_tag.name,
                "amount": 1,
            },
        ],
    )
    add_stage(
        stabiliser,
        2,
        "Field trial",
        [
            {
                "requirement_type": ResearchRequirementType.SCIENCE,
                "science_type": ScienceType.GENERIC,
                "amount": 1,
            }
        ],
    )
    lesson_stage = add_stage(
        lesson,
        1,
        "Lesson",
        [
            {
                "requirement_type": ResearchRequirementType.SCIENCE,
                "science_type": ScienceType.GENERIC,
                "amount": 1,
            }
        ],
    )
    add_stage(
        lesson,
        2,
        "Practice",
        [
            {
                "requirement_type": ResearchRequirementType.SCIENCE,
                "science_type": ScienceType.GENERIC,
                "amount": 3,
            }
        ],
    )
    add_stage(
        lens,
        1,
        "Lab lens",
        [
            {
                "requirement_type": ResearchRequirementType.SCIENCE,
                "science_type": ScienceType.GENERIC,
                "amount": 1,
            }
        ],
    )
    stabiliser.assign_character(nia.id)
    lesson.assign_character(theo.id)
    finish_current_stage(CharacterResearch.query.filter_by(character_id=theo.id).one())
    lesson.assign_character(wynn.id)
    lens.assign_character(theo.id)
    finish_current_stage(
        CharacterResearch.query.filter_by(character_id=theo.id, research_id=lens.id).one()
    )

    event = Event(
        event_number="42",
        name=f"Downtime Event {token}",
        event_type=EventType.MAINLINE,
        early_booking_deadline=datetime.now() + timedelta(days=1),
        booking_deadline=datetime.now() + timedelta(days=2),
        start_date=datetime.now() + timedelta(days=10),
        end_date=datetime.now() + timedelta(days=12),
        standard_ticket_price=50,
        early_booking_ticket_price=40,
        child_ticket_price_12_15=25,
        child_ticket_price_7_11=15,
        child_ticket_price_under_7=0,
    )
    db.session.add(event)
    db.session.flush()

    def ticket(user, character, ticket_type):
        db.session.add(
            EventTicket(
                event_id=event.id,
                user_id=user.id,
                character_id=character.id if character else None,
                ticket_type=ticket_type,
                price_paid=0,
                assigned_by_id=downtime_team_user.id,
            )
        )

    for user, character in (
        (iona_user, iona),
        (sera_user, sera),
        (nia_user, nia),
        (pax_user, pax),
        (theo_user, theo),
        (wynn_user, wynn),
    ):
        ticket(user, character, TicketType.ADULT)
    ticket(pip_user, pip, TicketType.CHILD_12_15)
    ticket(crew_user, None, TicketType.CREW)
    db.session.commit()

    login(test_client, downtime_team_user)
    started = test_client.post("/downtime/start", data={"event_id": event.id})
    assert started.status_code == 302
    period = DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).one()
    packs = {pack.character_id: pack for pack in period.packs}
    assert set(packs) == {iona.id, sera.id, nia.id, pax.id, theo.id, wynn.id, pip.id}

    assert (
        post_pack(
            test_client,
            period,
            iona,
            cybernetics=[tool_arm.id],
        ).status_code
        == 200
    )
    assert (
        post_pack(
            test_client,
            period,
            sera,
            samples=[contested.id],
            cybernetics=[analyzer.id],
            condition_ids=[fever.id],
            condition_durations={fever.id: 2},
            research_teams=[concord.id],
            credits=40,
            other="Return the sealed case to Concord.",
        ).status_code
        == 200
    )
    assert post_pack(test_client, period, nia, samples=[spore.id]).status_code == 200
    assert (
        post_pack(
            test_client,
            period,
            pax,
            item_ids=[shared_device.id, component.id],
            exotic_ids=[reagent.id],
            exotic_amounts={reagent.id: 1},
        ).status_code
        == 200
    )
    assert post_pack(test_client, period, theo).status_code == 200
    assert (
        post_pack(
            test_client,
            period,
            wynn,
            condition_ids=[burnout.id],
            condition_durations={burnout.id: 1},
        ).status_code
        == 200
    )
    assert post_pack(test_client, period, pip).status_code == 200

    db.session.refresh(iona)
    db.session.refresh(sera)
    db.session.refresh(lark)
    assert {link.cybernetic_id for link in iona.cybernetics_link} == {tool_arm.id}
    assert {link.cybernetic_id for link in sera.cybernetics_link} == {analyzer.id}
    assert len(get_available_engineering_slots_with_sources(iona)) == 3
    assert iona.get_available_engineering_mod_slots() == 1
    science_slots = get_available_science_slots_with_sources(sera)
    assert len(science_slots) == 3
    assert sera.get_available_science_slots() == 2
    assert any(slot["source"].startswith("Research Team:") for slot in science_slots)
    assert contested not in list(lark.samples)
    assert contested in list(sera.samples)
    assert sera.bank_account == 40

    assert (
        post_activities(
            test_client,
            period,
            iona,
            purchases=[
                {
                    "blueprint_id": rig_blueprint.id,
                    "name": rig_blueprint.name,
                    "cost": rig_blueprint.base_cost,
                }
            ],
            modifications=[
                {"mod_id": plating.id, "type": "forgetting"},
                {"mod_id": scope.id, "type": "learning"},
            ],
            engineering=[
                {"action": "maintain", "source": "own", "item_id": iona_device.id},
                {
                    "action": "modify",
                    "source": "own",
                    "blueprint_id": rig_blueprint.id,
                    "mod_id": scope.id,
                },
                {
                    "action": "modify",
                    "source": "group",
                    "item_id": shared_device.id,
                    "mod_id": scope.id,
                },
            ],
        ).status_code
        == 200
    )
    assert (
        post_activities(
            test_client,
            period,
            sera,
            science=[
                {
                    "action": "research_project",
                    "science_type": "life",
                    "project_id": stabiliser.public_id,
                    "research_for": "group",
                    "research_for_id": str(nia.id),
                },
                {"action": "synthesize", "science_type": "life"},
                {
                    "action": "theorise",
                    "science_type": "generic",
                    "theorise_name": "Field catalyst",
                    "theorise_desc": "A portable catalyst.",
                },
            ],
            reputation=[
                {
                    "faction_id": concord.id,
                    "question": "Will Concord sponsor the catalyst?",
                }
            ],
            player_other="Please mention the sealed case in the brief.",
        ).status_code
        == 200
    )
    assert (
        post_activities(
            test_client,
            period,
            nia,
            research=[
                {
                    "project_id": stabiliser.public_id,
                    "support_target": "self",
                    "contributed_samples": [spore.id],
                }
            ],
        ).status_code
        == 200
    )
    assert (
        post_activities(
            test_client,
            period,
            pax,
            purchases=[
                {
                    "blueprint_id": expensive_blueprint.id,
                    "name": expensive_blueprint.name,
                    "cost": expensive_blueprint.base_cost,
                }
            ],
            modifications=[{"mod_id": calibration.id, "type": "learning"}],
            research=[
                {
                    "project_id": stabiliser.public_id,
                    "support_target": "other",
                    "support_target_id": f"{nia.user_id}.{nia.character_id}",
                    "contributed_exotics": [{"id": reagent.id, "quantity": 1}],
                    "contributed_items": [component.id],
                }
            ],
        ).status_code
        == 200
    )
    assert (
        post_activities(
            test_client,
            period,
            theo,
            science=[
                {
                    "action": "teach_invention",
                    "science_type": "generic",
                    "project_id": lesson.public_id,
                    "teach_to": "other",
                    "teach_to_id": f"{wynn.user_id}.{wynn.character_id}",
                },
                {
                    "action": "theorise",
                    "science_type": "generic",
                    "theorise_name": "Lens focus",
                    "theorise_desc": "Sharper focus.",
                },
            ],
        ).status_code
        == 200
    )
    assert (
        post_activities(
            test_client,
            period,
            wynn,
            science=[
                {
                    "action": "research_sample",
                    "science_type": "generic",
                    "sample_id": culture.id,
                },
                {
                    "action": "theorise",
                    "science_type": "generic",
                    "theorise_name": "Perpetual engine",
                    "theorise_desc": "It runs forever.",
                },
            ],
            reputation=[{"faction_id": meridian.id, "question": "Does Meridian want the engine?"}],
        ).status_code
        == 200
    )
    assert post_activities(test_client, period, pip).status_code == 200

    catalyst_stages = json.dumps(
        [
            {
                "stage_number": 1,
                "name": "Bench test",
                "description": "Prove the principle.",
                "unlock_requirements": [
                    {
                        "requirement_type": "science",
                        "science_type": "generic",
                        "amount": 1,
                    }
                ],
            }
        ]
    )
    lens_stages = json.dumps(
        [
            {
                "stage_number": 1,
                "name": "Field focus",
                "description": "Focus it outside the lab.",
                "unlock_requirements": [
                    {
                        "requirement_type": "science",
                        "science_type": "generic",
                        "amount": 2,
                    }
                ],
            }
        ]
    )
    assert post_review(test_client, period, iona).status_code == 200
    assert (
        post_review(
            test_client,
            period,
            sera,
            invention_review="approve",
            invention_type="new",
            invention_name="Field catalyst",
            invention_description="A portable catalyst.",
            stages_json=catalyst_stages,
            **{
                f"reputation_{concord.id}": "4",
                f"reputation_response_{concord.id}": "Concord will sponsor one trial.",
                "other_confirmed": "on",
                "player_other_confirmed": "on",
            },
        ).status_code
        == 200
    )
    assert post_review(test_client, period, nia).status_code == 200
    assert post_review(test_client, period, pax).status_code == 200
    assert (
        post_review(
            test_client,
            period,
            theo,
            invention_review="approve",
            invention_type="improve",
            existing_invention=str(lens.id),
            stages_json=lens_stages,
        ).status_code
        == 200
    )
    assert (
        post_review(
            test_client,
            period,
            wynn,
            invention_review="decline",
            invention_response="That breaks thermodynamics.",
            **{
                f"reputation_{meridian.id}": "-1",
                f"reputation_response_{meridian.id}": "Meridian is not impressed.",
            },
        ).status_code
        == 200
    )
    assert post_review(test_client, period, pip).status_code == 200
    assert all(
        pack.status == DowntimeTaskStatus.COMPLETED
        for pack in DowntimePack.query.filter_by(period_id=period.id)
    )

    processed = test_client.post(f"/downtime/process/{period.id}", follow_redirects=True)
    assert processed.status_code == 200
    db.session.refresh(period)
    assert period.status == DowntimeStatus.COMPLETED

    for character in (iona, sera, nia, pax, theo, wynn, pip):
        db.session.refresh(character)
    db.session.refresh(field_team)
    db.session.refresh(culture)
    db.session.refresh(iona_device)
    db.session.refresh(shared_device)

    iona_pack = packs[iona.id]
    sera_pack = packs[sera.id]
    nia_pack = packs[nia.id]
    pax_pack = packs[pax.id]
    theo_pack = packs[theo.id]
    wynn_pack = packs[wynn.id]

    assert iona.known_modifications == [scope.id]
    assert iona.bank_account == 0
    assert field_team.bank_account == 100 - (20 - 8) - maintain_cost - new_mod_cost - group_mod_cost
    rig = Item.query.filter_by(blueprint_id=rig_blueprint.id).one()
    assert rig.expiry == 46
    assert rig.printed is False
    assert rig.version == 2
    assert scope in rig.mods_applied
    assert CharacterItem.query.filter_by(character_id=iona.id, item_id=rig.id).one()
    assert iona_device.expiry == 46
    assert iona_device.printed is False
    assert iona_device.version == 2
    assert shared_device.printed is False
    assert shared_device.version == 2
    assert scope in shared_device.mods_applied
    assert {item.id for item in Item.query.filter_by(printed=False)} == {
        rig.id,
        shared_device.id,
        iona_device.id,
    }
    iona_text = downtime_text(iona, iona_pack)
    assert f"Purchased: {rig_blueprint.display_name}" in iona_text
    assert f"Maintained {iona_device.name}" in iona_text
    assert f"Applied {scope.name} to {rig.name}" in iona_text
    assert f"Applied {scope.name} to {shared_device.name}" in iona_text
    assert "Forgot modification" in iona_text
    assert f"Learned mod: {scope.name}" in iona_text

    assert "insufficient funds" in downtime_text(pax, pax_pack)
    assert Item.query.filter_by(blueprint_id=expensive_blueprint.id).count() == 0
    assert "no free mod slots" in downtime_text(pax, pax_pack)
    assert calibration.id not in (pax.known_modifications or [])
    assert reagent.id not in pax.pack.exotics

    nia_research = CharacterResearch.query.filter_by(
        character_id=nia.id, research_id=stabiliser.id
    ).one()
    assert nia_research.current_stage.stage_number == 2
    prototype = CharacterResearchStage.query.filter_by(
        character_research_id=nia_research.id,
        stage_id=stabiliser.stages[0].id,
    ).one()
    assert prototype.stage_completed
    assert all(row.progress >= row.requirement.amount for row in prototype.requirement_progress)
    assert f"Synthesized {vita.name}" in downtime_text(sera, sera_pack)
    assert vita.id in sera.pack.exotics
    assert contested.id in sera.pack.samples
    assert "Made progress on" in downtime_text(sera, sera_pack)
    assert f"Contributed {spore.name}" in downtime_text(nia, nia_pack)
    assert f"Contributed 1 {reagent.name}" in downtime_text(pax, pax_pack)
    assert f"Contributed {component_blueprint.display_name}" in downtime_text(pax, pax_pack)

    catalyst = Research.query.filter_by(project_name="Field catalyst").one()
    sera_catalyst = CharacterResearch.query.filter_by(
        character_id=sera.id, research_id=catalyst.id
    ).one()
    assert sera_catalyst.get_current_stage().stage.name == "Bench test"
    assert "New project confirmed: Field catalyst" in downtime_text(sera, sera_pack)
    assert sera.get_reputation(concord.id) == 4
    sera_messages = messages(sera)
    assert any(
        message["type"] == "reputation_response" and "sponsor one trial" in message["content"]
        for message in sera_messages
    )
    assert any(
        message["type"] == "other_info"
        and message["content"] == "Return the sealed case to Concord."
        for message in sera_messages
    )
    assert sera_pack.player_other == "Please mention the sealed case in the brief."
    fever_state = next(row for row in sera.active_conditions if row.condition_id == fever.id)
    assert fever_state.current_stage == 1
    assert fever_state.current_duration == 1

    wynn_lesson = CharacterResearch.query.filter_by(
        character_id=wynn.id, research_id=lesson.id
    ).one()
    assert wynn_lesson.current_stage.stage_number == 2
    taught = CharacterResearchStage.query.filter_by(
        character_research_id=wynn_lesson.id, stage_id=lesson_stage.id
    ).one()
    assert taught.stage_completed
    assert f"Successfully taught {lesson.project_name} to Wynn" in downtime_text(theo, theo_pack)
    db.session.refresh(lens)
    assert [stage.stage_number for stage in lens.stages] == [1, 2]
    theo_lens = CharacterResearch.query.filter_by(character_id=theo.id, research_id=lens.id).one()
    assert theo_lens.current_stage.name == "Field focus"
    assert f"Improved {lens.project_name}" in downtime_text(theo, theo_pack)

    assert culture.is_researched is True
    assert "Researched sample" in downtime_text(wynn, wynn_pack)
    assert any(
        message["type"] == "invention_declined" and "Perpetual engine" in message["content"]
        for message in messages(wynn)
    )
    assert any("thermodynamics" in message["content"] for message in messages(wynn))
    assert wynn.get_reputation(meridian.id) == -1
    burnout_state = next(row for row in wynn.active_conditions if row.condition_id == burnout.id)
    assert burnout_state.current_stage is None
    assert burnout_state.current_duration == 0

    for user in (iona_user, sera_user, nia_user, pax_user, theo_user, wynn_user):
        db.session.refresh(user)
        assert user.character_points == 1.0
        assert "character points" in downtime_text(user.characters[0], packs[user.characters[0].id])
    db.session.refresh(pip_user)
    db.session.refresh(crew_user)
    db.session.refresh(lark_user)
    assert pip_user.character_points == 0
    assert crew_user.character_points == 1.0
    assert lark_user.character_points == 0

    for character in (iona, sera, nia, pax, theo, wynn, pip):
        assert character.pack_complete is False
        assert character.pack.completion.get("character_sheet") is not True
        assert character.pack.completion.get("character_id_badge") is not True
