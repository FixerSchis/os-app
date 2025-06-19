from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.extensions import db
from models.character import Character, CharacterStatus, CharacterAuditLog, CharacterTag
from models.user import User
from models.database.species import Species
from models.database.faction import Faction
from models.character import assign_character_id
from models.enums import Role, CharacterAuditAction, PrintTemplateType
from utils.decorators import email_verified_required
from models.database.conditions import Condition
from models.database.cybernetic import Cybernetic, CharacterCybernetic
from models.research import CharacterResearch
from models.print_template import PrintTemplate
from flask import render_template_string
from utils import generate_qr_code, generate_web_qr_code
import re
import base64

characters_bp = Blueprint("characters", __name__)

@characters_bp.route("/")
@login_required
@email_verified_required
def character_list():
    if not current_user.is_authenticated:
        flash("Please log in to view characters.")
        return redirect(url_for("index"))
    
    characters = []
    if current_user.has_role(Role.USER_ADMIN.value):
        characters = Character.query.all()
    elif current_user.player_id:
        characters = Character.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        "characters/list.html",
        characters=characters,
        CharacterStatus=CharacterStatus,
        Faction=Faction
    )

@characters_bp.route("/new", methods=['GET'])
@login_required
@email_verified_required
def create_character():
    admin_context = request.args.get('admin_context') == '1'
    if not current_user.player_id:
        flash('You need a player ID to create characters', 'error')
        return redirect(url_for('characters.character_list'))
    factions = Faction.query.all()
    species_list = Species.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template('characters/edit.html', admin_context=admin_context, factions=factions, species_list=species_list, all_cybernetics=all_cybernetics)

@characters_bp.route("/new", methods=['POST'])
@login_required
@email_verified_required
def create_character_post():
    admin_context = request.form.get('admin_context') == '1'
    if not current_user.player_id:
        flash('You need a player ID to create characters', 'error')
        return redirect(url_for('characters.character_list'))
    name = request.form.get('name')
    pronouns_subject = request.form.get('pronouns_subject')
    pronouns_object = request.form.get('pronouns_object')
    faction_id = request.form.get('faction')
    species_id = request.form.get('species_id')
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    if not name or not faction_id or not species_id:
        flash('Character name, faction, and species are required', 'error')
        return render_template('characters/edit.html', admin_context=admin_context, factions=factions, species_list=species_list, all_cybernetics=all_cybernetics)
    
    faction = Faction.query.get(faction_id)
    if not faction:
        flash('Invalid faction selected', 'error')
        return render_template('characters/edit.html', admin_context=admin_context, factions=factions, species_list=species_list, all_cybernetics=all_cybernetics)
    
    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not current_user.has_role('npc'):
        flash('You do not have permission to select this faction.', 'error')
        return render_template('characters/edit.html', admin_context=admin_context, factions=factions, species_list=species_list, all_cybernetics=all_cybernetics)
    
    # Set base character points based on NPC role
    base_character_points = 30 if current_user.has_role('npc') else 10
    
    character = Character(
        user_id=current_user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id),
        base_character_points=base_character_points
    )
    db.session.add(character)
    db.session.commit()
    # Audit log for creation
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes="Character created"
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_role('user_admin'):
        selected_cyber_ids = request.form.getlist('cybernetic_ids[]')
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
    flash('Character created successfully!', 'success')
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/<int:character_id>/edit', methods=['GET'])
@login_required
@email_verified_required
def edit(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.args.get('admin_context') == '1'
    user_id = None
    if admin_context:
        user = User.query.filter_by(player_id=character.player_id).first()
        user_id = user.id if user else None
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    # Serialize all_conditions as a list of dicts for JSON
    all_conditions = []
    for cond in Condition.query.order_by(Condition.name).all():
        all_conditions.append({
            'id': cond.id,
            'name': cond.name,
            'stages': [
                {
                    'stage_number': stage.stage_number,
                    'rp_effect': stage.rp_effect,
                    'diagnosis': stage.diagnosis,
                    'cure': stage.cure,
                    'duration': stage.duration
                }
                for stage in sorted(cond.stages, key=lambda s: s.stage_number)
            ]
        })
    # Get research projects for this character
    research_projects = CharacterResearch.query.filter_by(character_id=character.id).all()
    for r in research_projects:
        r.current_stage_progress = None
        if r.current_stage_id is not None:
            r.current_stage_progress = next((p for p in r.progress if p.stage_id == r.current_stage_id), None)
    return render_template('characters/edit.html', character=character, admin_context=admin_context, user_id=user_id, factions=factions, species_list=species_list, all_conditions=all_conditions, all_cybernetics=all_cybernetics, research_projects=research_projects)

@characters_bp.route('/<int:character_id>/edit', methods=['POST'])
@login_required
@email_verified_required
def edit_post(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get('admin_context') == '1'
    user = User.query.filter_by(player_id=character.player_id).first() if admin_context else None
    if character.player_id != current_user.player_id and not current_user.has_role('user_admin'):
        flash('You do not have permission to edit this character', 'error')
        return redirect(url_for('characters.character_list'))
    
    name = request.form.get('name')
    pronouns_subject = request.form.get('pronouns_subject')
    pronouns_object = request.form.get('pronouns_object')
    faction_id = request.form.get('faction')
    species_id = request.form.get('species_id')
    species_list = Species.query.all()
    factions = Faction.query.all()
    
    if not name or not faction_id or not species_id:
        flash('Character name, faction, and species are required', 'error')
        return render_template('characters/edit.html', character=character, admin_context=admin_context, factions=factions, species_list=species_list)
    
    faction = Faction.query.get(faction_id)
    if not faction:
        flash('Invalid faction selected', 'error')
        return render_template('characters/edit.html', character=character, admin_context=admin_context, factions=factions, species_list=species_list)
    
    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not current_user.has_role('npc'):
        flash('You do not have permission to select this faction.', 'error')
        return render_template('characters/edit.html', character=character, admin_context=admin_context, factions=factions, species_list=species_list)
    
    character.name = name
    character.pronouns_subject = pronouns_subject
    character.pronouns_object = pronouns_object
    character.faction_id = faction_id
    character.species_id = species_id
    
    # --- Active Conditions Logic (user_admin only) ---
    from models.character import CharacterCondition
    if current_user.has_role('user_admin'):
        # Remove condition
        remove_condition_id = request.form.get('remove_condition')
        if remove_condition_id:
            cc = CharacterCondition.query.filter_by(id=remove_condition_id, character_id=character.id).first()
            if cc:
                db.session.delete(cc)
                db.session.commit()
                flash('Condition removed.', 'success')
                return redirect(url_for('characters.edit', character_id=character.id))
        # Add condition
        if request.form.get('add_condition'):
            cond_id = request.form.get('add_condition_id')
            stage = request.form.get('add_condition_stage')
            duration = request.form.get('add_condition_duration')
            if cond_id and stage and duration is not None:
                exists = CharacterCondition.query.filter_by(character_id=character.id, condition_id=cond_id).first()
                if not exists:
                    new_cc = CharacterCondition(
                        character_id=character.id,
                        condition_id=cond_id,
                        current_stage=stage,
                        current_duration=duration
                    )
                    db.session.add(new_cc)
                    db.session.commit()
                    flash('Condition added.', 'success')
                    return redirect(url_for('characters.edit', character_id=character.id))
        # Update existing conditions
        for cc in character.active_conditions:
            stage_val = request.form.get(f'active_condition_stage_{cc.id}')
            duration_val = request.form.get(f'active_condition_duration_{cc.id}')
            if stage_val is not None:
                cc.current_stage = int(stage_val)
            if duration_val is not None:
                cc.current_duration = int(duration_val)
        # Update cybernetics if user_admin
        selected_cyber_ids = request.form.getlist('cybernetic_ids[]')
        # Remove all current
        CharacterCybernetic.query.filter_by(character_id=character.id).delete()
        # Add new
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
    
    # Update faction reputations if user is admin
    if current_user.has_role('user_admin'):
        for faction in factions:
            reputation = request.form.get(f'reputation_{faction.id}')
            if reputation is not None:
                try:
                    reputation_value = int(reputation)
                    character.set_reputation(faction.id, reputation_value, current_user.id)
                except ValueError:
                    pass
        # Handle tag updates
        tag_ids = request.form.getlist('tag_ids[]')
        current_tags = set(tag.id for tag in character.tags)
        new_tags = set()
        for tag_id in tag_ids:
            if tag_id.isdigit():
                new_tags.add(int(tag_id))
            else:
                tag = CharacterTag.query.filter_by(name=tag_id).first()
                if not tag:
                    tag = CharacterTag(name=tag_id)
                    db.session.add(tag)
                    db.session.flush()
                new_tags.add(tag.id)
        for tag_id in current_tags - new_tags:
            tag = CharacterTag.query.get(tag_id)
            if tag:
                character.tags.remove(tag)
        for tag_id in new_tags - current_tags:
            tag = CharacterTag.query.get(tag_id)
            if tag and tag not in character.tags:
                character.tags.append(tag)
    db.session.commit()
    flash('Character updated successfully')
    if admin_context:
        return redirect(url_for('user_management.user_management_edit_user', user_id=user.id))
    return redirect(url_for('characters.character_list'))

def can_edit_character(character):
    return character.player_id == current_user.player_id or current_user.has_role('user_admin')

@characters_bp.route('/<int:character_id>/retire', methods=['POST'])
@login_required
@email_verified_required
def retire_character(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get('admin_context') == '1'
    if not can_edit_character(character):
        flash('You do not have permission to retire this character.', 'error')
        return redirect(url_for('characters.character_list'))
    if character.status != CharacterStatus.ACTIVE.value:
        flash('Only active characters can be retired.', 'error')
        return redirect(url_for('characters.character_list'))
    character.status = CharacterStatus.RETIRED.value
    db.session.commit()
    # Audit log for status change
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes="Retired character"
    )
    db.session.add(audit)
    db.session.commit()
    flash('Character retired.', 'success')
    if admin_context:
        user = User.query.filter_by(player_id=character.player_id).first()
        if user:
            return redirect(url_for('user_management.user_management_edit_user', user_id=user.id))
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/<int:character_id>/kill', methods=['POST'])
@login_required
@email_verified_required
def kill_character(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get('admin_context') == '1'
    if not current_user.has_role('user_admin'):
        flash('Only user admins can kill characters.', 'error')
        return redirect(url_for('characters.character_list'))
    if character.status != CharacterStatus.ACTIVE.value:
        flash('Only active characters can be killed.', 'error')
        return redirect(url_for('characters.character_list'))
    character.status = CharacterStatus.DEAD.value
    db.session.commit()
    flash('Character marked as dead.', 'success')
    if admin_context:
        user = User.query.filter_by(player_id=character.player_id).first()
        if user:
            return redirect(url_for('user_management.user_management_edit_user', user_id=user.id))
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/<int:character_id>/restore', methods=['POST'])
@login_required
@email_verified_required
def restore_character(character_id):
    character = Character.query.get_or_404(character_id)
    if not current_user.has_role('user_admin'):
        flash('Only user admins can restore characters.', 'error')
        return redirect(url_for('characters.character_list'))
    if character.status not in [CharacterStatus.RETIRED.value, CharacterStatus.DEAD.value]:
        flash('Only retired or dead characters can be restored.', 'error')
        return redirect(url_for('characters.character_list'))
    # Check if user has enough CP
    user = User.query.filter_by(player_id=character.player_id).first()
    if not user:
        flash('Could not find character owner.', 'error')
        return redirect(url_for('characters.character_list'))
    total_skill_cost = character.get_total_skill_cost()
    if total_skill_cost > character.base_character_points and not user.can_spend_character_points(total_skill_cost - character.base_character_points):
        flash('Not enough character points to restore character.', 'error')
        return redirect(url_for('characters.character_list'))
    # Assign character_id if not already set
    if character.character_id is None:
        character.character_id = assign_character_id(character.player_id)
    # Spend CP if needed
    if total_skill_cost > character.base_character_points:
        user.spend_character_points(total_skill_cost - character.base_character_points)
    character.status = CharacterStatus.ACTIVE.value
    db.session.commit()
    # Audit log for status change
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes=f"Restored character. Spent {total_skill_cost} character points on skills."
    )
    db.session.add(audit)
    db.session.commit()
    flash('Character restored and set to active.', 'success')
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/<int:character_id>/delete', methods=['POST'])
@login_required
@email_verified_required
def delete_character(character_id):
    character = Character.query.get_or_404(character_id)
    admin_context = request.form.get('admin_context') == '1'
    if not current_user.has_role('user_admin') and character.status != CharacterStatus.DEVELOPING.value:
        flash('Only developing characters can be deleted.', 'error')
        return redirect(url_for('characters.character_list'))
    if character.player_id != current_user.player_id and not current_user.has_role('user_admin'):
        flash('You do not have permission to delete this character.', 'error')
        return redirect(url_for('characters.character_list'))
    for audit_log in CharacterAuditLog.query.filter_by(character_id=character.id).all():
        db.session.delete(audit_log)
    db.session.delete(character)
    db.session.commit()
    flash('Character deleted.', 'success')
    if admin_context:
        user = User.query.filter_by(player_id=character.player_id).first()
        if user:
            return redirect(url_for('user_management.user_management_edit_user', user_id=user.id))
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/<int:character_id>/activate', methods=['POST'])
@login_required
@email_verified_required
def activate_character(character_id):
    character = Character.query.get_or_404(character_id)
    if character.player_id != current_user.player_id and not current_user.has_role('user_admin'):
        flash('You do not have permission to activate this character.', 'error')
        return redirect(url_for('characters.character_list'))
    if character.status != CharacterStatus.DEVELOPING.value:
        flash('Only developing characters can be activated.', 'error')
        return redirect(url_for('characters.character_list'))
    # Check if user has enough CP
    user = User.query.filter_by(player_id=character.player_id).first()
    if not user:
        flash('Could not find character owner.', 'error')
        return redirect(url_for('characters.character_list'))
    total_skill_cost = character.get_total_skill_cost()
    if total_skill_cost > character.base_character_points and not user.can_spend_character_points(total_skill_cost - character.base_character_points):
        flash('Not enough character points to activate character.', 'error')
        return redirect(url_for('characters.character_list'))
    # Assign character_id if not already set
    if character.character_id is None:
        character.character_id = assign_character_id(character.player_id)
    # Spend CP if needed
    if total_skill_cost > character.base_character_points:
        user.spend_character_points(total_skill_cost - character.base_character_points)
    # Activate character
    character.status = CharacterStatus.ACTIVE.value
    # Audit log for activation
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes=f"Character activated. Spent {total_skill_cost} character points on skills."
    )
    db.session.add(audit)
    db.session.commit()
    flash('Character activated successfully!', 'success')
    return redirect(url_for('characters.character_list'))

@characters_bp.route('/new/<int:player_id>', methods=['GET'])
@login_required
@email_verified_required
def create_for_player(player_id):
    if not current_user.has_role('user_admin'):
        flash('Only user admins can create characters for other players.', 'error')
        return redirect(url_for('characters.character_list'))
    user = User.query.filter_by(player_id=player_id).first()
    if not user:
        flash('Player not found.', 'error')
        return redirect(url_for('characters.character_list'))
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    return render_template('characters/edit.html', player_id=player_id, admin_context=True, factions=factions, user_id=user.id, species_list=species_list, all_cybernetics=all_cybernetics)

@characters_bp.route('/new/<int:player_id>', methods=['POST'])
@login_required
@email_verified_required
def create_for_player_post(player_id):
    if not current_user.has_role('user_admin'):
        flash('Only user admins can create characters for other players.', 'error')
        return redirect(url_for('characters.character_list'))
    user = User.query.filter_by(player_id=player_id).first()
    if not user:
        flash('Player not found.', 'error')
        return redirect(url_for('characters.character_list'))
    name = request.form.get('name')
    pronouns_subject = request.form.get('pronouns_subject')
    pronouns_object = request.form.get('pronouns_object')
    faction_id = request.form.get('faction')
    species_id = request.form.get('species_id')
    species_list = Species.query.all()
    factions = Faction.query.all()
    all_cybernetics = Cybernetic.query.order_by(Cybernetic.name).all()
    if not name or not faction_id or not species_id:
        flash('Character name, faction, and species are required', 'error')
        return render_template('characters/edit.html', player_id=player_id, admin_context=True, factions=factions, user_id=user.id, species_list=species_list, all_cybernetics=all_cybernetics)
    
    faction = Faction.query.get(faction_id)
    if not faction:
        flash('Invalid faction selected', 'error')
        return render_template('characters/edit.html', player_id=player_id, admin_context=True, factions=factions, user_id=user.id, species_list=species_list, all_cybernetics=all_cybernetics)
    
    # Only allow factions that allow player characters if user is not an NPC
    if not faction.allow_player_characters and not user.has_role('npc'):
        flash('You do not have permission to select this faction.', 'error')
        return render_template('characters/edit.html', player_id=player_id, admin_context=True, factions=factions, user_id=user.id, species_list=species_list, all_cybernetics=all_cybernetics)
    
    # Validate species is permitted for faction
    if not (current_user.has_role('user_admin') or current_user.has_role('npc')):
        species = Species.query.get(species_id)
        if not species or faction.id not in species.permitted_factions_list:
            flash('Selected species is not permitted for the chosen faction.', 'error')
            return render_template('characters/edit.html', player_id=player_id, admin_context=True, factions=factions, user_id=user.id, species_list=species_list, all_cybernetics=all_cybernetics)
    
    character = Character(
        user_id=user.id,
        name=name,
        pronouns_subject=pronouns_subject,
        pronouns_object=pronouns_object,
        status=CharacterStatus.DEVELOPING.value,
        faction_id=faction.id,
        species_id=int(species_id)
    )
    db.session.add(character)
    db.session.commit()
    # Audit log for creation
    audit = CharacterAuditLog(
        character_id=character.id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.CREATE.value,
        changes="Character created by admin"
    )
    db.session.add(audit)
    db.session.commit()
    if current_user.has_role('user_admin'):
        selected_cyber_ids = request.form.getlist('cybernetic_ids[]')
        for cid in selected_cyber_ids:
            db.session.add(CharacterCybernetic(character_id=character.id, cybernetic_id=cid))
        db.session.commit()
    flash('Character created successfully!', 'success')
    return redirect(url_for('user_management.user_management_edit_user', user_id=user.id))

@characters_bp.route('/<int:character_id>/audit-log')
@login_required
@email_verified_required
def audit_log(character_id):
    character = Character.query.get_or_404(character_id)
    if not (character.player_id == current_user.player_id or current_user.has_role(Role.USER_ADMIN.value)):
        flash('You do not have permission to view this character\'s audit log.', 'error')
        return redirect(url_for('characters.character_list'))
    
    audit_logs = CharacterAuditLog.query.filter_by(character_id=character_id).order_by(CharacterAuditLog.timestamp.desc()).all()
    return render_template('characters/audit_log.html', character=character, audit_logs=audit_logs, CharacterAuditAction=CharacterAuditAction)

@characters_bp.route('/<int:character_id>/reputation', methods=['GET'])
@login_required
@email_verified_required
def view_reputation(character_id):
    character = Character.query.get_or_404(character_id)
    if not (character.player_id == current_user.player_id or current_user.has_role(Role.USER_ADMIN.value)):
        flash('You do not have permission to view this character\'s reputation.', 'error')
        return redirect(url_for('characters.character_list'))
    
    factions = Faction.query.all()
    reputations = {faction.id: character.get_reputation(faction.id) for faction in factions}
    
    return render_template(
        'characters/reputation.html',
        character=character,
        factions=factions,
        reputations=reputations,
        can_edit=current_user.has_role(Role.USER_ADMIN.value)
    )

@characters_bp.route('/<int:character_id>/reputation', methods=['POST'])
@login_required
@email_verified_required
def update_reputation(character_id):
    if not current_user.has_role(Role.USER_ADMIN.value):
        flash('Only user admins can modify character reputation.', 'error')
        return redirect(url_for('characters.character_list'))
    
    character = Character.query.get_or_404(character_id)
    faction_id = request.form.get('faction_id')
    value = request.form.get('value')
    
    if not faction_id or value is None:
        flash('Faction and value are required.', 'error')
        return redirect(url_for('characters.view_reputation', character_id=character_id))
    
    try:
        value = int(value)
    except ValueError:
        flash('Reputation value must be a number.', 'error')
        return redirect(url_for('characters.view_reputation', character_id=character_id))
    
    character.set_reputation(faction_id, value, current_user.id)
    flash('Reputation updated successfully.', 'success')
    return redirect(url_for('characters.view_reputation', character_id=character_id))

@characters_bp.route('/api/validate_user_id_character_id')
@login_required
def validate_user_id_character_id():
    character_id = request.args.get('character_id')
    if not character_id:
        return jsonify({'success': False, 'error': 'No character ID provided'})
    
    try:
        # Split the character_id into user_id and character_id
        user_id, char_id = map(int, character_id.split('.'))
        
        # Query the character
        character = Character.query.filter_by(
            user_id=user_id,
            id=char_id
        ).first()
        
        if character:
            return jsonify({
                'success': True,
                'character_name': character.name
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Character not found'
            })
            
    except (ValueError, AttributeError):
        return jsonify({
            'success': False,
            'error': 'Invalid character ID format'
        })

@characters_bp.route('/<int:character_id>/view')
def view(character_id):
    character = Character.query.get_or_404(character_id)
    
    # Check access permissions
    can_view = False
    if current_user.is_authenticated:
        # Character owner can view
        if character.player_id == current_user.player_id:
            can_view = True
        # Users with specific roles can view
        elif current_user.has_role(Role.USER_ADMIN.value):
            can_view = True
        elif current_user.has_role(Role.RULES_TEAM.value):
            can_view = True
        elif current_user.has_role(Role.WIKI_EDITOR.value):
            can_view = True
        elif current_user.has_role(Role.NPC.value):
            can_view = True
    
    if not can_view:
        flash('You do not have permission to view this character.', 'error')
        return redirect(url_for('characters.character_list'))
    
    # Get the character sheet template
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.CHARACTER_SHEET.value).first()
    
    if not template:
        flash('Character sheet template not found.', 'error')
        return redirect(url_for('characters.character_list'))
    
    # Prepare template context
    template_context = {
        'character': character,
        'generate_qr_code': generate_qr_code,
        'generate_web_qr_code': generate_web_qr_code
    }
    
    # Render the template
    front_rendered = template.get_front_page_render(template_context)
    back_rendered = template.get_back_page_render(template_context)
    css = template.get_css_render()
    css_b64 = base64.b64encode(css.encode('utf-8')).decode('ascii')
    
    # Determine edit URL based on permissions
    edit_url = None
    if current_user.is_authenticated and (character.player_id == current_user.player_id or current_user.has_role('user_admin')):
        edit_url = url_for('characters.edit', character_id=character.id)
    
    return render_template('templates/view.html', 
                         title=f"{character.name} - Character Sheet",
                         template=template,
                         front_rendered=front_rendered,
                         back_rendered=back_rendered,
                         edit_url=edit_url,
                         back_url=url_for('characters.character_list'),
                         css_b64=css_b64,
                         character=character)
