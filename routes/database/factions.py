from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.database.faction import Faction
from models.enums import Role
from utils.decorators import email_verified_required
from models.wiki import get_or_create_wiki_page, WikiPage

factions_bp = Blueprint('factions', __name__)

@factions_bp.route('/')
def faction_list():
    factions = Faction.query.order_by(Faction.name).all()
    return render_template('factions/list.html', 
                         factions=factions,
                         can_edit=current_user.is_authenticated and current_user.has_role(Role.RULES_TEAM.value))

@factions_bp.route('/<int:faction_id>/edit', methods=['GET', 'POST'])
@login_required
@email_verified_required
def edit_faction(faction_id):
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    faction = Faction.query.get_or_404(faction_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        wiki_page = request.form.get('wiki_page')
        allow_player_characters = request.form.get('allow_player_characters') == 'on'
        
        if not all([name, wiki_page]):
            flash('All fields are required.', 'error')
            return render_template('factions/edit.html', faction=faction)
        
        try:
            # Ensure wiki page exists or create it
            get_or_create_wiki_page(wiki_page, f"{name} - Faction", created_by=current_user.id)
            faction.name = name
            faction.wiki_slug = wiki_page
            faction.allow_player_characters = allow_player_characters
            db.session.commit()
            flash('Faction updated successfully.', 'success')
            return redirect(url_for('factions.faction_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating faction: {str(e)}', 'error')
            return render_template('factions/edit.html', faction=faction)
    
    # For GET, fetch the wiki page title for the initial value
    initial_title = ''
    if faction.wiki_slug:
        wiki_page_obj = WikiPage.query.filter_by(slug=faction.wiki_slug).first()
        if wiki_page_obj:
            initial_title = wiki_page_obj.title
    return render_template('factions/edit.html', faction=faction, initial_title=initial_title)

@factions_bp.route('/new', methods=['GET', 'POST'])
@login_required
@email_verified_required
def new_faction():
    if not current_user.has_role(Role.RULES_TEAM.value):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        wiki_page = request.form.get('wiki_page')
        allow_player_characters = request.form.get('allow_player_characters') == 'on'
        
        if not all([name, wiki_page]):
            flash('All fields are required.', 'error')
            return render_template('factions/edit.html')
        
        try:
            # Ensure wiki page exists or create it
            get_or_create_wiki_page(wiki_page, f"{name} - Faction", created_by=current_user.id)
            faction = Faction(
                name=name,
                wiki_slug=wiki_page,
                allow_player_characters=allow_player_characters
            )
            db.session.add(faction)
            db.session.commit()
            flash('Faction created successfully.', 'success')
            return redirect(url_for('factions.faction_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating faction: {str(e)}', 'error')
            return render_template('factions/edit.html')
    
    return render_template('factions/edit.html', initial_title='') 