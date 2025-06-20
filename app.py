from flask import Flask, render_template, redirect, url_for, request, abort
from models.tools.character import Character
from models.extensions import db
from models import init_app
from utils.email import mail
from config import Config
from routes.wiki import wiki_bp
from routes.tools.user_management import user_management_bp
from routes.settings import settings_bp
from routes.auth import auth_bp
from routes.tools.characters import characters_bp
from routes.tools.character_skills import character_skills_bp
from routes.tools.groups import groups_bp
from routes.tools.banking import banking_bp
from routes.tools.templates import templates_bp
from routes.database.factions import factions_bp
from routes.database.species import species_bp
from routes.database.skills import skills_bp
from routes.database.exotic_substances import exotic_substances_bp
from routes.database.mods import mods_bp
from routes.database.medicaments import medicaments_bp
from routes.database.conditions import conditions_bp
from routes.database.item_types import item_types_bp
from routes.database.item_blueprints import item_blueprints_bp
from routes.database.items import items_bp
from routes.database.cybernetics import cybernetics_bp
from routes.tools.research import research_bp
from routes.tools.downtime import bp as downtime_bp
from routes.tools.messages import bp as messages_bp
from flask_login import current_user, login_required
from models.tools.downtime import DowntimePeriod
from models.enums import DowntimeStatus, DowntimeTaskStatus
from models.tools.research import CharacterResearch
from routes.tools.samples import samples_bp
from routes.events import events_bp
from routes.tools.tickets import tickets_bp

def create_app(config_class=None):
    app = Flask("Orion Sphere LRP")
    
    if config_class is None:
        config_class = Config
        try:
            from config.local import LocalConfig
            config_class = LocalConfig
        except ImportError:
            pass
    
    app.config.from_object(config_class())
    init_app(app)
    mail.init_app(app)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.route('/.well-known/appspecific/com.chrome.devtools.json')
    def chrome_devtools_json():
        return '', 204

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(banking_bp, url_prefix='/banking')
    app.register_blueprint(downtime_bp, url_prefix='/downtime')
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(groups_bp, url_prefix='/groups')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(research_bp, url_prefix='/research')
    app.register_blueprint(samples_bp, url_prefix='/samples')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(user_management_bp, url_prefix='/users')
    app.register_blueprint(wiki_bp, url_prefix='/wiki')

    app.register_blueprint(characters_bp, url_prefix='/characters')
    app.register_blueprint(character_skills_bp, url_prefix='/characters/skills')

    app.register_blueprint(conditions_bp, url_prefix='/db/conditions')
    app.register_blueprint(cybernetics_bp, url_prefix='/db/cybernetics')
    app.register_blueprint(exotic_substances_bp, url_prefix='/db/exotic-substances')
    app.register_blueprint(factions_bp, url_prefix='/db/factions')
    app.register_blueprint(item_blueprints_bp, url_prefix='/db/item-blueprints')
    app.register_blueprint(item_types_bp, url_prefix='/db/item-types')
    app.register_blueprint(items_bp, url_prefix='/db/items')
    app.register_blueprint(medicaments_bp, url_prefix='/db/medicaments')
    app.register_blueprint(mods_bp, url_prefix='/db/mods')
    app.register_blueprint(skills_bp, url_prefix='/db/skills')
    app.register_blueprint(species_bp, url_prefix='/db/species')

    @app.route('/')
    def index():
        return redirect(url_for("wiki.wiki_view", slug="index"))

    @app.context_processor
    def utility_processor():
        def has_enter_downtime_packs():
            if not current_user.is_authenticated:
                return False
            active_period = DowntimePeriod.query.filter_by(status=DowntimeStatus.PENDING).first()
            if not active_period:
                return False
            return any(pack.character.user_id == current_user.id and 
                      pack.status == DowntimeTaskStatus.ENTER_DOWNTIME 
                      for pack in active_period.packs)
        
        def has_research_projects():
            if not current_user.is_authenticated:
                return False
            return CharacterResearch.query.join(CharacterResearch.character).filter(
                Character.user_id == current_user.id
            ).first() is not None
        
        return dict(
            has_enter_downtime_packs=has_enter_downtime_packs,
            has_research_projects=has_research_projects
        )

    if app.config.get('TESTING'):
        @app.route('/test-page')
        def test_page():
            return render_template('test_page.html')

        @app.route('/protected')
        @login_required
        def protected_route():
            return "Protected content"
        
        @app.route('/admin-only')
        @login_required
        def admin_only_route():
            if not current_user.has_role('admin'):
                abort(403)
            return "Admin content"

    return app

if __name__ == '__main__':
    app = create_app()
    config = app.config
    
    ssl_context = None
    if config.get('SSL_ENABLED'):
        ssl_context = (
            config.get('SSL_CERT_FILE'),
            config.get('SSL_KEY_FILE')
        )
    
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=config.get('DEFAULT_PORT', 443),
        ssl_context=ssl_context
    )