from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.tools.sample import Sample, SampleTag
from models.enums import ScienceType, Role
from models.tools.print_template import PrintTemplate, PrintTemplateType
from utils.print_layout import PrintLayout
from utils.decorators import downtime_or_rules_team_required

samples_bp = Blueprint('samples', __name__)

@samples_bp.route('/')
@login_required
@downtime_or_rules_team_required
def sample_list():
    """List all samples."""
    samples = Sample.query.order_by(Sample.name).all()
    return render_template('samples/list.html', samples=samples)

@samples_bp.route('/new', methods=['GET'])
@login_required
@downtime_or_rules_team_required
def create():
    """Show the create sample form."""
    return render_template('samples/edit.html', sample=None, science_types=ScienceType.values(), tags=SampleTag.query.order_by(SampleTag.name).all())

@samples_bp.route('/new', methods=['POST'])
@login_required
@downtime_or_rules_team_required
def create_post():
    """Handle the create sample form submission."""
    name = request.form.get('name')
    type_str = request.form.get('type')
    description = request.form.get('description', '')
    tags = request.form.getlist('tags[]')
    is_researched = request.form.get('is_researched') == 'on'
    
    if not name or not type_str:
        flash('Name and type are required', 'error')
        return render_template('samples/edit.html', sample=None, science_types=ScienceType.values(), tags=SampleTag.query.order_by(SampleTag.name).all())
        
    sample = Sample(
        name=name,
        type=ScienceType(type_str),
        description=description,
        is_researched=is_researched
    )
    
    if tags:
        for tag_name in tags:
            tag = SampleTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = SampleTag(name=tag_name)
                db.session.add(tag)
            sample.tags.append(tag)
    
    db.session.add(sample)
    db.session.commit()
    flash('Sample created', 'success')
    return redirect(url_for('samples.sample_list'))

@samples_bp.route('/<int:id>/edit', methods=['GET'])
@login_required
@downtime_or_rules_team_required
def edit(id):
    """Show the edit sample form."""
    sample = Sample.query.get_or_404(id)
    return render_template('samples/edit.html', sample=sample, science_types=ScienceType.values(), tags=SampleTag.query.order_by(SampleTag.name).all())

@samples_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
@downtime_or_rules_team_required
def edit_post(id):
    """Handle the edit sample form submission."""
    sample = Sample.query.get_or_404(id)
    
    name = request.form.get('name')
    type_str = request.form.get('type')
    description = request.form.get('description', '')
    tags = request.form.getlist('tags[]')
    is_researched = request.form.get('is_researched') == 'on'
    
    if not name or not type_str:
        flash('Name and type are required', 'error')
        return render_template('samples/edit.html', sample=sample, science_types=ScienceType.values(), tags=SampleTag.query.order_by(SampleTag.name).all())
        
    sample.name = name
    sample.type = ScienceType(type_str)
    sample.description = description
    sample.is_researched = is_researched
    
    # Clear existing tags and add new ones
    sample.tags.clear()
    if tags:
        for tag_name in tags:
            tag = SampleTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = SampleTag(name=tag_name)
                db.session.add(tag)
            sample.tags.append(tag)
    
    db.session.commit()
    flash('Sample updated', 'success')
    return redirect(url_for('samples.sample_list'))

@samples_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@downtime_or_rules_team_required
def delete(id):
    """Delete a sample."""
    sample = Sample.query.get_or_404(id)
    db.session.delete(sample)
    db.session.commit()
    flash('Sample deleted', 'success')
    return redirect(url_for('samples.sample_list'))

@samples_bp.route('/create', methods=['POST'])
@login_required
@downtime_or_rules_team_required
def create_sample():
    """Create a new sample."""
    name = request.form.get('name')
    type_str = request.form.get('type')
    description = request.form.get('description', '')
    tags = request.form.getlist('tags[]')
    
    if not name or not type_str:
        return jsonify({'error': 'Name and type are required'}), 400

    sample = Sample(
        name=name,
        type=ScienceType(type_str),
        description=description
    )
    
    if tags:
        for tag_name in tags:
            tag = SampleTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = SampleTag(name=tag_name)
                db.session.add(tag)
            sample.tags.append(tag)
    
    db.session.add(sample)
    db.session.commit()
    
    return jsonify({
        'id': sample.id,
        'name': sample.name,
        'type': sample.type.value,
        'description': sample.description
    }) 