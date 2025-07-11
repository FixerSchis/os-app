from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.skills import Skill
from models.enums import CharacterAuditAction, CharacterStatus
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog, CharacterSkill
from utils.decorators import (
    character_owner_or_user_admin_required,
    email_verified_required,
    user_admin_required,
)

character_skills_bp = Blueprint("character_skills", __name__)


@character_skills_bp.route("/characters/<int:character_id>/skills")
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def character_skills(character_id):
    character = Character.query.get_or_404(character_id)

    # Get all skills and filter out those the character cannot access
    all_skills = Skill.query.all()
    available_skills = []

    # First, get all skills the character already has
    character_skill_ids = {cs.skill_id for cs in character.skills}

    for skill in all_skills:
        # Skip if character already has this skill
        if skill.id in character_skill_ids:
            available_skills.append(skill)
            continue

        # Check required skill
        if skill.required_skill_id:
            if skill.required_skill_id not in character_skill_ids:
                continue

        # Check required factions
        if skill.required_factions:
            required_factions = skill.required_factions_list
            if str(character.faction_id) not in required_factions:
                continue

        # Check required species
        if skill.required_species:
            required_species = skill.required_species_list
            if str(character.species_id) not in required_species:
                continue

        # If we get here, the skill is available
        available_skills.append(skill)

    return render_template(
        "character_skills/list.html", character=character, skills=available_skills
    )


@character_skills_bp.route("/characters/<int:character_id>/skills/cost")
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def get_skill_cost(character_id):
    character = Character.query.get_or_404(character_id)

    skill_id = request.args.get("skill_id", type=int)
    if not skill_id:
        return jsonify({"error": "No skill selected"}), 400

    skill = Skill.query.get_or_404(skill_id)

    # Check if character already has this skill
    character_skill = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=skill.id
    ).first()

    if character_skill and not skill.can_purchase_multiple:
        return jsonify({"can_purchase": False, "reason": "This skill can only be purchased once"})

    # Check if character has enough CP
    cost = character.get_skill_cost(skill)
    total_skills_cost = character.get_total_skill_cost()
    remaining_base_cp = character.base_character_points - total_skills_cost
    cp_from_user = max(0, cost - remaining_base_cp)

    if character.status == CharacterStatus.ACTIVE.value and cp_from_user > 0:
        if not current_user.can_spend_character_points(cp_from_user):
            return jsonify(
                {
                    "can_purchase": False,
                    "reason": (f"Not enough character points (need {cp_from_user} from user)"),
                }
            )

    # Check required skill
    if skill.required_skill_id:
        required_skill = CharacterSkill.query.filter_by(
            character_id=character.id, skill_id=skill.required_skill_id
        ).first()
        if not required_skill:
            return jsonify(
                {
                    "can_purchase": False,
                    "reason": f"Requires {skill.required_skill.name}",
                }
            )

    # Check required factions
    if skill.required_factions:
        required_factions = skill.required_factions_list
        if str(character.faction_id) not in required_factions:
            # Get faction names for the error message
            faction_names = [
                f.name for f in Faction.query.filter(Faction.id.in_(required_factions)).all()
            ]
            return jsonify(
                {
                    "can_purchase": False,
                    "reason": f'Requires faction: {", ".join(faction_names)}',
                }
            )

    # Check required species
    if skill.required_species:
        required_species = skill.required_species_list
        if str(character.species_id) not in required_species:
            return jsonify(
                {
                    "can_purchase": False,
                    "reason": f'Requires species: {", ".join(required_species)}',
                }
            )

    return jsonify(
        {
            "can_purchase": True,
            "cost": cost,
            "base_cp_used": cost - cp_from_user,
            "user_cp_used": cp_from_user,
        }
    )


@character_skills_bp.route("/characters/<int:character_id>/skills/purchase", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def purchase_skill(character_id):
    character = Character.query.get_or_404(character_id)

    skill_id = request.form.get("skill_id", type=int)
    if not skill_id:
        flash("No skill selected.", "error")
        return redirect(url_for("character_skills.character_skills", character_id=character_id))

    skill = Skill.query.get_or_404(skill_id)

    try:
        # Get current skill level before purchase
        character_skill = CharacterSkill.query.filter_by(
            character_id=character.id, skill_id=skill.id
        ).first()
        current_level = character_skill.times_purchased if character_skill else 0

        # Purchase the skill
        character.purchase_skill(skill, current_user)

        new_level = current_level + 1
        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.SKILL_CHANGE.value,
            changes=f"Skill purchased: {skill.name} (Level {new_level})",
        )
        db.session.add(audit)

        db.session.commit()
        flash(f"Successfully purchased {skill.name}.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Error purchasing skill: {str(e)}", "error")

    return redirect(url_for("character_skills.character_skills", character_id=character_id))


@character_skills_bp.route("/characters/<int:character_id>/skills/refund", methods=["POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def refund_skill(character_id):
    character = Character.query.get_or_404(character_id)
    skill_id = request.form.get("skill_id", type=int)

    if not skill_id:
        flash("No skill selected.", "error")
        return redirect(url_for("character_skills.character_skills", character_id=character_id))

    skill = Skill.query.get_or_404(skill_id)

    # Only allow non-admins to refund skills for their own character if it's in development
    if not current_user.has_role("user_admin"):
        if character.status != CharacterStatus.DEVELOPING.value:
            flash("Only admins can refund skills for non-developing characters.", "error")
            return redirect(url_for("character_skills.character_skills", character_id=character_id))

    # Check if this skill is a prerequisite for any other skills the character has
    character_skills = CharacterSkill.query.filter_by(character_id=character.id).all()
    for character_skill in character_skills:
        if character_skill.skill.required_skill_id == skill_id:
            flash(
                f"Cannot refund {skill.name} as it is required for "
                f"{character_skill.skill.name}.",
                "error",
            )
            return redirect(url_for("character_skills.character_skills", character_id=character_id))

    try:
        # Get current skill level before refund
        character_skill = CharacterSkill.query.filter_by(
            character_id=character.id, skill_id=skill.id
        ).first()
        if not character_skill:
            flash("Character does not have this skill.", "error")
            return redirect(url_for("character_skills.character_skills", character_id=character_id))

        current_level = character_skill.times_purchased

        character.refund_skill(skill, current_user)

        new_level = current_level - 1
        if new_level == 0:
            changes = f"Skill refunded: {skill.name} (removed entirely)"
        else:
            changes = f"Skill refunded: {skill.name} (Level {new_level})"

        audit = CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.SKILL_CHANGE.value,
            changes=changes,
        )
        db.session.add(audit)

        db.session.commit()
        flash(f"Successfully refunded {skill.name}.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Error refunding skill: {str(e)}", "error")

    return redirect(url_for("character_skills.character_skills", character_id=character_id))
