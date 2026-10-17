from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.skills import Skill, id_listed
from models.enums import CharacterAuditAction, CharacterStatus
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog, CharacterSkill, _skill_name_list
from models.tools.user import User
from utils.decorators import character_owner_or_user_admin_required, email_verified_required
from utils.permission_decorators import permission_required

character_skills_bp = Blueprint("character_skills", __name__)


def _viewer_can_refund(character):
    if current_user.has_permission("character.refund") or current_user.has_permission(
        "character.edit_all"
    ):
        return True
    return character.status == CharacterStatus.DEVELOPING.value


def _available_skills(character):
    """Skills this character can see, including ones they already own."""
    all_skills = Skill.query.all()
    available_skills = []
    character_skill_ids = {cs.skill_id for cs in character.skills}

    for skill in all_skills:
        if skill.id in character_skill_ids:
            available_skills.append(skill)
            continue

        if skill.required_skill_id and skill.required_skill_id not in character_skill_ids:
            continue

        if character.skill_requirement_error(skill):
            continue

        if character.skill_ban_reason(skill):
            continue

        if skill.required_factions and not id_listed(
            skill.required_factions_list, character.faction_id
        ):
            continue

        if skill.required_species and not id_listed(
            skill.required_species_list, character.species_id
        ):
            continue

        available_skills.append(skill)

    return available_skills


def _skill_spend_payload(character, skills, can_refund):
    """Data the page uses to preview spends without posting each rank."""
    owner = User.query.get(character.user_id)
    owned = {row.skill_id: row for row in character.skills}
    payload = []
    for skill in skills:
        row = owned.get(skill.id)
        any_ids = skill.required_any_skills_list
        distinct_ids = skill.distinct_requirements_list
        payload.append(
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description or "",
                "baseCost": skill.base_cost,
                "multiple": bool(skill.can_purchase_multiple),
                "costIncreases": bool(skill.cost_increases),
                "earnedOnly": bool(skill.earned_points_only),
                "discount": character.skill_discount(skill),
                "freeRanks": (row.free_ranks or 0) if row else 0,
                "owned": row.times_purchased if row else 0,
                "rankLimit": character.maximum_rank(skill),
                "requiredSkillId": skill.required_skill_id,
                "requiredSkillName": skill.required_skill.name if skill.required_skill else "",
                "requiredAny": any_ids,
                "requiredAnyNames": _skill_name_list(any_ids) if any_ids else "",
                "distinct": distinct_ids,
                "distinctNames": _skill_name_list(distinct_ids) if distinct_ids else "",
            }
        )
    return {
        "basePoints": character.base_character_points,
        "userPoints": owner.character_points if owner else 0,
        "developing": character.status == CharacterStatus.DEVELOPING.value,
        "canRefund": can_refund,
        "skills": payload,
    }


def _parse_rank_changes(character, available_skills):
    """Desired ranks that differ from what the character owns now."""
    by_id = {skill.id: skill for skill in available_skills}
    owned = {
        row.skill_id: row.times_purchased
        for row in CharacterSkill.query.filter_by(character_id=character.id).all()
    }
    changes = {}
    for key, raw in request.form.items():
        if not key.startswith("rank_"):
            continue
        try:
            skill_id = int(key.removeprefix("rank_"))
            value = int(raw)
        except ValueError:
            return None, "Skill ranks must be whole numbers."
        skill = by_id.get(skill_id)
        if skill is None:
            return None, "Invalid skill selection."
        if value < 0:
            return None, "Skill ranks cannot be negative."
        if not skill.can_purchase_multiple and value > 1:
            return None, f"{skill.name} can only be purchased once."
        limit = character.maximum_rank(skill)
        if limit is not None and value > limit:
            return None, f"Maximum {limit} ranks"
        if value != owned.get(skill_id, 0):
            changes[skill_id] = value
    return changes, None


def _refund_block(character, skill):
    """Why this skill cannot lose a rank, matching the single-refund route."""
    rows = CharacterSkill.query.filter_by(character_id=character.id).all()
    for row in rows:
        if row.skill_id == skill.id or not row.times_purchased:
            continue
        if row.skill.required_skill_id == skill.id:
            return f"Cannot refund {skill.name} as it is required for {row.skill.name}."
    return character.skill_refund_error(skill)


def _times_purchased(character_id, skill_id):
    row = CharacterSkill.query.filter_by(character_id=character_id, skill_id=skill_id).first()
    return row.times_purchased if row else 0


def _audit_skill_change(character, changes):
    db.session.add(
        CharacterAuditLog(
            character_id=character.id,
            editor_user_id=current_user.id,
            action=CharacterAuditAction.SKILL_CHANGE.value,
            changes=changes,
        )
    )


def _apply_skill_changes(character, changes):
    """Buy and refund until every chosen rank is reached. Raises ValueError on failure."""
    skills = {skill.id: skill for skill in Skill.query.filter(Skill.id.in_(changes)).all()}
    reason = None

    def step_refunds():
        nonlocal reason
        for skill_id, desired in changes.items():
            if _times_purchased(character.id, skill_id) <= desired:
                continue
            skill = skills.get(skill_id)
            if skill is None:
                raise ValueError("Invalid skill selection.")
            db.session.expire(character, ["skills"])
            block = _refund_block(character, skill)
            if block:
                reason = block
                continue
            before = _times_purchased(character.id, skill_id)
            character.refund_skill(skill, current_user, commit=False)
            after = _times_purchased(character.id, skill_id)
            if after >= before:
                raise ValueError(reason or "Could not apply skill changes.")
            if after == 0:
                message = f"Skill refunded: {skill.name} (removed entirely)"
            else:
                message = f"Skill refunded: {skill.name} (Level {after})"
            _audit_skill_change(character, message)
            return True
        return False

    def step_purchases():
        nonlocal reason
        for skill_id, desired in changes.items():
            if _times_purchased(character.id, skill_id) >= desired:
                continue
            skill = skills.get(skill_id)
            if skill is None:
                raise ValueError("Invalid skill selection.")
            db.session.expire(character, ["skills"])
            allowed, error = character.can_purchase_skill(skill, current_user)
            if not allowed:
                reason = error
                continue
            before = _times_purchased(character.id, skill_id)
            character.purchase_skill(skill, current_user, commit=False)
            after = _times_purchased(character.id, skill_id)
            if after <= before:
                raise ValueError(reason or "Could not apply skill changes.")
            _audit_skill_change(character, f"Skill purchased: {skill.name} (Level {after})")
            return True
        return False

    def needs(compare):
        return any(
            compare(_times_purchased(character.id, skill_id), desired)
            for skill_id, desired in changes.items()
        )

    limit = (
        sum(
            abs(desired - _times_purchased(character.id, skill_id))
            for skill_id, desired in changes.items()
        )
        + len(changes)
        + 5
    )
    steps = 0
    while needs(lambda current, desired: current > desired):
        steps += 1
        if steps > limit or not step_refunds():
            raise ValueError(reason or "Could not apply skill changes.")
    while needs(lambda current, desired: current < desired):
        steps += 1
        if steps > limit or not step_purchases():
            raise ValueError(reason or "Could not apply skill changes.")
    for skill_id, desired in changes.items():
        if _times_purchased(character.id, skill_id) != desired:
            raise ValueError(reason or "Could not apply skill changes.")


def _save_skill_ranks(character, available_skills):
    changes, error = _parse_rank_changes(character, available_skills)
    if error:
        flash(error, "error")
        return redirect(url_for("character_skills.character_skills", character_id=character.id))
    if not changes:
        return redirect(url_for("character_skills.character_skills", character_id=character.id))

    owned = {
        row.skill_id: row.times_purchased
        for row in CharacterSkill.query.filter_by(character_id=character.id).all()
    }
    if any(value < owned.get(skill_id, 0) for skill_id, value in changes.items()):
        if not _viewer_can_refund(character):
            flash(
                "Only users with refund permission can refund skills for "
                "non-developing characters.",
                "error",
            )
            return redirect(url_for("character_skills.character_skills", character_id=character.id))

    character_id = character.id
    try:
        # Savepoint so a rejected spend undoes only these skill changes.
        with db.session.begin_nested():
            _apply_skill_changes(character, changes)
        db.session.commit()
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"Error saving skills: {exc}", "error")
    else:
        flash("Skill changes saved.", "success")
    return redirect(url_for("character_skills.character_skills", character_id=character_id))


@character_skills_bp.route("/characters/<int:character_id>/skills", methods=["GET", "POST"])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def character_skills(character_id):
    character = Character.query.get_or_404(character_id)
    available_skills = _available_skills(character)
    if request.method == "POST":
        return _save_skill_ranks(character, available_skills)

    can_refund = _viewer_can_refund(character)
    return render_template(
        "character_skills/list.html",
        character=character,
        skills=available_skills,
        can_refund=can_refund,
        skill_spend=_skill_spend_payload(character, available_skills, can_refund),
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
    cp_from_user = (
        character.earned_points_spent(cost, skill.earned_points_only)
        - character.earned_points_spent()
    )

    points_error = character.skill_points_error(skill, current_user, cost)
    if points_error:
        return jsonify({"can_purchase": False, "reason": points_error})

    ban_reason = character.skill_ban_reason(skill)
    if ban_reason:
        return jsonify({"can_purchase": False, "reason": ban_reason})

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
        if not id_listed(required_factions, character.faction_id):
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
        if not id_listed(required_species, character.species_id):
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

    # Only allow users with refund permission or character edit permission to refund skills
    # for non-developing characters
    if not (
        current_user.has_permission("character.refund")
        or current_user.has_permission("character.edit_all")
    ):
        if character.status != CharacterStatus.DEVELOPING.value:
            flash(
                "Only users with refund permission can refund skills for "
                "non-developing characters.",
                "error",
            )
            return redirect(url_for("character_skills.character_skills", character_id=character_id))

    refund_error = character.skill_refund_error(skill)
    if refund_error:
        flash(refund_error, "error")
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
