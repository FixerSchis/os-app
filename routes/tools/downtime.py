import json
import secrets

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.conditions import Condition
from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.database.sample import Sample, SampleTag
from models.enums import (
    DowntimeStatus,
    DowntimeTaskStatus,
    EventType,
    ResearchRequirementType,
    ScienceType,
)
from models.event import Event
from models.extensions import db
from models.tools.character import Character, CharacterCondition
from models.tools.downtime import DowntimePack, DowntimePeriod
from models.tools.event_ticket import EventTicket
from models.tools.research import (
    CharacterResearch,
    CharacterResearchStage,
    Research,
    ResearchStage,
    ResearchStageRequirement,
)
from utils.decorators import character_owner_or_downtime_team_required, downtime_team_required
from utils.email import send_downtime_completed_notification, send_downtime_pack_enter_notification

bp = Blueprint("downtime", __name__)


def get_available_science_slots_with_sources(character, science_type=None):
    """Get available science slots with their sources."""
    slots = []

    # Get slots from skills
    for skill in character.skills:
        if skill.skill.adds_science_downtime > 0:
            if science_type is None or skill.skill.science_type == science_type:
                for _ in range(skill.times_purchased):
                    slots.append(
                        {
                            "source": f"Skill: {skill.skill.name}",
                            "type": skill.skill.science_type,
                        }
                    )

    # Get slots from cybernetics
    for cybernetic in character.cybernetics_link:
        if cybernetic.cybernetic.adds_science_downtime > 0:
            if science_type is None or cybernetic.cybernetic.science_type == science_type:
                slots.append(
                    {
                        "source": f"Cybernetic: {cybernetic.cybernetic.name}",
                        "type": cybernetic.cybernetic.science_type,
                    }
                )

    # Get slots from research teams in current downtime pack
    current_pack = next(
        (
            pack
            for pack in character.downtime_packs
            if pack.status == DowntimeTaskStatus.ENTER_DOWNTIME
        ),
        None,
    )
    if current_pack and current_pack.research_teams:
        for faction_id in current_pack.research_teams:
            faction = db.session.get(Faction, faction_id)
            if faction and (science_type is None or science_type == ScienceType.GENERIC):
                slots.append(
                    {
                        "source": f"Research Team: {faction.name}",
                        "type": ScienceType.GENERIC,
                    }
                )

    return slots


def get_available_engineering_slots_with_sources(character):
    """Get available engineering slots with their sources."""
    slots = []

    # Get slots from skills
    for skill in character.skills:
        if skill.skill.adds_engineering_downtime > 0:
            for _ in range(skill.times_purchased):
                slots.append({"source": f"Skill: {skill.skill.name}"})

    # Get slots from cybernetics
    for cybernetic in character.cybernetics_link:
        if cybernetic.cybernetic.adds_engineering_downtime > 0:
            slots.append({"source": f"Cybernetic: {cybernetic.cybernetic.name}"})

    return slots


@bp.route("/")
@login_required
def index():
    """Display the downtime management page."""
    active_period = DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).first()

    if not active_period:
        return render_template(
            "downtime/index.html",
            active_period=None,
            DowntimeStatus=DowntimeStatus,
            DowntimeTaskStatus=DowntimeTaskStatus,
            EventType=EventType,
        )

    # For downtime team users
    if current_user.has_role("downtime_team"):
        # Get all packs and group them by status
        packs_by_status = {}
        for pack in active_period.packs:
            if pack.status.value not in packs_by_status:
                packs_by_status[pack.status.value] = []
            packs_by_status[pack.status.value].append(pack)

        # Get the first status that has entries
        default_status = next(
            (status for status in DowntimeTaskStatus if status.value in packs_by_status),
            None,
        )

        return render_template(
            "downtime/index.html",
            active_period=active_period,
            DowntimeStatus=DowntimeStatus,
            DowntimeTaskStatus=DowntimeTaskStatus,
            EventType=EventType,
            packs_by_status=packs_by_status,
            default_status=default_status.value if default_status else None,
        )

    # For regular users
    else:
        # Get user's characters that are in enter_downtime state
        user_packs = [
            pack
            for pack in active_period.packs
            if pack.character.user_id == current_user.id
            and pack.status == DowntimeTaskStatus.ENTER_DOWNTIME
        ]

        # If user has one character in enter_downtime state, redirect to enter downtime
        if len(user_packs) == 1:
            return redirect(
                url_for(
                    "downtime.enter_downtime",
                    period_id=active_period.id,
                    character_id=user_packs[0].character.id,
                )
            )

        # If user has no valid characters, flash message and redirect to site index
        if not user_packs:
            flash("You have no characters that can enter downtime at this time.", "info")
            return redirect(url_for("index"))

        return render_template(
            "downtime/index.html",
            active_period=active_period,
            DowntimeStatus=DowntimeStatus,
            DowntimeTaskStatus=DowntimeTaskStatus,
            EventType=EventType,
            user_packs=user_packs,
        )


@bp.route("/start", methods=["POST"])
@login_required
@downtime_team_required
def start_downtime():
    """Start a new downtime period."""
    if DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).first():
        flash("There is already an active downtime period.", "error")
        return redirect(url_for("downtime.index"))

    event_id = request.form.get("event_id")
    if not event_id:
        flash("Please select an event for this downtime period.", "error")
        return redirect(url_for("downtime.index"))

    event = Event.query.get_or_404(event_id)

    period = DowntimePeriod(status=DowntimeStatus.PENDING, event_id=event.id)
    db.session.add(period)

    for character in EventTicket.query.filter_by(event_id=event_id).all():
        pack = DowntimePack(
            period_id=period.id,
            character_id=character.id,
            status=DowntimeTaskStatus.ENTER_PACK,
        )
        db.session.add(pack)

    db.session.commit()
    flash("New downtime period started successfully.", "success")
    return redirect(url_for("downtime.index"))


@bp.route("/enter-pack-contents/<int:period_id>/<int:character_id>", methods=["GET"])
@login_required
@downtime_team_required
def enter_pack_contents(period_id, character_id):
    """Display the pack contents entry page."""
    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.ENTER_PACK:
        flash("This pack is not in the correct state for entering contents.", "error")
        return redirect(url_for("downtime.index"))

    # Get all available items, exotics, conditions, and samples
    items = db.session.query(Item).join(ItemBlueprint).order_by(ItemBlueprint.name).all()
    exotics = ExoticSubstance.query.order_by(ExoticSubstance.name).all()
    conditions = Condition.query.order_by(Condition.name).all()
    samples = Sample.query.order_by(Sample.name).all()
    sample_tags = SampleTag.query.order_by(SampleTag.name).all()
    cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    factions = Faction.query.order_by(Faction.name).all()

    return render_template(
        "downtime/enter_pack_contents.html",
        period_id=period_id,
        character=pack.character,
        pack=pack,
        items=items,
        exotics=exotics,
        conditions=conditions,
        samples=samples,
        sample_tags=sample_tags,
        cybernetics=cybernetics,
        factions=factions,
        ScienceType=ScienceType,
    )


@bp.route("/enter-pack-contents/<int:period_id>/<int:character_id>", methods=["POST"])
@login_required
@downtime_team_required
def enter_pack_contents_post(period_id, character_id):
    """Handle pack contents entry submission."""
    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.ENTER_PACK:
        flash("This pack is not in the correct state for entering contents.", "error")
        return redirect(url_for("downtime.index"))

    # Get selected items
    pack.items = request.form.getlist("items[]")

    # Get exotics with amounts
    exotics = []
    for exotic_id in request.form.getlist("exotic_ids[]"):
        amount = request.form.get(f"exotic_amount_{exotic_id}", type=int)
        if amount and amount > 0:
            exotics.append({"id": exotic_id, "amount": amount})
    pack.exotic_substances = exotics

    # Get conditions with durations
    conditions = []
    for condition_id in request.form.getlist("condition_ids[]"):
        duration = request.form.get(f"condition_duration_{condition_id}", type=int)
        if duration and duration > 0:
            conditions.append({"id": condition_id, "duration": duration})
    pack.conditions = conditions

    # Get samples
    pack.samples = request.form.getlist("samples[]")

    # Get cybernetics
    pack.cybernetics = request.form.getlist("cybernetics[]")

    # Get research teams
    pack.research_teams = request.form.getlist("research_teams[]")

    # Get energy chits
    pack.energy_credits = int(request.form.get("energy_chits", 0))

    # On confirm, add samples to group inventory and conditions to player
    if request.form.get("confirm_complete"):
        # Add samples to group inventory
        if pack.character.group and pack.samples:
            for sample_id in pack.samples:
                sample = db.session.get(Sample, sample_id)
                if sample and sample not in pack.character.group.samples:
                    pack.character.group.samples.append(sample)

        # Add conditions to player with audit logging
        if pack.conditions:
            from models.enums import CharacterAuditAction
            from models.tools.character import CharacterAuditLog

            for condition in pack.conditions:
                if condition and condition not in pack.character.active_conditions:
                    condition_obj = db.session.get(Condition, condition["id"])
                    if condition_obj:
                        # Create audit log for condition addition
                        audit = CharacterAuditLog(
                            character_id=pack.character.id,
                            editor_user_id=current_user.id,
                            action=CharacterAuditAction.CONDITION_CHANGE.value,
                            changes=f"Condition added via downtime: {condition_obj.name} "
                            "(Stage 1, Duration {condition['duration']})",
                        )
                        db.session.add(audit)

                        pack.character.active_conditions.append(
                            CharacterCondition(
                                character_id=pack.character.id,
                                condition_id=condition["id"],
                                current_stage=1,
                                current_duration=condition["duration"],
                            )
                        )

        # Add cybernetics to character with audit logging
        if pack.cybernetics:
            from models.enums import CharacterAuditAction
            from models.tools.character import CharacterAuditLog

            for cybernetic_id in pack.cybernetics:
                cybernetic = db.session.get(Cybernetic, cybernetic_id)
                if cybernetic and cybernetic not in pack.character.cybernetics:
                    # Create audit log for cybernetic addition
                    audit = CharacterAuditLog(
                        character_id=pack.character.id,
                        editor_user_id=current_user.id,
                        action=CharacterAuditAction.CYBERNETICS_CHANGE.value,
                        changes=f"Cybernetic added via downtime: {cybernetic.name}",
                    )
                    db.session.add(audit)

                    db.session.add(
                        CharacterCybernetic(
                            character_id=pack.character.id, cybernetic_id=cybernetic_id
                        )
                    )
        pack.status = DowntimeTaskStatus.ENTER_DOWNTIME
        if pack.energy_credits > 0:
            pack.character.add_funds(
                pack.energy_credits, current_user.id, f"Energy credits from downtime pack {pack.id}"
            )
        send_downtime_pack_enter_notification(pack.character.user, pack.character, pack)
    db.session.commit()
    flash("Pack contents entered successfully.", "success")
    return redirect(url_for("downtime.index"))


@bp.route("/enter-downtime/<int:period_id>/<int:character_id>", methods=["GET"])
@login_required
@character_owner_or_downtime_team_required
def enter_downtime(period_id, character_id):
    """Display the downtime activity entry page."""
    character = Character.query.get_or_404(character_id)

    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.ENTER_DOWNTIME:
        flash(
            "This pack is not in the correct state for entering downtime activities.",
            "error",
        )
        return redirect(url_for("downtime.index"))

    # Bank balances
    bank_balance = character.bank_account
    group_bank_balance = character.group.bank_account if character.group else None

    # Get all mods: known + available
    known_mod_ids = [mod_id for mod_id in character.known_modifications]
    available_mods = Mod.query.filter(~Mod.id.in_(known_mod_ids)).order_by(Mod.name).all()
    known_mods = Mod.query.filter(Mod.id.in_(known_mod_ids)).order_by(Mod.name).all()
    all_mods = known_mods + available_mods

    # Items from own and group downtime packs
    pack_items = [db.session.get(Item, item_id) for item_id in pack.items]
    group_items = []
    if character.group:
        group_packs = DowntimePack.query.filter(
            DowntimePack.period_id == period_id,
            DowntimePack.character_id.in_(
                [c.id for c in character.group.members if c.id != character.id]
            ),
        ).all()
        for pack in group_packs:
            group_items.extend(pack.items)

    # Get all item blueprints (for purchase step)
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    blueprints_data = [
        {"id": bp.id, "name": bp.name, "base_cost": bp.base_cost} for bp in blueprints
    ]

    if character.group:
        available_samples = character.group.samples.order_by(Sample.name).all()
    else:
        available_samples = (
            Sample.query.filter(Sample.id.in_(pack.samples)).order_by(Sample.name).all()
            if pack.samples
            else []
        )

    # Research projects for science step
    my_projects = CharacterResearch.query.filter_by(character_id=character.id).all()
    group_projects = []
    group_members = []
    if character.group:
        group_member_ids = [c.id for c in character.group.members]
        group_projects = CharacterResearch.query.filter(
            CharacterResearch.character_id.in_(group_member_ids)
        ).all()
        group_members = [c for c in character.group.members if c.id != character.id]

    # Convert CharacterResearch objects to dictionaries
    my_projects = [
        {
            "research_id": cr.research.public_id,
            "project_name": cr.research.project_name,
            "character_name": cr.character.name if cr.character else None,
        }
        for cr in my_projects
    ]
    group_projects = [
        {
            "research_id": cr.research.public_id,
            "project_name": cr.research.project_name,
            "character_name": cr.character.name if cr.character else None,
        }
        for cr in group_projects
    ]
    pack_items = [
        {
            "id": item.id,
            "name": item.blueprint.name,
            "type": item.blueprint.item_type.id,
            "full_code": item.full_code,
        }
        for item in pack_items
    ]
    group_items = [
        {
            "id": item.id,
            "name": item.blueprint.name,
            "type": item.blueprint.item_type.id,
            "full_code": item.full_code,
        }
        for item in group_items
    ]
    available_samples = [
        {
            "id": sample.id,
            "name": sample.name,
            "type": sample.type.value,
            "tags": [tag.name for tag in sample.tags],
            "is_researched": sample.is_researched,
        }
        for sample in available_samples
    ]
    pack_exotics = [
        {
            "id": exotic["id"],
            "name": db.session.get(ExoticSubstance, exotic["id"]).name,
            "amount": exotic["amount"],
        }
        for exotic in pack.exotic_substances
    ]

    # Get existing downtime activities
    pack_purchases = pack.purchases or []
    pack_modifications = pack.modifications or []
    pack_engineering = pack.engineering or []
    pack_science = pack.science or []
    pack_research = pack.research or []
    pack_reputation = pack.reputation or []

    # Get available slots with their sources
    science_slots = get_available_science_slots_with_sources(character)
    engineering_slots = get_available_engineering_slots_with_sources(character)

    return render_template(
        "downtime/enter_downtime.html",
        character=character,
        pack=pack,
        bank_balance=bank_balance,
        group_bank_balance=group_bank_balance,
        all_mods=all_mods,
        pack_items=pack_items,
        group_items=group_items,
        blueprints_data=blueprints_data,
        available_samples=available_samples,
        my_projects=my_projects,
        group_projects=group_projects,
        group_members=group_members,
        pack_purchases=pack_purchases,
        pack_modifications=pack_modifications,
        pack_engineering=pack_engineering,
        pack_science=pack_science,
        pack_research=pack_research,
        pack_reputation=pack_reputation,
        pack_exotics=pack_exotics,
        science_slots=science_slots,
        engineering_slots=engineering_slots,
        DowntimeTaskStatus=DowntimeTaskStatus,
        ResearchRequirementType=ResearchRequirementType,
        ScienceType=ScienceType,
    )


@bp.route("/enter-downtime/<int:period_id>/<int:character_id>", methods=["POST"])
@login_required
@character_owner_or_downtime_team_required
def enter_downtime_post(period_id, character_id):
    """Handle downtime activity entry submission."""
    Character.query.get_or_404(character_id)

    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.ENTER_DOWNTIME:
        flash(
            "This pack is not in the correct state for entering downtime activities.",
            "error",
        )
        return redirect(url_for("downtime.index"))

    # Parse JSON data with error handling
    try:
        pack.purchases = [json.loads(p) for p in request.form.getlist("purchases[]")]
        pack.modifications = [json.loads(m) for m in request.form.getlist("modifications[]")]
        pack.engineering = [json.loads(e) for e in request.form.getlist("engineering[]")]
        pack.science = [json.loads(s) for s in request.form.getlist("science[]")]
        pack.research = [json.loads(r) for r in request.form.getlist("research[]")]
        pack.reputation = [json.loads(r) for r in request.form.getlist("reputation[]")]
    except json.JSONDecodeError as e:
        flash(f"Invalid JSON data provided: {str(e)}", "error")
        return redirect(
            url_for(
                "downtime.enter_downtime",
                period_id=period_id,
                character_id=character_id,
            )
        )

    # If confirm complete is checked, move to manual review
    if request.form.get("confirm_complete"):
        pack.status = DowntimeTaskStatus.MANUAL_REVIEW

    db.session.commit()
    flash("Downtime activities saved successfully.", "success")
    return redirect(url_for("downtime.index"))


@bp.route("/manual-review/<int:period_id>/<int:character_id>", methods=["GET"])
@login_required
@downtime_team_required
def manual_review(period_id, character_id):
    """Display the manual review page for downtime activities."""
    character = Character.query.get_or_404(character_id)
    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.MANUAL_REVIEW:
        flash("This pack is not in the correct state for manual review.", "error")
        return redirect(url_for("downtime.index"))

    # Get all activities that need review
    invention = None
    invention_index = None
    for i, s in enumerate(pack.science):
        if s.get("action") == "theorise":
            invention = s
            invention_index = i
            break

    # Add faction names to reputation questions
    reputation_questions = []
    for question in pack.reputation or []:
        faction = db.session.get(Faction, question.get("faction_id"))
        if faction:
            question["faction"] = faction
            reputation_questions.append(question)

    # Get data needed for research requirements
    item_types = [
        {"id": item.id, "name": item.name, "id_prefix": item.id_prefix}
        for item in ItemType.query.all()
    ]
    exotics = [
        {"id": substance.id, "name": substance.name} for substance in ExoticSubstance.query.all()
    ]
    sample_tags = [tag.name for tag in SampleTag.query.all()]

    if not pack.review_data.get("stages_json") or pack.review_data.get("stages_json") == "[]":
        pack.review_data["stages_json"] = json.dumps(
            [
                {
                    "stage_number": 1,
                    "name": "Stage 1",
                    "description": "",
                    "unlock_requirements": [],
                }
            ]
        )

    # Add review data to the template context
    return render_template(
        "downtime/manual_review.html",
        character=character,
        pack=pack,
        invention=invention,
        invention_index=invention_index,
        reputation_questions=reputation_questions,
        review_data=pack.review_data or {},
        item_types=item_types,
        exotics=exotics,
        sample_tags=sample_tags,
        DowntimeTaskStatus=DowntimeTaskStatus,
        ResearchRequirementType=ResearchRequirementType,
        ScienceType=ScienceType,
    )


@bp.route("/manual-review/<int:period_id>/<int:character_id>", methods=["POST"])
@login_required
@downtime_team_required
def manual_review_post(period_id, character_id):
    """Handle manual review submission."""
    pack = DowntimePack.query.filter_by(
        period_id=period_id, character_id=character_id
    ).first_or_404()

    if pack.status != DowntimeTaskStatus.MANUAL_REVIEW:
        flash("This pack is not in the correct state for manual review.", "error")
        return redirect(url_for("downtime.index"))

    # Initialize review data
    review_data = dict(pack.review_data or {})

    print("STAGES_JSON from form:", request.form.get("stages_json"))

    # Handle invention review
    if "invention_review" in request.form:
        review_data["invention_review"] = request.form["invention_review"]
        if review_data["invention_review"] == "decline":
            review_data["invention_response"] = request.form.get("invention_response", "")
        else:
            review_data["invention_type"] = request.form.get("invention_type", "new")
            if review_data["invention_type"] == "new":
                review_data["invention_name"] = request.form.get("invention_name", "")
                review_data["invention_description"] = request.form.get("invention_description", "")
                review_data["stages_json"] = request.form.get("stages_json", "")
            else:
                review_data["existing_invention"] = request.form.get("existing_invention", "")

    # Handle reputation question responses
    for question in pack.reputation:
        response_key = f'reputation_response_{question.get("faction_id")}'
        if response_key in request.form:
            review_data[response_key] = request.form[response_key]

    # Save review data to pack
    pack.review_data = review_data

    if request.form.get("confirm_complete"):
        pack.status = DowntimeTaskStatus.COMPLETED

    db.session.commit()
    flash("Manual review saved successfully.", "success")
    return redirect(url_for("downtime.index"))


@bp.route("/process/<int:period_id>", methods=["POST"])
@login_required
@downtime_team_required
def process_downtime(period_id):
    """Process a completed downtime period."""
    period = DowntimePeriod.query.get_or_404(period_id)
    if not period.event:
        flash("This downtime period is not associated with an event.", "error")
        return redirect(url_for("downtime.index"))

    # Verify all packs are in completed state
    if not all(pack.status == DowntimeTaskStatus.COMPLETED for pack in period.packs):
        flash("Cannot process downtime - not all packs are complete.", "error")
        return redirect(url_for("downtime.index"))

    packs = DowntimePack.query.filter_by(period_id=period_id).all()

    # Initialize downtime results for all packs
    for pack in packs:
        # Initialize downtime results for this pack
        if not pack.character.character_pack:
            pack.character.character_pack = {}
        if "downtime_results" not in pack.character.character_pack:
            pack.character.character_pack["downtime_results"] = {}
        if str(pack.id) not in pack.character.character_pack["downtime_results"]:
            pack.character.character_pack["downtime_results"][str(pack.id)] = []
        if "items" not in pack.character.character_pack:
            pack.character.character_pack["items"] = []
        if "exotic_substances" not in pack.character.character_pack:
            pack.character.character_pack["exotic_substances"] = []
        if "samples" not in pack.character.character_pack:
            pack.character.character_pack["samples"] = []
        if "chits" not in pack.character.character_pack:
            pack.character.character_pack["chits"] = 0

    # Process modifications
    for pack in packs:
        for modification in pack.modifications:
            if modification["type"] == "learning":
                mod = db.session.get(Mod, modification["mod_id"])
                if mod:
                    pack.character.known_modifications.append(modification["mod_id"])
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Learned mod: {mod.name}"
                    )
            elif modification["type"] == "forgetting":
                mod = db.session.get(Mod, modification["mod_id"])
                if mod:
                    pack.character.known_modifications.remove(modification["mod_id"])
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Forgot modification: {mod.name}"
                    )

    # Process purchases
    for pack in packs:
        for purchase in pack.purchases:
            blueprint = db.session.get(ItemBlueprint, purchase["blueprint_id"])
            if pack.character.can_afford(blueprint.base_cost):
                pack.character.remove_funds(
                    blueprint.base_cost, current_user.id, f"Purchase: {blueprint.name}"
                )
                new_item = Item(
                    character_id=pack.character.id,
                    blueprint_id=blueprint.id,
                    full_code=blueprint.full_code,
                    expiry=period.event.event_number + 4,
                )
                pack.items.append(new_item)
                pack.character.character_pack["downtime_results"][str(pack.id)].append(
                    f"Purchased: {blueprint.name}"
                )
                for engineering in pack.engineering:
                    if engineering.source == "own" and engineering.blueprint_id == blueprint.id:
                        engineering.item_id = new_item.id
                        engineering.blueprint_id = None
                        break
            else:
                pack.character.character_pack["downtime_results"][str(pack.id)].append(
                    f"Could not purchase {blueprint.name} - insufficient funds"
                )

    # Process engineering maintenance
    for pack in packs:
        for engineering in pack.engineering:
            if engineering.action == "maintain":
                item = db.session.get(Item, engineering.item_id)
                if item and pack.character.can_afford(item.get_maintenance_cost()):
                    pack.character.remove_funds(
                        item.get_maintenance_cost(), current_user.id, f"Maintenance: {item.name}"
                    )
                    item.expiry = period.event.event_number + 4
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Maintained {item.name} - new expiry: E{item.expiry}"
                    )
                elif not pack.character.can_afford(item.get_maintenance_cost()):
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Could not maintain {item.name} - insufficient funds"
                    )

    # Process engineering modifications
    for pack in packs:
        for engineering in pack.engineering:
            if engineering.action == "modify":
                item = db.session.get(Item, engineering.item_id)
                mod = db.session.get(Mod, engineering.mod_id)
                if (
                    item
                    and mod
                    and pack.character.can_afford(item.get_modification_cost(engineering.mods))
                    and pack.character.known_modifications.contains(mod)
                ):
                    pack.character.remove_funds(
                        item.get_modification_cost(engineering.mods),
                        current_user.id,
                        f"Modification: {mod.name} on {item.name}",
                    )
                    item.mods_applied.append(mod)
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Applied {mod.name} to {item.name}"
                    )
                elif not pack.character.can_afford(item.get_modification_cost(engineering.mods)):
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Could not apply {mod.name} to {item.name} - " f"insufficient funds"
                    )
                elif not pack.character.known_modifications.contains(mod):
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Could not apply {mod.name} to {item.name} - "
                        f"character does not know the modification"
                    )

    # Process science
    for pack in packs:
        for science in pack.science:
            if science.action == "synthesize":
                science_type = science.get("science_type", ScienceType.GENERIC)

                query = ExoticSubstance.query
                if science_type != ScienceType.GENERIC:
                    query = query.filter_by(type=science_type)

                exotics = query.all()
                if exotics:
                    exotic = secrets.choice(exotics)

                    # Add the exotic to the character's pack
                    if not pack.exotic_substances:
                        pack.exotic_substances = []
                    pack.exotic_substances.append(
                        {
                            "id": exotic.id,
                            "name": exotic.name,
                            "type": exotic.type.value,
                        }
                    )
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Synthesized {exotic.name}"
                    )

            elif science.action == "research_sample":
                sample_id = science.get("sample_id")
                if sample_id:
                    sample = db.session.get(Sample, sample_id)
                    if sample and not sample.is_researched:
                        sample.is_researched = True
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Researched sample: {sample.name}"
                        )
                    elif sample.is_researched:
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Sample {sample.name} already researched"
                        )

            elif science.action == "research_project":
                project_id = science.get("project_id")
                research_for_id = science.get("research_for_id")
                science_type = science.get("science_type", ScienceType.GENERIC)

                if project_id and research_for_id:
                    research_for_character = Character.get_by_player_reference(research_for_id)

                    # Get the target character's research
                    target_research = CharacterResearch.query.filter_by(
                        research_id=Research.query.filter_by(public_id=project_id).first().id,
                        character_id=research_for_character.id,
                    ).first()

                    if target_research and not target_research.is_complete():
                        current_stage = target_research.get_current_stage()
                        if current_stage:
                            # Find the first matching requirement based on science type
                            made_progress = False
                            for req_progress in current_stage.requirement_progress:
                                if (
                                    req_progress.requirement.requirement_type
                                    == ResearchRequirementType.SCIENCE
                                    and req_progress.requirement.science_type == science_type
                                    and req_progress.progress < req_progress.requirement.amount
                                ):
                                    req_progress.progress += 1
                                    pack.character.character_pack["downtime_results"][
                                        str(pack.id)
                                    ].append(
                                        f"Made progress on "
                                        f"{target_research.research.project_name}"
                                    )
                                    made_progress = True
                                    break
                            if not made_progress:
                                pack.character.character_pack["downtime_results"][
                                    str(pack.id)
                                ].append(
                                    f"Failed to make progress on "
                                    f"{target_research.research.project_name} for "
                                    f"{target_research.character.name}"
                                )
                        else:
                            pack.character.character_pack["downtime_results"][str(pack.id)].append(
                                f"No current stage for "
                                f"{target_research.research.project_name} for "
                                f"{target_research.character.name}"
                            )
                    elif target_research.is_complete():
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Research already complete for "
                            f"{target_research.research.project_name} for "
                            f"{target_research.character.name}"
                        )
                    else:
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"No research found for {project_id}"
                        )

            elif science.action == "teach_invention":
                project_id = science.get("project_id")
                teach_to_id = science.get("teach_to_id")

                if project_id and teach_to_id:
                    teach_to_character = Character.get_by_player_reference(teach_to_id)

                    # Get the teaching character's research
                    teaching_research = CharacterResearch.query.filter_by(
                        research_id=Research.query.filter_by(public_id=project_id).first().id,
                        character_id=pack.character.id,
                    ).first()

                    # Get the target character's research
                    target_research = CharacterResearch.query.filter_by(
                        research_id=Research.query.filter_by(public_id=project_id).first().id,
                        character_id=teach_to_character.id,
                    ).first()

                    if not target_research:
                        target_research = teaching_research.assign_character(teach_to_id)

                    if teaching_research and target_research and not target_research.is_complete():
                        target_current_stage = target_research.get_current_stage()
                        if target_current_stage:
                            # Check if teaching character has completed this stage
                            teaching_stage = CharacterResearchStage.query.filter_by(
                                character_research_id=teaching_research.id,
                                stage_id=target_current_stage.stage_id,
                                stage_completed=True,
                            ).first()

                            if teaching_stage:
                                # Mark all requirements as complete
                                for req_progress in target_current_stage.requirement_progress:
                                    req_progress.progress = req_progress.requirement.amount

                                # Mark stage as completed
                                target_current_stage.stage_completed = True
                                pack.character.character_pack["downtime_results"][
                                    str(pack.id)
                                ].append(
                                    f"Successfully taught "
                                    f"{target_research.research.project_name} to "
                                    f"{target_research.character.name}"
                                )
                            else:
                                pack.character.character_pack["downtime_results"][
                                    str(pack.id)
                                ].append(
                                    f"Failed to teach "
                                    f"{target_research.research.project_name} to "
                                    f"{target_research.character.name} - no stages to teach"
                                )
                    else:
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Failed to teach "
                            f"{target_research.research.project_name} for "
                            f"{target_research.character.name} - target has completed this project"
                        )

        for research in pack.research:
            project_id = research.get("project_id")
            support_target = research.get("support_target")
            support_target_id = research.get("support_target_id")

            if project_id:
                # Get the target character's research
                research_character = None
                target_research = None
                if support_target == "self":
                    research_character = pack.character
                    target_research = CharacterResearch.query.filter_by(
                        research_id=Research.query.filter_by(public_id=project_id).first().id,
                        character_id=pack.character.id,
                    ).first()
                elif support_target == "group" or support_target == "other":
                    research_character = Character.get_by_player_reference(support_target_id)
                    target_research = CharacterResearch.query.filter_by(
                        research_id=Research.query.filter_by(public_id=project_id).first().id,
                        character_id=research_character.id,
                    ).first()

                if target_research and not target_research.is_complete():
                    current_stage = target_research.get_current_stage()
                    if current_stage:
                        # Process contributed exotics
                        if research.get("contributed_exotics"):
                            for exotic in research.get("contributed_exotics"):
                                exotic_id = exotic.get("id")
                                quantity = exotic.get("quantity", 0)
                                if exotic_id and quantity > 0:
                                    substance = db.session.get(ExoticSubstance, exotic_id)
                                    # Find matching requirement
                                    for req_progress in current_stage.requirement_progress:
                                        if (
                                            req_progress.requirement.requirement_type
                                            == ResearchRequirementType.EXOTIC
                                            and req_progress.requirement.exotic_substance_id
                                            == substance.id
                                            and req_progress.progress
                                            < req_progress.requirement.amount
                                        ):
                                            # Add progress
                                            req_progress.progress += quantity
                                            # Remove from pack
                                            for pack_exotic in pack.exotic_substances:
                                                if pack_exotic.get("id") == exotic_id:
                                                    pack_exotic["quantity"] -= quantity
                                                    if pack_exotic.get("quantity", 0) <= 0:
                                                        pack.exotic_substances.remove(pack_exotic)
                                                    break
                                            pack.character.character_pack["downtime_results"][
                                                str(pack.id)
                                            ].append(
                                                f"Contributed {quantity} {substance.name} to "
                                                f"{target_research.research.project_name} "
                                                f"for {research_character.name}"
                                            )
                                            break

                        # Process contributed items
                        if research.get("contributed_items"):
                            for item_id in research.get("contributed_items"):
                                if item_id:
                                    item = db.session.get(Item, item_id)
                                    # Find matching requirement
                                    for req_progress in current_stage.requirement_progress:
                                        if (
                                            req_progress.requirement.requirement_type
                                            == ResearchRequirementType.ITEM
                                            and req_progress.requirement.item_type
                                            == item.blueprint.item_type.id
                                            and req_progress.progress
                                            < req_progress.requirement.amount
                                        ):
                                            # Add progress
                                            req_progress.progress += 1
                                            # Remove from pack
                                            for pack_item in pack.items:
                                                if pack_item.get("id") == item_id:
                                                    pack.items.remove(pack_item)
                                                    break
                                            pack.character.character_pack["downtime_results"][
                                                str(pack.id)
                                            ].append(
                                                f"Contributed {item.blueprint.name} to "
                                                f"{target_research.research.project_name} "
                                                f"for {research_character.name}"
                                            )
                                            break

                        # Process contributed samples
                        if research.get("contributed_samples"):
                            for sample_id in research.get("contributed_samples"):
                                if sample_id:
                                    sample = db.session.get(Sample, sample_id)
                                    # Find matching requirement
                                    for req_progress in current_stage.requirement_progress:
                                        if (
                                            req_progress.requirement.requirement_type
                                            == ResearchRequirementType.SAMPLE
                                            and req_progress.requirement.sample_tag == sample.tag
                                            and req_progress.progress
                                            < req_progress.requirement.amount
                                        ):
                                            # Add progress
                                            req_progress.progress += 1
                                            # Remove from pack
                                            for pack_sample in pack.samples:
                                                if pack_sample.get("id") == sample_id:
                                                    pack.samples.remove(pack_sample)
                                                    break
                                            pack.character.character_pack["downtime_results"][
                                                str(pack.id)
                                            ].append(
                                                f"Contributed {sample.name} to "
                                                f"{target_research.research.project_name} "
                                                f"for {research_character.name}"
                                            )
                                            break

    # Process manual entries
    for pack in packs:
        for manual in pack.manual_entries:
            if manual.get("type") == "invention_theory":
                if manual.get("review_status") == "approved":
                    if manual.get("invention_type") == "new":
                        # Create new research project
                        new_research = Research(
                            project_name=manual.get("invention_name"),
                            description=manual.get("invention_description"),
                            created_by=pack.character.id,
                        )
                        db.session.add(new_research)
                        db.session.flush()  # Get the ID

                        # Create stages and requirements
                        stages_data = json.loads(manual.get("stages_json", "[]"))
                        for stage_data in stages_data:
                            stage = ResearchStage(
                                research_id=new_research.id,
                                stage_number=stage_data["stage_number"],
                                name=stage_data["name"],
                                description=stage_data["description"],
                            )
                            db.session.add(stage)
                            db.session.flush()  # Get the ID

                            # Create requirements
                            for req_data in stage_data["unlock_requirements"]:
                                requirement = ResearchStageRequirement(
                                    stage_id=stage.id,
                                    requirement_type=req_data["requirement_type"],
                                    amount=req_data["amount"],
                                )

                                # Set type-specific fields
                                if req_data["requirement_type"] == "science":
                                    requirement.science_type = req_data["science_type"]
                                elif req_data["requirement_type"] == "item":
                                    requirement.item_type = req_data["item_type"]
                                elif req_data["requirement_type"] == "exotic":
                                    requirement.exotic_substance_id = req_data["exotic_type"]
                                elif req_data["requirement_type"] == "sample":
                                    requirement.sample_tag = req_data["sample_tag"]
                                    requirement.requires_researched = req_data.get(
                                        "requires_researched", False
                                    )

                                db.session.add(requirement)

                        # Assign character to the research
                        new_research.assign_character(pack.character.id)
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"New project confirmed: {new_research.project_name}"
                        )

                    elif manual.get("invention_type") == "improve":
                        # Get the existing research project
                        existing_research = Research.query.filter_by(
                            id=manual.get("existing_invention")
                        ).first()

                        if existing_research:
                            # Get character's research
                            char_research = CharacterResearch.query.filter_by(
                                research_id=existing_research.id,
                                character_id=pack.character.id,
                            ).first()

                            if char_research:
                                # Verify all previous stages are complete
                                all_complete = True
                                for stage in char_research.stages:
                                    if not stage.stage_completed:
                                        all_complete = False
                                        break

                                if all_complete:
                                    # Create new stage
                                    stages_data = json.loads(manual.get("stages_json", "[]"))
                                    if stages_data:
                                        new_stage_data = stages_data[
                                            0
                                        ]  # Only use first stage for improvement
                                        new_stage = ResearchStage(
                                            research_id=existing_research.id,
                                            stage_number=len(existing_research.stages) + 1,
                                            name=new_stage_data["name"],
                                            description=new_stage_data["description"],
                                        )
                                        db.session.add(new_stage)
                                        db.session.flush()  # Get the ID

                                        # Create requirements
                                        for req_data in new_stage_data["unlock_requirements"]:
                                            requirement = ResearchStageRequirement(
                                                stage_id=new_stage.id,
                                                requirement_type=req_data["requirement_type"],
                                                amount=req_data["amount"],
                                            )

                                            # Set type-specific fields
                                            if req_data["requirement_type"] == "science":
                                                requirement.science_type = req_data["science_type"]
                                            elif req_data["requirement_type"] == "item":
                                                requirement.item_type = req_data["item_type"]
                                            elif req_data["requirement_type"] == "exotic":
                                                requirement.exotic_substance_id = req_data[
                                                    "exotic_type"
                                                ]
                                            elif req_data["requirement_type"] == "sample":
                                                requirement.sample_tag = req_data["sample_tag"]
                                                requirement.requires_researched = req_data.get(
                                                    "requires_researched", False
                                                )

                                            db.session.add(requirement)

                                        # Create character's stage
                                        char_stage = CharacterResearchStage(
                                            character_research_id=char_research.id,
                                            stage_id=new_stage.id,
                                        )
                                        db.session.add(char_stage)

                                        # Set as current stage
                                        char_research.current_stage_id = new_stage.id

                                        pack.character.character_pack["downtime_results"][
                                            str(pack.id)
                                        ].append(f"Improved {existing_research.project_name}")
                elif manual.get("review_status") == "declined":
                    # Add decline reason to character's pack
                    if not pack.character.character_pack:
                        pack.character.character_pack = {}
                    if "messages" not in pack.character.character_pack:
                        pack.character.character_pack["messages"] = []

                    # Add the decline message
                    pack.character.character_pack["messages"].append(
                        {
                            "type": "invention_declined",
                            "invention_name": manual.get("invention_name"),
                            "reason": manual.get("invention_response"),
                        }
                    )
            elif manual.get("type") == "reputation_response":
                # Add reputation response to character's pack
                if not pack.character.character_pack:
                    pack.character.character_pack = {}
                if "messages" not in pack.character.character_pack:
                    pack.character.character_pack["messages"] = []

                # Add the reputation response message
                pack.character.character_pack["messages"].append(
                    {
                        "type": "reputation_response",
                        "faction_id": manual.get("faction_id"),
                        "faction_name": manual.get("faction_name"),
                        "question": manual.get("question"),
                        "response": manual.get("response"),
                    }
                )

    # Process all research stages
    for pack in packs:
        # Get all research for this character
        character_research = CharacterResearch.query.filter_by(character_id=pack.character.id).all()

        for research in character_research:
            current_stage = research.get_current_stage()
            if current_stage:
                # If all requirements are met, mark the stage as complete
                if current_stage.meets_requirements():
                    current_stage.stage_completed = True
                    pack.character.character_pack["downtime_results"][str(pack.id)].append(
                        f"Completed stage '{current_stage.name}' of "
                        f"{research.research.project_name}"
                    )

                # If the stage is complete (whether just now or previously), advance to next stage
                if current_stage.stage_completed:
                    next_stage = research.advance_stage()
                    if next_stage:
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Advanced to stage '{next_stage.name}' in "
                            f"{research.research.project_name}"
                        )
                    else:
                        pack.character.character_pack["downtime_results"][str(pack.id)].append(
                            f"Completed all stages of " f"{research.research.project_name}"
                        )

    # Add items to character's pack
    for pack in packs:
        if pack.items:
            for item in pack.items:
                pack.character.character_pack["items"].append(item)
        if pack.exotic_substances:
            for exotic in pack.exotic_substances:
                pack.character.character_pack["exotic_substances"].append(exotic)
        if pack.samples:
            for sample in pack.samples:
                pack.character.character_pack["samples"].append(sample)
        # Add character income to their pack
        pack.character.character_pack["chits"] += 30
        send_downtime_completed_notification(pack.character.user, pack, pack.character)

    period.status = DowntimeStatus.COMPLETED

    db.session.commit()
    flash("Downtime period processed successfully.", "success")
    return redirect(url_for("downtime.index"))
