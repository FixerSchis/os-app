from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models.extensions import db
from models.character import Character
from models.character import CharacterSkill
from models.database.skills import Skill
from models.enums import CharacterStatus, Role
from utils.decorators import email_verified_required, user_admin_required, character_owner_or_user_admin_required
from models.database.faction import Faction

character_skills_bp = Blueprint('character_skills', __name__)

@character_skills_bp.route('/characters/<int:character_id>/skills')
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
    
    return render_template('character_skills/list.html', 
                         character=character,
                         skills=available_skills)

@character_skills_bp.route('/characters/<int:character_id>/skills/cost')
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def get_skill_cost(character_id):
    character = Character.query.get_or_404(character_id)
    
    skill_id = request.args.get('skill_id', type=int)
    if not skill_id:
        return jsonify({'error': 'No skill selected'}), 400
        
    skill = Skill.query.get_or_404(skill_id)
    
    # Check if character already has this skill
    character_skill = CharacterSkill.query.filter_by(
        character_id=character.id,
        skill_id=skill.id
    ).first()
    
    if character_skill and not skill.can_purchase_multiple:
        return jsonify({
            'can_purchase': False,
            'reason': 'This skill can only be purchased once'
        })
    
    # Check if character has enough CP
    cost = character.get_skill_cost(skill)
    total_skills_cost = character.get_total_skill_cost()
    remaining_base_cp = character.base_character_points - total_skills_cost
    cp_from_user = max(0, cost - remaining_base_cp)
    
    if character.status == CharacterStatus.ACTIVE.value and cp_from_user > 0:
        if not current_user.can_spend_character_points(cp_from_user):
            return jsonify({
                'can_purchase': False,
                'reason': f'Not enough character points (need {cp_from_user} from user)'
            })
    
    # Check required skill
    if skill.required_skill_id:
        required_skill = CharacterSkill.query.filter_by(
            character_id=character.id,
            skill_id=skill.required_skill_id
        ).first()
        if not required_skill:
            return jsonify({
                'can_purchase': False,
                'reason': f'Requires {skill.required_skill.name}'
            })
    
    # Check required factions
    if skill.required_factions:
        required_factions = skill.required_factions_list
        if str(character.faction_id) not in required_factions:
            # Get faction names for the error message
            faction_names = [f.name for f in Faction.query.filter(Faction.id.in_(required_factions)).all()]
            return jsonify({
                'can_purchase': False,
                'reason': f'Requires faction: {", ".join(faction_names)}'
            })
    
    # Check required species
    if skill.required_species:
        required_species = skill.required_species_list
        if str(character.species_id) not in required_species:
            return jsonify({
                'can_purchase': False,
                'reason': f'Requires species: {", ".join(required_species)}'
            })
    
    return jsonify({
        'can_purchase': True,
        'cost': cost,
        'base_cp_used': cost - cp_from_user,
        'user_cp_used': cp_from_user
    })

@character_skills_bp.route('/characters/<int:character_id>/skills/purchase', methods=['POST'])
@login_required
@email_verified_required
@character_owner_or_user_admin_required
def purchase_skill(character_id):
    character = Character.query.get_or_404(character_id)
    
    skill_id = request.form.get('skill_id', type=int)
    if not skill_id:
        flash('No skill selected.', 'error')
        return redirect(url_for('character_skills.character_skills', character_id=character_id))
    
    skill = Skill.query.get_or_404(skill_id)
    
    try:
        # Purchase the skill
        character.purchase_skill(skill, current_user)
        db.session.commit()
        flash(f'Successfully purchased {skill.name}.', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error purchasing skill: {str(e)}', 'error')
    
    return redirect(url_for('character_skills.character_skills', character_id=character_id))

@character_skills_bp.route('/characters/<int:character_id>/skills/refund', methods=['POST'])
@login_required
@email_verified_required
@user_admin_required
def refund_skill(character_id):
    character = Character.query.get_or_404(character_id)
    skill_id = request.form.get('skill_id', type=int)
    
    if not skill_id:
        flash('No skill selected.', 'error')
        return redirect(url_for('character_skills.character_skills', character_id=character_id))
    
    skill = Skill.query.get_or_404(skill_id)
    
    # Check if this skill is a prerequisite for any other skills the character has
    character_skills = CharacterSkill.query.filter_by(character_id=character.id).all()
    for character_skill in character_skills:
        if character_skill.skill.required_skill_id == skill_id:
            flash(f'Cannot refund {skill.name} as it is required for {character_skill.skill.name}.', 'error')
            return redirect(url_for('character_skills.character_skills', character_id=character_id))
    
    try:
        character.refund_skill(skill, current_user)
        db.session.commit()
        flash(f'Successfully refunded {skill.name}.', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error refunding skill: {str(e)}', 'error')
    
    return redirect(url_for('character_skills.character_skills', character_id=character_id)) 