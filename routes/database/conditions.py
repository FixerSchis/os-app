from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models.extensions import db
from models.database.conditions import Condition, ConditionStage
from models.enums import Role
from utils.decorators import email_verified_required

conditions_bp = Blueprint('conditions', __name__)

@conditions_bp.route('/')
def list():
    conditions = Condition.query.order_by(Condition.name).all()
    can_edit = current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value)
    return render_template('rules/conditions/list.html', conditions=conditions, can_edit=can_edit)

@conditions_bp.route('/new', methods=['GET'])
@login_required
@email_verified_required
def create():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('index'))
    return render_template('rules/conditions/edit.html')

@conditions_bp.route('/new', methods=['POST'])
@login_required
@email_verified_required
def create_post():
    name = request.form.get('name')
    stages_data = request.form.getlist('stages')
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('index'))
    
    if not name:
        flash('Name is required', 'error')
        return render_template('rules/conditions/edit.html')
    
    try:
        condition = Condition(name=name)
        db.session.add(condition)
        db.session.flush()  # Get the condition ID
        
        # Process stages
        for i, stage_data in enumerate(stages_data, 1):
            stage = ConditionStage(
                condition_id=condition.id,
                stage_number=i,
                rp_effect=request.form.get(f'rp_effect_{i}'),
                diagnosis=request.form.get(f'diagnosis_{i}'),
                cure=request.form.get(f'cure_{i}'),
                duration=int(request.form.get(f'duration_{i}', 0))
            )
            db.session.add(stage)
        
        db.session.commit()
        flash('Condition created successfully', 'success')
        return redirect(url_for('conditions.list'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating condition: {str(e)}', 'error')
        return render_template('rules/conditions/edit.html')

@conditions_bp.route('/<int:id>/edit', methods=['GET'])
@login_required
@email_verified_required
def edit(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('index'))
    
    condition = Condition.query.get_or_404(id)
    return render_template('rules/conditions/edit.html', condition=condition)

@conditions_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
@email_verified_required
def edit_post(id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('index'))
    
    condition = Condition.query.get_or_404(id)
    name = request.form.get('name')
    stages_data = request.form.getlist('stages')
    print('DEBUG edit_post: stages_data:', stages_data)
    print('DEBUG edit_post: request.form:', dict(request.form))
    
    if not name:
        flash('Name is required', 'error')
        return render_template('rules/conditions/edit.html', condition=condition)
    
    try:
        condition.name = name
        
        # Delete existing stages
        print('DEBUG edit_post: deleting existing stages, count:', len(condition.stages))
        ConditionStage.query.filter_by(condition_id=condition.id).delete()
        
        # Add new stages
        print('DEBUG edit_post: adding new stages, count:', len(stages_data))
        for i, stage_data in enumerate(stages_data, 1):
            stage = ConditionStage(
                condition_id=condition.id,
                stage_number=i,
                rp_effect=request.form.get(f'rp_effect_{i}'),
                diagnosis=request.form.get(f'diagnosis_{i}'),
                cure=request.form.get(f'cure_{i}'),
                duration=int(request.form.get(f'duration_{i}', 0))
            )
            db.session.add(stage)
            print(f'DEBUG edit_post: added stage {i}')
        
        db.session.commit()
        print('DEBUG edit_post: commit successful, final stage count:', len(condition.stages))
        flash('Condition updated successfully', 'success')
        return redirect(url_for('conditions.list'))
    except Exception as e:
        db.session.rollback()
        print('DEBUG edit_post: error:', str(e))
        flash(f'Error updating condition: {str(e)}', 'error')
        return render_template('rules/conditions/edit.html', condition=condition) 