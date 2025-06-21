from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.tools.group import Group, GroupInvite
from models.tools.character import Character
from models.enums import CharacterStatus, Role, GroupType
from flask_login import login_required, current_user
from models.tools.sample import Sample

from utils.decorators import email_verified_required, has_active_character_required, user_admin_required


groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/')
@login_required
@email_verified_required
def group_list():
    if current_user.has_role(Role.USER_ADMIN.value):
        # Show all groups for admins
        groups = Group.query.all()
        return render_template('groups/admin_list.html', groups=groups, GroupType=GroupType)
    
    # Get active character
    active_character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if not active_character:
        flash('You need an active character to access groups', 'error')
        return redirect(url_for('characters.character_list'))
    
    # Get group invites for the character
    invites = GroupInvite.query.filter_by(character_id=active_character.id).all()
    
    # Get list of active characters not in a group for invites
    active_characters = Character.query.filter_by(
        status=CharacterStatus.ACTIVE.value
    ).filter(
        Character.group_id.is_(None)
    ).all()
    
    return render_template('groups/list.html', 
                         character=active_character,
                         invites=invites,
                         active_characters=active_characters,
                         GroupType=GroupType)

@groups_bp.route('/new', methods=['GET'])
@login_required
@email_verified_required
def create_group():
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/create', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def create_group_post():
    name = request.form.get('name')
    type = request.form.get('type')
    
    if not name or not type:
        flash('Name and type are required', 'error')
        return redirect(url_for('groups.group_list'))

    if type not in GroupType.values():
        flash('Invalid group type', 'error')
        return redirect(url_for('groups.group_list'))

    active_character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    group = Group(
        name=name,
        type=type,  # The type value is already the enum value string
        bank_account=0
    )
    db.session.add(group)
    db.session.flush()  # Flush to get the group ID
    
    # Add character to group
    active_character.group_id = group.id
    
    db.session.commit()
    flash('Group created successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/edit', methods=['POST'])
@login_required
@email_verified_required
def edit_group_post(group_id):
    group = Group.query.get_or_404(group_id)
    name = request.form.get('name')
    type = request.form.get('type')
    bank_account = request.form.get('bank_account')
    
    if not name:
        flash('Name is required', 'error')
        return redirect(url_for('groups.group_list'))
    
    group.name = name
    
    if current_user.has_role(Role.USER_ADMIN.value):
        if type:
            group.type = type
        if bank_account is not None:
            try:
                group.bank_account = int(bank_account)
            except ValueError:
                flash('Bank account must be a number', 'error')
                return redirect(url_for('groups.group_list'))
    
    db.session.commit()
    flash('Group updated successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/invite', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def invite_character(group_id):
    group = Group.query.get_or_404(group_id)
    active_character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if active_character.group_id != group.id:
        flash('You must be a member of the group to invite others', 'error')
        return redirect(url_for('groups.group_list'))
    
    character_id = request.form.get('character_id')
    if not character_id:
        flash('Character ID is required', 'error')
        return redirect(url_for('groups.group_list'))
    
    character = Character.query.get(character_id)
    if not character:
        flash('Character not found', 'error')
        return redirect(url_for('groups.group_list'))
    
    if character.group_id:
        flash('Character is already in a group', 'error')
        return redirect(url_for('groups.group_list'))
    
    # Check if invite already exists
    existing_invite = GroupInvite.query.filter_by(
        group_id=group.id,
        character_id=character.id
    ).first()
    
    if existing_invite:
        flash('Character already has an invite to this group', 'error')
        return redirect(url_for('groups.group_list'))
    
    invite = GroupInvite(
        group_id=group.id,
        character_id=character.id
    )
    db.session.add(invite)
    db.session.commit()
    
    flash('Invite sent successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/invite/<int:invite_id>/accept', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def accept_invite(invite_id):
    invite = GroupInvite.query.get_or_404(invite_id)
    active_character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if active_character.id != invite.character_id:
        flash('This invite is not for your character', 'error')
        return redirect(url_for('groups.group_list'))
    
    if active_character.group_id:
        flash('Your character is already in a group', 'error')
        return redirect(url_for('groups.group_list'))
    
    # Add character to group
    active_character.group_id = invite.group_id
    
    # Delete the invite
    db.session.delete(invite)
    db.session.commit()
    
    flash('Joined group successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/invite/<int:invite_id>/decline', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def decline_invite(invite_id):
    invite = GroupInvite.query.get_or_404(invite_id)
    active_character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if active_character.id != invite.character_id:
        flash('This invite is not for your character', 'error')
        return redirect(url_for('groups.group_list'))
    
    # Delete the invite
    db.session.delete(invite)
    db.session.commit()
    
    flash('Invite declined', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def leave_group(group_id):
    group = Group.query.get_or_404(group_id)
    character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if character.group_id != group_id:
        flash('You are not a member of this group', 'error')
        return redirect(url_for('groups.group_list'))
    
    character.group_id = None
    db.session.commit()
    flash('You have left the group', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/disband', methods=['POST'])
@login_required
@email_verified_required
@has_active_character_required
def disband_group(group_id):
    group = Group.query.get_or_404(group_id)
    character = Character.query.filter_by(
        user_id=current_user.id,
        status=CharacterStatus.ACTIVE.value
    ).first()
    
    if character.group_id != group_id:
        flash('You are not a member of this group', 'error')
        return redirect(url_for('groups.group_list'))
    
    # Check if this is the only member
    if len(group.characters) > 1:
        flash('Cannot disband group with multiple members', 'error')
        return redirect(url_for('groups.group_list'))
    
    # Remove character from group
    character.group_id = None
    
    # Delete all invites for this group
    GroupInvite.query.filter_by(group_id=group_id).delete()
    
    # Delete the group
    db.session.delete(group)
    db.session.commit()
    
    flash('Group has been disbanded', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/remove/<int:character_id>', methods=['POST'])
@login_required
@email_verified_required
@user_admin_required
def remove_character(group_id, character_id):
    group = Group.query.get_or_404(group_id)
    character = Character.query.get_or_404(character_id)
    
    if character.group_id != group.id:
        flash('Character is not a member of this group', 'error')
        return redirect(url_for('groups.group_list'))
    
    character.group_id = None
    db.session.commit()
    flash('Character removed from group', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/create/admin', methods=['GET', 'POST'])
@login_required
@email_verified_required
@user_admin_required
def create_group_admin():
    if request.method == 'GET':
        return render_template('groups/admin_edit.html', GroupType=GroupType)
    
    name = request.form.get('name')
    type = request.form.get('type')
    bank_account = request.form.get('bank_account')
    
    if not name or not type:
        flash('Name and type are required', 'error')
        return redirect(url_for('groups.create_group_admin'))

    if type not in GroupType.values():
        flash('Invalid group type', 'error')
        return redirect(url_for('groups.create_group_admin'))

    try:
        bank_account_int = int(bank_account) if bank_account else 0
    except ValueError:
        flash('Bank account must be a number', 'error')
        return redirect(url_for('groups.create_group_admin'))

    group = Group(
        name=name,
        type=type,
        bank_account=bank_account_int
    )
    db.session.add(group)
    db.session.commit()
    
    flash('Group created successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/edit/admin', methods=['GET'])
@login_required
@email_verified_required
@user_admin_required
def edit_group_admin(group_id):
    group = Group.query.get_or_404(group_id)
    
    return render_template('groups/admin_edit.html', group=group, GroupType=GroupType)

@groups_bp.route('/<int:group_id>/edit/admin', methods=['POST'])
@login_required
@email_verified_required
@user_admin_required
def edit_group_admin_post(group_id):
    group = Group.query.get_or_404(group_id)
    
    name = request.form.get('name')
    type = request.form.get('type')
    bank_account = request.form.get('bank_account')
    
    if not name:
        flash('Name is required', 'error')
        return redirect(url_for('groups.edit_group_admin', group_id=group.id, GroupType=GroupType))
    
    if type not in GroupType.values():
        flash('Invalid group type', 'error')
        return redirect(url_for('groups.edit_group_admin', group_id=group.id, GroupType=GroupType))
    
    try:
        bank_account_int = int(bank_account) if bank_account else 0
    except ValueError:
        flash('Bank account must be a number', 'error')
        return redirect(url_for('groups.admin_edit', group_id=group.id, GroupType=GroupType))
    
    group.name = name
    group.type = type
    group.bank_account = bank_account_int
    
    db.session.commit()
    flash('Group updated successfully', 'success')
    return redirect(url_for('groups.group_list'))

@groups_bp.route('/<int:group_id>/add_character/admin', methods=['POST'])
@login_required
@email_verified_required
@user_admin_required
def add_character_admin(group_id):
    group = Group.query.get_or_404(group_id)
    character_id = request.form.get('character_id')
    
    if not character_id:
        flash('Character ID is required', 'error')
        return redirect(url_for('groups.group_list'))
    
    character = Character.query.get(character_id)
    if not character:
        flash('Character not found', 'error')
        return redirect(url_for('groups.group_list'))
    
    if character.group_id:
        flash('Character is already in a group', 'error')
        return redirect(url_for('groups.group_list'))
    
    character.group_id = group_id
    db.session.commit()
    
    flash('Character added to group', 'success')
    return redirect(url_for('groups.group_list')) 