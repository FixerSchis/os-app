from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.extensions import db
from models.database.skills import Skill
from models.database.species import Species
from models.database.faction import Faction
from models.tools.character import CharacterTag
from models.enums import Role, ScienceType
from utils.decorators import email_verified_required, rules_team_required
import re

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/')
def skills_list():
    # Get all skills
    skills = Skill.query.all()

    # Build a mapping of skill_type to friendly name
    skill_types = Skill.get_all_skill_types()
    type_friendly_names = {t[0]: t[0].replace('_', ' ').title() for t in skill_types if t[0] is not None}

    # Group skills by type
    from collections import defaultdict
    skills_by_type = defaultdict(list)
    for s in skills:
        skill_type = s.skill_type or 'UNCATEGORIZED'
        skills_by_type[skill_type].append(s)

    # For each type, sort by name, and ensure requirements are after their prerequisites
    sorted_skills_by_type = {}
    for skill_type in sorted(skills_by_type.keys()):
        group = skills_by_type[skill_type]
        group_sorted = []
        processed_ids = set()
        # First, add skills with no requirements
        for skill in sorted(group, key=lambda s: s.name):
            if not skill.required_skill_id and skill.id not in processed_ids:
                group_sorted.append(skill)
                processed_ids.add(skill.id)
        # Then, add skills with requirements, after their prerequisites
        remaining_skills = [s for s in group if s.id not in processed_ids]
        while remaining_skills:
            for skill in sorted(remaining_skills, key=lambda s: s.name):
                if skill.required_skill_id in processed_ids:
                    group_sorted.append(skill)
                    processed_ids.add(skill.id)
                    remaining_skills.remove(skill)
                    break
            else:
                # If we couldn't add any skills in this pass, add the remaining ones
                for skill in sorted(remaining_skills, key=lambda s: s.name):
                    group_sorted.append(skill)
                    processed_ids.add(skill.id)
                break
        sorted_skills_by_type[skill_type] = group_sorted

    return render_template('skills/list.html', 
                         skills_by_type=sorted_skills_by_type,
                         type_friendly_names=type_friendly_names,
                         can_edit=current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value))

@skills_bp.route('/<int:skill_id>/edit', methods=['GET'])
@login_required
@email_verified_required
def edit_skill(skill_id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    skill = Skill.query.get_or_404(skill_id)
    species_list = Species.query.all()
    skills_list = Skill.query.all()
    skill_types = Skill.get_all_skill_types()
    science_types = ScienceType.values()
    
    return render_template('skills/edit.html', 
                         skill=skill, 
                         factions=Faction.query.all(), 
                         species_list=species_list,
                         skills_list=skills_list,
                         skill_types=skill_types,
                         science_types=science_types,
                         tags=CharacterTag.query.all())

@skills_bp.route('/<int:skill_id>/edit', methods=['POST'])
@login_required
@email_verified_required
def edit_skill_post(skill_id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    skill = Skill.query.get_or_404(skill_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    skill_type = request.form.get('skill_type')
    base_cost = request.form.get('base_cost')
    can_purchase_multiple = request.form.get('can_purchase_multiple') == 'on'
    cost_increases = request.form.get('cost_increases') == 'on'
    required_skill_id = request.form.get('required_skill_id')
    required_species = request.form.getlist('required_species')
    required_factions = request.form.getlist('required_factions')
    required_tags = request.form.getlist('required_tags')
    
    # Handle character sheet values
    character_sheet_values = []
    form_data = request.form.to_dict()
    for key, value in form_data.items():
        if key.startswith('character_sheet_values[') and key.endswith('][id]'):
            # Extract the index from the key using regex
            match = re.match(r'character_sheet_values\[(\d+)\]\[id\]', key)
            if match:
                index = match.group(1)
            else:
                index = ''
            id_value = value
            description_value = form_data.get(f'character_sheet_values[{index}][description]', '')
            value_value = form_data.get(f'character_sheet_values[{index}][value]', '0')
            # Only add if we have an ID
            if id_value.strip():
                try:
                    value_value = int(value_value) if value_value else 0
                except ValueError:
                    value_value = 0
                character_sheet_values.append({
                    'id': id_value.strip(),
                    'description': description_value.strip(),
                    'value': value_value
                })
    
    if not all([name, description, skill_type, base_cost]):
        flash('Name, description, skill type, and base cost are required.', 'error')
        species_list = Species.query.all()
        skills_list = Skill.query.all()
        skill_types = Skill.get_all_skill_types()
        science_types = ScienceType.values()
        return render_template('skills/edit.html', 
                             skill=skill, 
                             factions=Faction.query.all(),
                             species_list=species_list,
                             skills_list=skills_list,
                             skill_types=skill_types,
                             science_types=science_types,
                             tags=CharacterTag.query.all())
    
    try:
        # Handle new tags
        tag_ids = []
        for tag_id in required_tags:
            if not tag_id.isdigit():  # This is a new tag
                tag = CharacterTag(name=tag_id)
                db.session.add(tag)
                db.session.flush()  # Get the new tag's ID
                tag_ids.append(str(tag.id))
            else:
                tag_ids.append(tag_id)
        
        skill.name = name
        skill.description = description
        skill.skill_type = skill_type
        skill.base_cost = int(base_cost)
        skill.can_purchase_multiple = can_purchase_multiple
        skill.cost_increases = cost_increases
        skill.required_skill_id = int(required_skill_id) if required_skill_id else None
        skill.required_species_list = required_species
        skill.required_factions_list = required_factions
        skill.required_tags_list = tag_ids
        skill.character_sheet_values_list = character_sheet_values
        
        db.session.commit()
        flash('Skill updated successfully.', 'success')
        return redirect(url_for('skills.skills_list'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating skill: {str(e)}', 'error')

@skills_bp.route('/new', methods=['GET', 'POST'])
@login_required
@email_verified_required
def new_skill():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        skill_type = request.form.get('skill_type')
        base_cost = request.form.get('base_cost')
        can_purchase_multiple = request.form.get('can_purchase_multiple') == 'on'
        cost_increases = request.form.get('cost_increases') == 'on'
        required_skill_id = request.form.get('required_skill_id')
        required_species = request.form.getlist('required_species')
        required_factions = request.form.getlist('required_factions')
        required_tags = request.form.getlist('required_tags')
        
        # Handle character sheet values
        character_sheet_values = []
        form_data = request.form.to_dict()
        for key, value in form_data.items():
            if key.startswith('character_sheet_values[') and key.endswith('][id]'):
                # Extract the index from the key using regex
                match = re.match(r'character_sheet_values\[(\d+)\]\[id\]', key)
                if match:
                    index = match.group(1)
                else:
                    index = ''
                id_value = value
                description_value = form_data.get(f'character_sheet_values[{index}][description]', '')
                value_value = form_data.get(f'character_sheet_values[{index}][value]', '0')
                # Only add if we have an ID
                if id_value.strip():
                    try:
                        value_value = int(value_value) if value_value else 0
                    except ValueError:
                        value_value = 0
                    character_sheet_values.append({
                        'id': id_value.strip(),
                        'description': description_value.strip(),
                        'value': value_value
                    })
        
        if not all([name, description, skill_type, base_cost]):
            flash('Name, description, skill type, and base cost are required.', 'error')
            species_list = Species.query.all()
            skills_list = Skill.query.all()
            skill_types = Skill.get_all_skill_types()
            science_types = ScienceType.values()
            return render_template('skills/edit.html', 
                                 skill=None,
                                 factions=Faction.query.all(),
                                 species_list=species_list,
                                 skills_list=skills_list,
                                 skill_types=skill_types,
                                 science_types=science_types,
                                 tags=CharacterTag.query.all())
        
        try:
            # Handle new tags
            tag_ids = []
            for tag_id in required_tags:
                if not tag_id.isdigit():  # This is a new tag
                    tag = CharacterTag(name=tag_id)
                    db.session.add(tag)
                    db.session.flush()  # Get the new tag's ID
                    tag_ids.append(str(tag.id))
                else:
                    tag_ids.append(tag_id)
            
            skill = Skill(
                name=name,
                description=description,
                skill_type=skill_type,
                base_cost=int(base_cost),
                can_purchase_multiple=can_purchase_multiple,
                cost_increases=cost_increases,
                required_skill_id=int(required_skill_id) if required_skill_id else None,
                required_species_list=required_species,
                required_factions_list=required_factions,
                required_tags_list=tag_ids,
                character_sheet_values_list=character_sheet_values
            )
            db.session.add(skill)
            db.session.commit()
            flash('Skill created successfully.', 'success')
            return redirect(url_for('skills.skills_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating skill: {str(e)}', 'error')
    
    species_list = Species.query.all()
    skills_list = Skill.query.all()
    skill_types = Skill.get_all_skill_types()
    science_types = ScienceType.values()
    
    return render_template('skills/edit.html', 
                         factions=Faction.query.all(), 
                         species_list=species_list,
                         skills_list=skills_list,
                         skill_types=skill_types,
                         science_types=science_types,
                         tags=CharacterTag.query.all()) 