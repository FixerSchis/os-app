import json

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.exotic_substances import ExoticSubstance
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.sample import SampleTag
from models.enums import ResearchRequirementType, ResearchType, Role, ScienceType
from models.extensions import db
from models.tools.character import Character
from models.tools.research import (
    CharacterResearch,
    CharacterResearchStage,
    CharacterResearchStageRequirement,
    Research,
    ResearchStage,
    ResearchStageRequirement,
)
from utils.decorators import rules_team_required

research_bp = Blueprint("research", __name__)


def research_to_dict(project):
    """Convert a Research project to a dictionary format for API responses"""
    return {
        "found": True,
        "project_id": project.public_id,
        "project_name": project.project_name,
        "assignees": [
            {
                "character_id": cr.character_id,
                "character_name": cr.character.name,
                "user_id": cr.character.user_id,
                "current_stage_id": cr.current_stage_id,
                "character_research_id": cr.id,
            }
            for cr in project.character_research
        ],
    }


def req_to_dict(req):
    return {
        "id": req.id,
        "type": req.requirement_type.value if req.requirement_type else None,
        "science_type": req.science_type.value if req.science_type else None,
        "item_type": req.item_type,
        "exotic_type": req.exotic_substance_id,
        "sample_tag": req.sample_tag,
        "requires_researched": req.requires_researched,
        "amount": req.amount,
    }


@research_bp.route("/")
@login_required
@rules_team_required
def research_list():
    researches = Research.query.order_by(Research.project_name).all()
    return render_template("research/list.html", researches=researches)


@research_bp.route("/create", methods=["GET"])
@login_required
@rules_team_required
def research_create():
    items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    item_types = ItemType.query.order_by(ItemType.name).all()
    exotics = ExoticSubstance.query.order_by(ExoticSubstance.name).all()
    return render_template(
        "research/edit.html",
        research=None,
        items=items,
        blueprints=blueprints,
        item_types=item_types,
        exotics=exotics,
        ResearchType=ResearchType,
        ScienceType=ScienceType,
        ResearchRequirementType=ResearchRequirementType,
    )


@research_bp.route("/create", methods=["POST"])
@login_required
@rules_team_required
def research_create_post():
    project_name = request.form.get("project_name")
    type_value = request.form.get("type")
    description = request.form.get("description")
    artefact_option = request.form.get("artefact_option")
    stages_json = request.form.get("stages_json", "[]")
    item_id = None
    if type_value == "artefact":
        if artefact_option == "existing":
            item_id = request.form.get("item_id") or None
        elif artefact_option == "new":
            item_type_id = request.form.get("item_type_id")
            if not item_type_id:
                flash(
                    "You must select an item type to create a new artefact item.",
                    "error",
                )
                items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
                blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
                item_types = ItemType.query.order_by(ItemType.name).all()
                return render_template(
                    "research/edit.html",
                    research=None,
                    items=items,
                    blueprints=blueprints,
                    item_types=item_types,
                    ResearchType=ResearchType,
                    ScienceType=ScienceType,
                    ResearchRequirementType=ResearchRequirementType,
                )
            # Create new blueprint
            max_blueprint = (
                ItemBlueprint.query.filter_by(item_type_id=item_type_id)
                .order_by(ItemBlueprint.blueprint_id.desc())
                .first()
            )
            next_blueprint_id = (max_blueprint.blueprint_id + 1) if max_blueprint else 1
            new_blueprint = ItemBlueprint(
                name=project_name,
                item_type_id=item_type_id,
                blueprint_id=next_blueprint_id,
                base_cost=0,
            )
            db.session.add(new_blueprint)
            db.session.flush()
            # Create new item from blueprint
            max_item = (
                Item.query.filter_by(blueprint_id=new_blueprint.id)
                .order_by(Item.item_id.desc())
                .first()
            )
            next_item_id = (max_item.item_id + 1) if max_item else 1
            new_item = Item(blueprint_id=new_blueprint.id, item_id=next_item_id)
            db.session.add(new_item)
            db.session.flush()
            item_id = new_item.id
    if not project_name or not type_value:
        flash("Project name and type are required.", "error")
        items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
        blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
        item_types = ItemType.query.order_by(ItemType.name).all()
        return render_template(
            "research/edit.html",
            research=None,
            items=items,
            blueprints=blueprints,
            item_types=item_types,
            ResearchType=ResearchType,
            ScienceType=ScienceType,
            ResearchRequirementType=ResearchRequirementType,
        )
    research = Research(
        project_name=project_name,
        type=type_value,
        description=description,
        item_id=item_id if type_value == "artefact" and item_id else None,
    )
    db.session.add(research)
    db.session.flush()

    # Parse and create stages
    try:
        stages_data = json.loads(stages_json)
        for idx, stage_data in enumerate(stages_data, 1):
            stage = ResearchStage(
                research_id=research.id,
                stage_number=idx,
                name=stage_data["name"],
                description=stage_data.get("description", ""),
            )
            db.session.add(stage)
            db.session.flush()
            for req_data in stage_data.get("unlock_requirements", []):
                requirement = ResearchStageRequirement(
                    stage_id=stage.id,
                    requirement_type=req_data["requirement_type"],
                    science_type=req_data.get("science_type"),
                    item_type=req_data.get("item_type"),
                    exotic_substance_id=req_data.get("exotic_type"),
                    amount=req_data["amount"],
                )
                if req_data["requirement_type"] == "sample":
                    sample_tag_name = req_data.get("sample_tag")
                    if sample_tag_name:
                        tag = SampleTag.query.filter_by(name=sample_tag_name).first()
                        if not tag:
                            tag = SampleTag(name=sample_tag_name)
                            db.session.add(tag)
                            db.session.flush()
                        requirement.sample_tag = tag.name
                    requirement.requires_researched = req_data.get("requires_researched", False)
                db.session.add(requirement)
    except json.JSONDecodeError:
        flash("Invalid stages data format.", "error")
        return redirect(url_for("research.research_create"))

    db.session.commit()
    flash("Research project created successfully.", "success")
    return redirect(url_for("research.research_list"))


@research_bp.route("/<int:research_id>/edit", methods=["GET"])
@login_required
@rules_team_required
def research_edit(research_id):
    research = Research.query.get_or_404(research_id)
    items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
    blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
    item_types = ItemType.query.order_by(ItemType.name).all()
    exotics = ExoticSubstance.query.order_by(ExoticSubstance.name).all()
    sample_tags = SampleTag.query.order_by(SampleTag.name).all()
    return render_template(
        "research/edit.html",
        research=research,
        items=items,
        blueprints=blueprints,
        item_types=item_types,
        exotics=exotics,
        sample_tags=sample_tags,
        ResearchType=ResearchType,
        ScienceType=ScienceType,
        ResearchRequirementType=ResearchRequirementType,
    )


@research_bp.route("/<int:research_id>/edit", methods=["POST"])
@login_required
@rules_team_required
def research_edit_post(research_id):
    research = Research.query.get_or_404(research_id)
    description = request.form.get("description")
    artefact_option = request.form.get("artefact_option")
    stages_json = request.form.get("stages_json", "[]")
    item_id = None
    if research.type.value == "artefact":
        if artefact_option == "existing":
            item_id = request.form.get("item_id") or None
        elif artefact_option == "new":
            item_type_id = request.form.get("item_type_id")
            if not item_type_id:
                flash(
                    "You must select an item type to create a new artefact item.",
                    "error",
                )
                items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()
                blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()
                item_types = ItemType.query.order_by(ItemType.name).all()
                return render_template(
                    "research/edit.html",
                    research=research,
                    items=items,
                    blueprints=blueprints,
                    item_types=item_types,
                    ResearchType=ResearchType,
                    ScienceType=ScienceType,
                    ResearchRequirementType=ResearchRequirementType,
                )
            max_blueprint = (
                ItemBlueprint.query.filter_by(item_type_id=item_type_id)
                .order_by(ItemBlueprint.blueprint_id.desc())
                .first()
            )
            next_blueprint_id = (max_blueprint.blueprint_id + 1) if max_blueprint else 1
            new_blueprint = ItemBlueprint(
                name=research.project_name,
                item_type_id=item_type_id,
                blueprint_id=next_blueprint_id,
                base_cost=0,
            )
            db.session.add(new_blueprint)
            db.session.flush()
            max_item = (
                Item.query.filter_by(blueprint_id=new_blueprint.id)
                .order_by(Item.item_id.desc())
                .first()
            )
            next_item_id = (max_item.item_id + 1) if max_item else 1
            new_item = Item(blueprint_id=new_blueprint.id, item_id=next_item_id)
            db.session.add(new_item)
            db.session.flush()
            item_id = new_item.id
    research.description = description
    research.item_id = item_id if research.type.value == "artefact" and item_id else None

    # Load all existing stages, ordered by stage_number
    existing_stages = list(
        ResearchStage.query.filter_by(research_id=research.id)
        .order_by(ResearchStage.stage_number)
        .all()
    )
    existing_stage_count = len(existing_stages)

    # Parse new stages data
    try:
        stages_data = json.loads(stages_json)
    except json.JSONDecodeError:
        flash("Invalid stages data format.", "error")
        return redirect(url_for("research.research_edit", research_id=research.id))

    new_stage_count = len(stages_data)

    # 1. Update or add stages
    for idx, stage_data in enumerate(stages_data, 1):
        if idx <= existing_stage_count:
            # Update existing stage
            stage = existing_stages[idx - 1]
            stage.name = stage_data["name"]
            stage.description = stage_data.get("description", "")
            stage.stage_number = idx
            # Update requirements
            # Remove requirements not present in new data
            new_reqs_data = stage_data.get("unlock_requirements", [])
            existing_reqs = {
                (
                    r.requirement_type.value,
                    getattr(r, "science_type", None) and r.science_type.value,
                    r.item_type,
                    r.sample_tag,
                    r.requires_researched,
                    r.amount,
                ): r
                for r in stage.unlock_requirements
            }
            new_reqs_keys = set()
            for req_data in new_reqs_data:
                key = (
                    req_data["requirement_type"],
                    req_data.get("science_type"),
                    req_data.get("item_type"),
                    req_data.get("exotic_type"),
                    req_data.get("sample_tag"),
                    req_data.get("requires_researched", False),
                    req_data["amount"],
                )
                new_reqs_keys.add(key)
                if key not in existing_reqs:
                    # Add new requirement
                    requirement = ResearchStageRequirement(
                        stage_id=stage.id,
                        requirement_type=req_data["requirement_type"],
                        science_type=req_data.get("science_type"),
                        exotic_substance_id=req_data.get("exotic_type"),
                        item_type=req_data.get("item_type"),
                        amount=req_data["amount"],
                    )
                    if req_data["requirement_type"] == "sample":
                        sample_tag_name = req_data.get("sample_tag")
                        if sample_tag_name:
                            tag = SampleTag.query.filter_by(name=sample_tag_name).first()
                            if not tag:
                                tag = SampleTag(name=sample_tag_name)
                                db.session.add(tag)
                                db.session.flush()
                            requirement.sample_tag = tag.name
                        requirement.requires_researched = req_data.get("requires_researched", False)
                    db.session.add(requirement)
            # Remove requirements not in new data
            for key, req in existing_reqs.items():
                if key not in new_reqs_keys:
                    # Remove any CharacterResearchStageRequirement referencing this
                    # requirement
                    for crsr in req.character_progress:
                        db.session.delete(crsr)
                    db.session.delete(req)
            # --- Preserve/adjust player progress for this stage ---
            for crs in stage.character_progress:
                # Map: requirement_id -> CharacterResearchStageRequirement
                existing_crsr = {crsr.requirement_id: crsr for crsr in crs.requirement_progress}
                # Map: requirement_id for all current requirements
                current_req_ids = {req.id for req in stage.unlock_requirements}
                # Add new CharacterResearchStageRequirement for new requirements
                for req in stage.unlock_requirements:
                    if req.id not in existing_crsr:
                        new_crsr = CharacterResearchStageRequirement(
                            character_research_stage_id=crs.id,
                            requirement_id=req.id,
                            progress=0,
                        )
                        db.session.add(new_crsr)
                # Remove CharacterResearchStageRequirement for deleted requirements
                for req_id, crsr in existing_crsr.items():
                    if req_id not in current_req_ids:
                        db.session.delete(crsr)
        else:
            # Add new stage
            stage = ResearchStage(
                research_id=research.id,
                stage_number=idx,
                name=stage_data["name"],
                description=stage_data.get("description", ""),
            )
            db.session.add(stage)
            db.session.flush()
            for req_data in stage_data.get("unlock_requirements", []):
                requirement = ResearchStageRequirement(
                    stage_id=stage.id,
                    requirement_type=req_data["requirement_type"],
                    science_type=req_data.get("science_type"),
                    item_type=req_data.get("item_type"),
                    exotic_substance_id=req_data.get("exotic_type"),
                    amount=req_data["amount"],
                )
                if req_data["requirement_type"] == "sample":
                    sample_tag_name = req_data.get("sample_tag")
                    if sample_tag_name:
                        tag = SampleTag.query.filter_by(name=sample_tag_name).first()
                        if not tag:
                            tag = SampleTag(name=sample_tag_name)
                            db.session.add(tag)
                            db.session.flush()
                        requirement.sample_tag = tag.name
                    requirement.requires_researched = req_data.get("requires_researched", False)
                db.session.add(requirement)

    # 2. Delete excess stages (and their requirements and character progress)
    if existing_stage_count > new_stage_count:
        for stage in existing_stages[new_stage_count:]:
            # Remove any CharacterResearchStage referencing this stage
            for crs in stage.character_progress:
                # Remove CharacterResearchStageRequirement for this stage
                for crsr in crs.requirement_progress:
                    db.session.delete(crsr)
                db.session.delete(crs)
            # Remove requirements
            for req in stage.unlock_requirements:
                for crsr in req.character_progress:
                    db.session.delete(crsr)
                db.session.delete(req)
            db.session.delete(stage)
    db.session.flush()

    db.session.commit()
    flash("Research project updated successfully.", "success")
    return redirect(url_for("research.research_list"))


@research_bp.route("/api/blueprints")
@login_required
@rules_team_required
def api_blueprints():
    q = request.args.get("q", "").strip().lower()
    query = ItemBlueprint.query
    if q:
        query = query.filter(ItemBlueprint.name.ilike(f"%{q}%"))
    blueprints = query.order_by(ItemBlueprint.name).limit(20).all()
    results = [
        {
            "id": bp.id,
            "text": f"{bp.name} ({bp.item_type.id_prefix}{bp.blueprint_id:04d})",
        }
        for bp in blueprints
    ]
    return jsonify({"results": results})


@research_bp.route("/api/exotics")
@login_required
@rules_team_required
def api_exotics():
    q = request.args.get("q", "").strip().lower()
    query = ExoticSubstance.query
    if q:
        query = query.filter(ExoticSubstance.name.ilike(f"%{q}%"))
    exotics = query.order_by(ExoticSubstance.name).limit(20).all()
    results = [{"id": ex.id, "text": ex.name} for ex in exotics]
    return jsonify({"results": results})


@research_bp.route("/<int:research_id>/assignees")
@login_required
@rules_team_required
def assignees(research_id):
    research = Research.query.get_or_404(research_id)
    if not research.stages:
        flash("Cannot assign characters to research without stages", "error")
        return redirect(url_for("research.research_list"))

    # Get current assignees with their progress
    assignees = CharacterResearch.query.filter_by(research_id=research_id).all()

    # Calculate progress percent for each assignee
    for assignee in assignees:
        assignee.current_stage_progress = assignee.get_current_stage()

    # Get available characters (those not already assigned)
    assigned_character_ids = [a.character_id for a in assignees]
    available_characters = Character.query.filter(
        ~Character.id.in_(assigned_character_ids), Character.status == "active"
    ).all()

    return render_template(
        "research/assignees.html",
        research=research,
        assignees=assignees,
        available_characters=available_characters,
    )


@research_bp.route("/<int:research_id>/assignees/add", methods=["POST"])
@login_required
@rules_team_required
def add_assignee(research_id):
    research = Research.query.get_or_404(research_id)
    if not research.stages:
        flash("Cannot assign characters to research without stages", "error")
        return redirect(url_for("research.research_list"))

    character_id = request.form.get("character_id")
    if not character_id:
        flash("No character selected", "error")
        return redirect(url_for("research.assignees", research_id=research_id))

    # Only allow active characters
    character = db.session.get(Character, character_id)
    if not character or character.status != "active":
        flash("Only active characters can be assigned to research.", "error")
        return redirect(url_for("research.assignees", research_id=research_id))

    # Check if character is already assigned
    existing = CharacterResearch.query.filter_by(
        research_id=research_id, character_id=character_id
    ).first()

    if existing:
        flash("Character is already assigned to this research", "error")
        return redirect(url_for("research.assignees", research_id=research_id))

    # Assign character to research
    research.assign_character(character_id)
    db.session.commit()

    flash("Character assigned to research successfully", "success")
    return redirect(url_for("research.assignees", research_id=research_id))


@research_bp.route("/<int:research_id>/assignees/<int:character_id>/remove", methods=["POST"])
@login_required
@rules_team_required
def remove_assignee(research_id, character_id):
    character_research = CharacterResearch.query.filter_by(
        research_id=research_id, character_id=character_id
    ).first_or_404()

    db.session.delete(character_research)
    db.session.commit()

    flash("Character removed from research successfully", "success")
    return redirect(url_for("research.assignees", research_id=research_id))


@research_bp.route("/<int:research_id>/assignees/<int:character_id>/progress", methods=["GET"])
@login_required
@rules_team_required
def edit_progress(research_id, character_id):
    character_research = CharacterResearch.query.filter_by(
        research_id=research_id, character_id=character_id
    ).first_or_404()

    # Get the current stage progress
    current_stage = character_research.get_current_stage()

    item_types = {str(item.id): item.name for item in ItemType.query.all()}
    exotics = {substance.id: substance.name for substance in ExoticSubstance.query.all()}
    return render_template(
        "research/edit_progress.html",
        research=character_research.research,
        character=character_research.character,
        character_research=character_research,
        current_stage=current_stage,
        item_types=item_types,
        exotics=exotics,
        ResearchRequirementType=ResearchRequirementType,
        ScienceType=ScienceType,
    )


@research_bp.route("/<int:research_id>/assignees/<int:character_id>/progress", methods=["POST"])
@login_required
@rules_team_required
def edit_progress_post(research_id, character_id):
    character_research = CharacterResearch.query.filter_by(
        research_id=research_id, character_id=character_id
    ).first_or_404()

    # Get the current stage progress
    current_stage = character_research.get_current_stage()

    # Handle stage progression if requested
    if request.form.get("advance_stage"):
        character_research.advance_stage()
        db.session.commit()
        flash("Research progress advanced successfully", "success")
        return redirect(
            url_for(
                "research.edit_progress",
                research_id=research_id,
                character_id=character_id,
            )
        )

    elif request.form.get("regress_stage"):
        character_research.regress_stage()
        db.session.commit()
        flash("Research progress regressed successfully", "success")
        return redirect(
            url_for(
                "research.edit_progress",
                research_id=research_id,
                character_id=character_id,
            )
        )

    # Update requirement progress
    for req in current_stage.requirement_progress:
        progress = request.form.get(f"requirement_{req.id}")
        if progress is not None:
            req.progress = int(progress)

    db.session.commit()
    flash("Research progress updated successfully", "success")
    return redirect(url_for("research.assignees", research_id=research_id))


@research_bp.route("/project_info", methods=["GET"])
@login_required
def project_info():
    public_id = request.args.get("project_id", type=str)
    target_id = request.args.get("character_id", type=str)

    if not public_id:
        return jsonify({"found": False, "error": "Missing project_id"}), 400

    project = Research.query.filter_by(public_id=public_id).first()
    if not project:
        return jsonify({"found": False, "error": "Project not found"}), 404

    result = research_to_dict(project)
    result["valid"] = False

    if target_id:
        # Parse user_id.character_id
        if "." in target_id:
            try:
                user_id_str, char_id_str = target_id.split(".")
                user_id = int(user_id_str)
                char_id = int(char_id_str)
            except Exception:
                result["error"] = "Invalid character ID format."
                return jsonify(result)
            cr = CharacterResearch.query.filter_by(
                research_id=project.id, character_id=char_id
            ).first()
            if cr and cr.character.user_id == user_id:
                result["valid"] = True
                result["character_name"] = cr.character.name
                current_stage = cr.get_current_stage()
                if current_stage:
                    result["stage_requirements"] = [
                        req_to_dict(req) for req in current_stage.stage.unlock_requirements
                    ]
            else:
                # If the character is the current user or a downtime_team user, allow
                # access
                char = db.session.get(Character, char_id)
                if (
                    char
                    and char.user_id == user_id
                    and (
                        char.user_id == current_user.id
                        or current_user.has_role(Role.DOWNTIME_TEAM.value)
                    )
                ):
                    result["valid"] = True
                    result["character_name"] = char.name
                    # If not assigned to project yet, use first stage requirements
                    if not cr:
                        first_stage = (
                            ResearchStage.query.filter_by(research_id=project.id)
                            .order_by(ResearchStage.stage_number)
                            .first()
                        )
                        if first_stage:
                            result["stage_requirements"] = [
                                req_to_dict(req) for req in first_stage.unlock_requirements
                            ]
                    else:
                        # If assigned, use current stage requirements
                        current_stage = cr.get_current_stage()
                        if current_stage:
                            result["stage_requirements"] = [
                                req_to_dict(req) for req in current_stage.stage.unlock_requirements
                            ]
                else:
                    result["error"] = "Character not assigned to this project or user ID mismatch."
        else:
            result["error"] = "Invalid character ID format."
    return jsonify(result)


@research_bp.route("/can_teach_character", methods=["GET"])
@login_required
def can_teach_character():
    """Check if a character can be taught a project by another character"""
    project_id = request.args.get("project_id")
    character_id = request.args.get("character_id")
    teaching_character_id = request.args.get("teaching_character_id")

    if not all([project_id, character_id, teaching_character_id]):
        return jsonify(
            {
                "found": False,
                "valid": False,
                "error": "Missing required parameters",
                "project_id": None,
                "project_name": None,
                "assignees": [],
                "character_name": None,
                "stage_requirements": [],
            }
        )

    # Get the project
    project = Research.query.filter_by(public_id=project_id).first()
    if not project:
        return jsonify(
            {
                "found": False,
                "valid": False,
                "error": "Project not found",
                "project_id": None,
                "project_name": None,
                "assignees": [],
                "character_name": None,
                "stage_requirements": [],
            }
        )

    # Get the teaching character's research
    teaching_research = CharacterResearch.query.filter_by(
        character_id=teaching_character_id, research_id=project.id
    ).first()

    if not teaching_research:
        return jsonify(
            {
                "found": True,
                "valid": False,
                "error": "Teaching character is not assigned to this project",
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": None,
                "stage_requirements": [],
            }
        )

    # Get the teaching character's completed stages
    teaching_stages = CharacterResearchStage.query.filter_by(
        character_research_id=teaching_research.id, stage_completed=True
    ).all()

    if not teaching_stages:
        return jsonify(
            {
                "found": True,
                "valid": False,
                "error": ("Teaching character has not completed any stages of this project"),
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": teaching_research.character.name,
                "stage_requirements": [],
            }
        )

    # Get the target character
    if "." in character_id:
        try:
            user_id_str, char_id_str = character_id.split(".")
            user_id = int(user_id_str)
            char_id = int(char_id_str)
        except Exception:
            return jsonify(
                {
                    "found": False,
                    "valid": False,
                    "error": "Invalid character ID format.",
                }
            )

    target_character = Character.query.filter_by(user_id=user_id, character_id=char_id).first()
    if not target_character:
        return jsonify(
            {
                "found": True,
                "valid": False,
                "error": "Target character not found",
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": None,
                "stage_requirements": [],
            }
        )

    # Get the target character's research
    target_research = CharacterResearch.query.filter_by(
        character_id=character_id, research_id=project.id
    ).first()

    if not target_research:
        # Check if teaching character has completed the first stage
        first_stage = (
            ResearchStage.query.filter_by(research_id=project.id)
            .order_by(ResearchStage.stage_number)
            .first()
        )
        if not first_stage:
            return jsonify(
                {
                    "found": True,
                    "valid": False,
                    "error": "Project has no stages",
                    "project_id": project.public_id,
                    "project_name": project.project_name,
                    "assignees": [
                        {
                            "character_id": cr.character_id,
                            "character_name": cr.character.name,
                            "user_id": cr.character.user_id,
                            "current_stage_id": cr.current_stage_id,
                            "character_research_id": cr.id,
                        }
                        for cr in project.character_research
                    ],
                    "character_name": target_character.name,
                    "stage_requirements": [],
                }
            )

        teaching_first_stage = CharacterResearchStage.query.filter_by(
            character_research_id=teaching_research.id,
            stage_id=first_stage.id,
            stage_completed=True,
        ).first()

        if not teaching_first_stage:
            return jsonify(
                {
                    "found": True,
                    "valid": False,
                    "error": "Teaching character has not completed the first stage",
                    "project_id": project.public_id,
                    "project_name": project.project_name,
                    "assignees": [
                        {
                            "character_id": cr.character_id,
                            "character_name": cr.character.name,
                            "user_id": cr.character.user_id,
                            "current_stage_id": cr.current_stage_id,
                            "character_research_id": cr.id,
                        }
                        for cr in project.character_research
                    ],
                    "character_name": target_character.name,
                    "stage_requirements": [],
                }
            )

        return jsonify(
            {
                "found": True,
                "valid": True,
                "message": "Target character can be taught this project",
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": target_character.name,
                "stage_requirements": [],
            }
        )

    # Get the target character's current stage
    target_current_stage = target_research.get_current_stage()
    if not target_current_stage:
        return jsonify(
            {
                "found": True,
                "valid": False,
                "error": "Target character has no current stage",
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": target_character.name,
                "stage_requirements": [],
            }
        )

    # Check if teaching character has completed this stage
    teaching_stage = CharacterResearchStage.query.filter_by(
        character_research_id=teaching_research.id,
        stage_id=target_current_stage.stage_id,
        stage_completed=True,
    ).first()

    if not teaching_stage:
        return jsonify(
            {
                "found": True,
                "valid": False,
                "error": "Teaching character has not completed this stage",
                "project_id": project.public_id,
                "project_name": project.project_name,
                "assignees": [
                    {
                        "character_id": cr.character_id,
                        "character_name": cr.character.name,
                        "user_id": cr.character.user_id,
                        "current_stage_id": cr.current_stage_id,
                        "character_research_id": cr.id,
                    }
                    for cr in project.character_research
                ],
                "character_name": target_character.name,
                "stage_requirements": [],
            }
        )

    return jsonify(
        {
            "found": True,
            "valid": True,
            "message": "Target character can be taught this project",
            "project_id": project.public_id,
            "project_name": project.project_name,
            "assignees": [
                {
                    "character_id": cr.character_id,
                    "character_name": cr.character.name,
                    "user_id": cr.character.user_id,
                    "current_stage_id": cr.current_stage_id,
                    "character_research_id": cr.id,
                }
                for cr in project.character_research
            ],
            "character_name": target_character.name,
            "stage_requirements": [],
        }
    )


@research_bp.route("/view")
@login_required
def view_research_list():
    """Display a view-only list of research projects for the user's characters."""
    # Get all research projects assigned to the user's characters
    user_research = (
        CharacterResearch.query.join(Character).filter(Character.user_id == current_user.id).all()
    )

    # Group research by character
    research_by_character = {}
    for cr in user_research:
        if cr.character not in research_by_character:
            research_by_character[cr.character] = []
        research_by_character[cr.character].append(cr)

    return render_template("research/view_list.html", research_by_character=research_by_character)


@research_bp.route("/view/<int:research_id>")
@login_required
def view_research_project(research_id):
    """Display a view-only page for a specific research project."""
    # Get the research project
    research = Research.query.get_or_404(research_id)

    # Get the user's character's research for this project
    character_research = (
        CharacterResearch.query.join(Character)
        .filter(
            CharacterResearch.research_id == research_id,
            Character.user_id == current_user.id,
        )
        .first_or_404()
    )

    # Get the current stage progress
    current_stage = None
    if character_research.current_stage_id is not None:
        current_stage = CharacterResearchStage.query.filter_by(
            character_research_id=character_research.id,
            stage_id=character_research.current_stage_id,
        ).first()

    # Get all stages and their progress
    stages = []
    for stage in research.stages:
        stage_progress = CharacterResearchStage.query.filter_by(
            character_research_id=character_research.id, stage_id=stage.id
        ).first()
        stages.append({"stage": stage, "progress": stage_progress})

    return render_template(
        "research/view_project.html",
        research=research,
        character_research=character_research,
        current_stage=current_stage,
        stages=stages,
        ResearchRequirementType=ResearchRequirementType,
        ScienceType=ScienceType,
    )
