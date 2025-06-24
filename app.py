import os

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This must be done before importing other modules that depend on env vars
load_dotenv()

from flask import (  # noqa: E402
    Flask,
    abort,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required  # noqa: E402
from flask_migrate import Migrate  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from config import Config  # noqa: E402
from models import db, init_app, login_manager  # noqa: E402
from models.enums import DowntimeStatus, DowntimeTaskStatus  # noqa: E402
from models.tools.character import Character  # noqa: E402
from models.tools.downtime import DowntimePeriod  # noqa: E402
from models.tools.research import CharacterResearch  # noqa: E402
from routes.auth import auth_bp  # noqa: E402
from routes.database.conditions import conditions_bp  # noqa: E402
from routes.database.cybernetics import cybernetics_bp  # noqa: E402
from routes.database.exotic_substances import exotic_substances_bp  # noqa: E402
from routes.database.factions import factions_bp  # noqa: E402
from routes.database.global_settings import global_settings_bp  # noqa: E402
from routes.database.group_types import group_types_bp  # noqa: E402
from routes.database.item_blueprints import item_blueprints_bp  # noqa: E402
from routes.database.item_types import item_types_bp  # noqa: E402
from routes.database.items import items_bp  # noqa: E402
from routes.database.medicaments import medicaments_bp  # noqa: E402
from routes.database.mods import mods_bp  # noqa: E402
from routes.database.samples import samples_bp  # noqa: E402
from routes.database.skills import skills_bp  # noqa: E402
from routes.database.species import species_bp  # noqa: E402
from routes.events import events_bp  # noqa: E402
from routes.settings import settings_bp  # noqa: E402
from routes.tools.banking import banking_bp  # noqa: E402
from routes.tools.character_skills import character_skills_bp  # noqa: E402
from routes.tools.characters import characters_bp  # noqa: E402
from routes.tools.downtime import bp as downtime_bp  # noqa: E402
from routes.tools.groups import groups_bp  # noqa: E402
from routes.tools.messages import bp as messages_bp  # noqa: E402
from routes.tools.research import research_bp  # noqa: E402
from routes.tools.templates import templates_bp  # noqa: E402
from routes.tools.tickets import tickets_bp  # noqa: E402
from routes.tools.user_management import user_management_bp  # noqa: E402
from routes.wiki import wiki_bp  # noqa: E402
from utils.database_init import initialize_database  # noqa: E402
from utils.email import mail  # noqa: E402


def create_app(config_class=None):
    app = Flask("Orion Sphere LRP")

    if config_class is None:
        config_class = Config

    app.config.from_object(config_class())
    init_app(app)

    # Create engine and Session after app and db are initialized
    with app.app_context():
        engine = db.engine
        app.Session = sessionmaker(bind=engine)

        # Only create default data if not in testing mode
        if not app.config.get("TESTING"):
            initialize_database()

    mail.init_app(app)

    @app.before_request
    def before_request():
        g.db_session = app.Session()

    @app.after_request
    def after_request(response):
        db_session = getattr(g, "db_session", None)
        if db_session:
            db_session.close()
        return response

    @app.teardown_appcontext
    def teardown_db(exception):
        db_session = getattr(g, "db_session", None)
        if db_session:
            db_session.close()

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    @app.route("/.well-known/appspecific/com.chrome.devtools.json")
    def chrome_devtools_json():
        return "", 204

    @app.route("/toggle-theme", methods=["POST"])
    def toggle_theme():
        """Handle theme toggle for non-authenticated users."""
        try:
            data = request.get_json()
            theme = data.get("theme", "dark") if data else "dark"

            # Set cookie for non-authenticated users
            response = jsonify({"success": True, "theme": theme})
            response.set_cookie("theme", theme, max_age=30 * 24 * 60 * 60, path="/")  # 30 days
            return response
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(banking_bp, url_prefix="/banking")
    app.register_blueprint(downtime_bp, url_prefix="/downtime")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(groups_bp, url_prefix="/groups")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(research_bp, url_prefix="/research")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(templates_bp, url_prefix="/templates")
    app.register_blueprint(tickets_bp, url_prefix="/tickets")
    app.register_blueprint(user_management_bp, url_prefix="/users")
    app.register_blueprint(wiki_bp, url_prefix="/wiki")

    app.register_blueprint(characters_bp, url_prefix="/characters")
    app.register_blueprint(character_skills_bp, url_prefix="/characters/skills")

    app.register_blueprint(conditions_bp, url_prefix="/db/conditions")
    app.register_blueprint(cybernetics_bp, url_prefix="/db/cybernetics")
    app.register_blueprint(exotic_substances_bp, url_prefix="/db/exotic-substances")
    app.register_blueprint(factions_bp, url_prefix="/db/factions")
    app.register_blueprint(global_settings_bp, url_prefix="/db/global-settings")
    app.register_blueprint(group_types_bp, url_prefix="/db/group-types")
    app.register_blueprint(item_blueprints_bp, url_prefix="/db/item-blueprints")
    app.register_blueprint(item_types_bp, url_prefix="/db/item-types")
    app.register_blueprint(items_bp, url_prefix="/db/items")
    app.register_blueprint(medicaments_bp, url_prefix="/db/medicaments")
    app.register_blueprint(mods_bp, url_prefix="/db/mods")
    app.register_blueprint(samples_bp, url_prefix="/db/samples")
    app.register_blueprint(skills_bp, url_prefix="/db/skills")
    app.register_blueprint(species_bp, url_prefix="/db/species")

    @app.route("/")
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
            return any(
                pack.character.user_id == current_user.id
                and pack.status == DowntimeTaskStatus.ENTER_DOWNTIME
                for pack in active_period.packs
            )

        def has_research_projects():
            if not current_user.is_authenticated:
                return False
            return (
                CharacterResearch.query.join(CharacterResearch.character)
                .filter(Character.user_id == current_user.id)
                .first()
                is not None
            )

        return dict(
            has_enter_downtime_packs=has_enter_downtime_packs,
            has_research_projects=has_research_projects,
        )

    if app.config.get("TESTING"):

        @app.route("/test-page")
        def test_page():
            return render_template("test_page.html")

        @app.route("/protected")
        @login_required
        def protected_route():
            return "Protected content"

        @app.route("/admin-only")
        @login_required
        def admin_only_route():
            if not current_user.has_role("admin"):
                abort(403)
            return "Admin content"

    return app


if __name__ == "__main__":
    app = create_app()
    config = app.config
    ssl_context = None
    if config.get("SSL_ENABLED"):
        ssl_context = (config.get("SSL_CERT_FILE"), config.get("SSL_KEY_FILE"))

    app.run(
        debug=config.get("FLASK_DEBUG", "0") == "1",
        host=config.get("FLASK_RUN_HOST", "0.0.0.0"),  # nosec B104
        port=config.get("DEFAULT_PORT", 443),
        ssl_context=ssl_context,
    )
