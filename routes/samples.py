from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.sample import Sample, SampleTag
from models.enums import ScienceType, Role
from models.print_template import PrintTemplate, PrintTemplateType
from utils.print_layout import PrintLayout

samples_bp = Blueprint('samples', __name__)

@samples_bp.route('/')
@login_required
def sample_list():
    """List all samples."""
    if not current_user.has_role('user_admin'):
        flash('You do not have permission to view samples.', 'error')
        return redirect(url_for('index'))
    
    samples = Sample.query.order_by(Sample.name).all()
    return render_template('samples/list.html', samples=samples)

@samples_bp.route('/create', methods=['POST'])
@login_required
def create_sample():
    """Create a new sample."""
    if not (current_user.has_role('downtime_team') or 
            current_user.has_role('rules_team') or 
            current_user.has_role('user_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
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