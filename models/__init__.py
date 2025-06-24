import logging
import os
import uuid
from datetime import datetime, timedelta

from models.database.conditions import Condition, ConditionStage
from models.database.cybernetic import Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.global_settings import GlobalSettings
from models.database.group_type import GroupType
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.database.mods import Mod
from models.database.sample import Sample
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import (
    AbilityType,
    BodyHitsType,
    EventType,
    PrintTemplateType,
    ScienceType,
    WikiPageVersionStatus,
)
from models.event import Event
from models.extensions import db, login_manager, migrate
from models.tools.character import (
    Character,
    CharacterAuditLog,
    CharacterCondition,
    CharacterReputation,
    CharacterSkill,
    CharacterTag,
)
from models.tools.group import Group, GroupInvite
from models.tools.pack import Pack
from models.tools.print_template import PrintTemplate
from models.tools.user import User
from models.wiki import WikiImage, WikiPage, WikiPageVersion, WikiSection, WikiTag
from utils.database_init import initialize_database


def init_app(app):
    # Ensure database directory exists
    os.makedirs(app.config["DATABASE_PATH"], exist_ok=True)

    # Initialize database
    db.init_app(app)

    # Initialize migrate
    migrate.init_app(app, db)

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


__all__ = [
    "db",
    "login_manager",
    "migrate",
    "User",
    "Character",
    "CharacterStatus",
    "CharacterAuditLog",
    "CharacterSkill",
    "Species",
    "Ability",
    "WikiPage",
    "WikiImage",
    "Skill",
    "Faction",
    "CharacterTag",
    "Group",
    "GroupInvite",
    "Sample",
    "Pack",
    "PackExotic",
    "PackMessage",
    "PackDowntimeResult",
    "setup_relationships",
]
