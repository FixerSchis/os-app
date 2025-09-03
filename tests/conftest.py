import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

from app import create_app
from config import TestConfig
from models.database.conditions import Condition, ConditionStage
from models.database.cybernetic import CharacterCybernetic, Cybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.faction import Faction
from models.database.global_settings import GlobalSettings
from models.database.group_type import GroupType
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.database.mods import Mod
from models.database.permissions import Role as Role
from models.database.sample import Sample, SampleTag
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.enums import CharacterStatus, DowntimeStatus, DowntimeTaskStatus
from models.enums import GroupType as GroupTypeEnum
from models.enums import ScienceType, WikiPageVersionStatus
from models.event import Event
from models.extensions import db as _db
from models.tools.character import (
    Character,
    CharacterAuditLog,
    CharacterCondition,
    CharacterReputation,
    CharacterSkill,
    CharacterTag,
)
from models.tools.downtime import DowntimePack, DowntimePeriod
from models.tools.event_ticket import EventTicket
from models.tools.group import Group, GroupInvite
from models.tools.message import Message
from models.tools.print_template import PrintTemplate
from models.tools.research import (
    CharacterResearch,
    CharacterResearchStage,
    CharacterResearchStageRequirement,
    Research,
    ResearchStage,
    ResearchStageRequirement,
)
from models.tools.user import User
from models.wiki import WikiChangeLog, WikiImage, WikiPage, WikiPageVersion, WikiSection, WikiTag

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def initialize_test_permissions(db_session):
    """Initialize permissions for testing."""
    from models.database.permissions import Permission

    # Create all the permissions that might be needed in tests
    permissions_data = [
        ("rules.conditions", "Manage conditions", "rules"),
        ("rules.skills", "Manage skills", "rules"),
        ("rules.species", "Manage species", "rules"),
        ("rules.cybernetics", "Manage cybernetics", "rules"),
        ("rules.exotic_substances", "Manage exotic substances", "rules"),
        ("rules.factions", "Manage factions", "rules"),
        ("rules.items", "Manage items", "rules"),
        ("rules.medicaments", "Manage medicaments", "rules"),
        ("rules.mods", "Manage mods", "rules"),
        ("rules.item_types", "Manage item types", "rules"),
        ("rules.item_blueprints", "Manage item blueprints", "rules"),
        ("rules.global_settings", "Manage global settings", "rules"),
        ("rules.group_types", "Manage group types", "rules"),
        ("event.create", "Create events", "event"),
        ("event.edit", "Edit events", "event"),
        ("event.delete", "Delete events", "event"),
        ("event.manage", "Manage event assignments and attendees", "event"),
        ("event.view_attendees", "View event attendees", "event"),
        ("event.view_packs", "View event packs", "event"),
        ("event.assign_tickets", "Assign event tickets", "event"),
        ("event.manage_attendees", "Manage event attendees", "event"),
        ("user.view", "View user list", "user"),
        ("user.edit", "Edit user details", "user"),
        ("user.roles", "Manage user roles", "user"),
        ("owner.promote", "Promote users to owner", "owner"),
        ("wiki.create", "Create wiki pages", "wiki"),
        ("wiki.edit", "Edit wiki pages", "wiki"),
        ("wiki.delete", "Delete wiki pages", "wiki"),
        ("wiki.publish", "Publish wiki pages", "wiki"),
        ("wiki.manage_sections", "Manage wiki sections", "wiki"),
        ("plot.reputation_briefings", "Manage reputation briefings", "plot"),
        ("character.view_all", "View all characters", "character"),
        ("character.edit_all", "Edit any character", "character"),
        ("character.background_approve", "Approve character backgrounds", "character"),
        ("character.refund", "Refund character skills from active characters", "character"),
        ("banking.view_all", "View all bank accounts", "banking"),
        ("banking.manage", "Manage banking operations", "banking"),
        ("database.backup", "Create database backups", "database"),
        ("database.restore", "Restore database backups", "database"),
        ("group.view_all", "View all groups", "group"),
        ("group.edit", "Edit groups", "group"),
        ("group.background_approve", "Approve group backgrounds", "group"),
        ("messages.view_all", "View all messages", "messages"),
        ("messages.respond", "Respond to messages", "messages"),
        ("messages.send_for_character", "Send messages for characters", "messages"),
        ("messages.send_for_other", "Send messages on behalf of other users", "messages"),
        ("research.create", "Create research projects", "research"),
        ("research.edit", "Edit research projects", "research"),
        ("research.delete", "Delete research projects", "research"),
        ("research.assign", "Assign research projects", "research"),
        ("template.create", "Create templates", "template"),
        ("template.edit", "Edit templates", "template"),
        ("downtime.manage", "Manage downtime packs", "downtime"),
    ]

    for name, description, category in permissions_data:
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            permission = Permission(name=name, description=description, category=category)
            db_session.add(permission)

    db_session.commit()


def assign_role_to_user(user, role_name, db_session):
    """Helper function to assign a role to a user."""
    # Initialize permissions first
    initialize_test_permissions(db_session)

    role = Role.query.filter_by(name=role_name).first()
    if role:
        user.role = role
        db_session.commit()
    else:
        # Create the role if it doesn't exist (for testing)
        role = Role(name=role_name, description=f"Test {role_name} role")
        db_session.add(role)
        db_session.commit()

        # Assign appropriate permissions based on role name
        if role_name == "rules_team":
            # Add rules-related permissions
            from models.database.permissions import Permission

            rules_permissions = [
                "rules.conditions",
                "rules.skills",
                "rules.species",
                "rules.cybernetics",
                "rules.exotic_substances",
                "rules.factions",
                "rules.items",
                "rules.medicaments",
                "rules.mods",
                "rules.item_types",
                "rules.item_blueprints",
                "rules.global_settings",
                "rules.group_types",
            ]
            # Add event permissions
            event_permissions = [
                "event.create",
                "event.edit",
                "event.delete",
                "event.assign_tickets",
                "event.manage_attendees",
            ]
            # Add research permissions
            research_permissions = [
                "research.create",
                "research.edit",
                "research.delete",
                "research.assign",
            ]
            all_permissions = rules_permissions + event_permissions + research_permissions
            for perm_name in all_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role.add_permission(permission)
        elif role_name == "admin":
            # Add all permissions to admin role
            from models.database.permissions import Permission

            all_permissions = [
                "rules.conditions",
                "rules.skills",
                "rules.species",
                "rules.cybernetics",
                "rules.exotic_substances",
                "rules.factions",
                "rules.items",
                "rules.medicaments",
                "rules.mods",
                "rules.item_types",
                "rules.item_blueprints",
                "rules.global_settings",
                "rules.group_types",
                "event.create",
                "event.edit",
                "event.delete",
                "event.manage",
                "event.view_attendees",
                "event.view_packs",
                "event.assign_tickets",
                "event.manage_attendees",
                "user.view",
                "user.edit",
                "user.roles",
                "owner.promote",
                "character.view_all",
                "character.edit_all",
                "character.background_approve",
                "character.refund",
                "banking.view_all",
                "banking.manage",
                "database.backup",
                "database.restore",
                "group.view_all",
                "group.edit",
                "group.background_approve",
                "messages.view_all",
                "messages.respond",
                "messages.send_for_character",
                "messages.send_for_other",
                "template.create",
                "template.edit",
                "research.create",
                "research.edit",
                "research.delete",
                "research.assign",
                "wiki.create",
                "wiki.edit",
                "wiki.delete",
                "wiki.publish",
                "wiki.manage_sections",
                "plot.reputation_briefings",
                "downtime.manage",
            ]
            for perm_name in all_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role.add_permission(permission)
        elif role_name == "plot_team":
            # Add plot team permissions
            from models.database.permissions import Permission

            plot_permissions = [
                "wiki.create",
                "wiki.edit",
                "wiki.delete",
                "wiki.publish",
                "wiki.manage_sections",
                "plot.reputation_briefings",
            ]
            for perm_name in plot_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role.add_permission(permission)
        elif role_name == "npc":
            # Add NPC permissions - NPCs can have multiple active characters
            from models.database.permissions import Permission

            npc_permissions = [
                "character.edit_all",
                "messages.respond",
                "messages.view_all",
                "messages.send_for_character",
                "messages.send_for_other",
            ]
            for perm_name in npc_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role.add_permission(permission)
        elif role_name == "downtime_team":
            # Add downtime team permissions
            from models.database.permissions import Permission

            downtime_permissions = ["downtime.manage"]
            for perm_name in downtime_permissions:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role.add_permission(permission)

        user.role = role
        db_session.commit()


@pytest.fixture(scope="session")
def app():
    """Session-wide test `Flask` application."""
    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def db(app):
    """Function-scoped database for the tests with automatic rollback."""
    with app.app_context():
        # Create all tables for this test
        _db.create_all()

        # Start a transaction
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Create a session bound to the transaction
        from sqlalchemy.orm import scoped_session, sessionmaker

        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session

        yield _db

        # Clean up after each test
        session.remove()
        transaction.rollback()
        connection.close()
        _db.drop_all()


@pytest.fixture(scope="function")
def db_session(db):
    """Function-scoped database session with automatic rollback."""
    connection = db.engine.connect()
    transaction = connection.begin()

    from sqlalchemy.orm import scoped_session, sessionmaker

    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    db.session = session

    yield session

    session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(app, db):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def new_user(db):
    """Fixture for creating a new user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"test.user.{unique_id}@example.com",
        first_name="Test",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def authenticated_user(test_client, new_user):
    """Fixture for an authenticated user."""
    with test_client.session_transaction() as session:
        session["_user_id"] = new_user.id
        session["_fresh"] = True
    return new_user


@pytest.fixture(scope="function")
def admin_user(db, authenticated_user):
    """Fixture for an authenticated admin user."""
    assign_role_to_user(authenticated_user, "admin", db.session)
    return authenticated_user


@pytest.fixture(scope="function")
def character(db_session, new_user, species):
    """Fixture for creating a character for the new_user."""
    c = Character(
        user_id=new_user.id,
        name="Test Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def downtime_period(db_session):
    """Fixture for creating a downtime period."""
    period = DowntimePeriod(status=DowntimeStatus.PENDING)
    db_session.add(period)
    db_session.commit()
    return period


@pytest.fixture(scope="function")
def research_project(db_session):
    """Fixture for creating a research project."""
    project = Research(project_name="Test Project", type="artefact")
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture(scope="function")
def downtime_pack(db_session, character, downtime_period):
    """Fixture for creating a downtime pack for a character."""
    pack = DowntimePack(
        character_id=character.id,
        period_id=downtime_period.id,
        status=DowntimeTaskStatus.ENTER_DOWNTIME,
    )
    db_session.add(pack)
    db_session.commit()
    return pack


@pytest.fixture(scope="function")
def character_research(db_session, character, research_project):
    """Fixture for assigning a character to a research project."""
    cr = CharacterResearch(character_id=character.id, research_id=research_project.id)
    db_session.add(cr)
    db_session.commit()
    return cr


@pytest.fixture(scope="function")
def skill(db_session):
    """Fixture for creating a basic skill."""
    unique_id = uuid.uuid4().hex
    s = Skill(
        name=f"Test Skill {unique_id}",
        description="A skill for testing",
        base_cost=5,
        skill_type="GENERAL",
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture(scope="function")
def species(db_session, faction):
    """Fixture for creating a basic species."""
    unique_id = uuid.uuid4().hex
    s = Species(
        name=f"Test Species {unique_id}",
        wiki_page=f"test-species-{unique_id}",
        permitted_factions=f"[{faction.id}]",
        body_hits_type="locational",
        body_hits=5,
        death_count=3,
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture(scope="function")
def faction(db_session):
    """Fixture for creating a basic faction."""
    unique_id = uuid.uuid4().hex
    f = Faction(
        name=f"Test Faction {unique_id}",
        wiki_slug=f"test-faction-{unique_id}",
        allow_player_characters=True,
    )
    db_session.add(f)
    db_session.commit()
    return f


@pytest.fixture(scope="function")
def npc_user(db_session):
    """Fixture for creating an NPC user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"npc.user.{unique_id}@example.com",
        first_name="NPC",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    assign_role_to_user(user, "npc", db_session)
    return user


@pytest.fixture(scope="function")
def npc_user_with_chars(db_session, npc_user, species, group):
    """Fixture for creating an NPC user with multiple active characters with groups."""
    char1 = Character(
        name="NPC Char 1",
        user_id=npc_user.id,
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        group_id=group.id,
    )
    char2 = Character(
        name="NPC Char 2",
        user_id=npc_user.id,
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        group_id=group.id,
    )
    db_session.add_all([char1, char2])
    db_session.commit()
    return npc_user, char1, char2


@pytest.fixture(scope="function")
def npc_user_with_chars_no_groups(db_session, npc_user, species, faction):
    """Fixture for creating an NPC user with multiple active characters without groups."""
    char1 = Character(
        name="NPC Char 1",
        user_id=npc_user.id,
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    char2 = Character(
        name="NPC Char 2",
        user_id=npc_user.id,
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    db_session.add_all([char1, char2])
    db_session.commit()
    return npc_user, char1, char2


@pytest.fixture(scope="function")
def sample_user(db_session):
    """Fixture for creating a sample user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"sample.user.{unique_id}@example.com",
        first_name="Sample",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def sample_character(db_session, sample_user, species):
    """Fixture for creating a sample character."""
    c = Character(
        user_id=sample_user.id,
        name="Sample Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def regular_user(db_session):
    """Fixture for creating a regular user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"regular.user.{unique_id}@example.com",
        first_name="Regular",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def rules_team_user(db):
    """Fixture for creating a rules team user."""
    # Initialize permissions first
    initialize_test_permissions(db.session)

    unique_id = uuid.uuid4()
    user = User(
        email=f"rules.team.{unique_id}@example.com",
        first_name="Rules",
        surname="Team",
        email_verified=True,
    )
    user.set_password("password")
    db.session.add(user)

    # Create or get the rules_team role
    role = Role.query.filter_by(name="rules_team").first()
    if not role:
        role = Role(name="rules_team", description="Test rules team role")
        db.session.add(role)
        db.session.commit()

        # Assign permissions to rules_team role
        from models.database.permissions import Permission

        rules_permissions = [
            "rules.conditions",
            "rules.skills",
            "rules.species",
            "rules.cybernetics",
            "rules.exotic_substances",
            "rules.factions",
            "rules.items",
            "rules.medicaments",
            "rules.mods",
            "rules.item_types",
            "rules.item_blueprints",
            "rules.global_settings",
            "rules.group_types",
        ]
        # Add sample permissions
        sample_permissions = ["view_samples", "add_samples", "edit_samples", "delete_samples"]
        # Add event permissions
        event_permissions = ["event.create", "event.edit", "event.delete"]
        # Add research permissions
        research_permissions = ["research.create"]
        all_permissions = (
            rules_permissions + sample_permissions + event_permissions + research_permissions
        )
        for perm_name in all_permissions:
            permission = Permission.query.filter_by(name=perm_name).first()
            if permission:
                role.add_permission(permission)

    user.role = role
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def user_rules_team(db):
    """Fixture for creating a user with rules team role."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"user.rules.team.{unique_id}@example.com",
        first_name="User",
        surname="Rules Team",
        email_verified=True,
    )
    user.set_password("password")
    assign_role_to_user(user, "rules_team", db.session)
    return user


@pytest.fixture(scope="function")
def downtime_team_user(db_session):
    """Fixture for creating a downtime team user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"downtime.team.{unique_id}@example.com",
        first_name="Downtime",
        surname="Team",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    assign_role_to_user(user, "downtime_team", db_session)
    return user


@pytest.fixture(scope="function")
def other_user(db_session):
    """Fixture for creating another user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"other.user.{unique_id}@example.com",
        first_name="Other",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def item_type(db):
    """Fixture for creating a basic item type."""
    unique_id = uuid.uuid4().hex
    it = ItemType(name=f"Test Item Type {unique_id}", id_prefix="IT")
    db.session.add(it)
    db.session.commit()
    return it


@pytest.fixture(scope="function")
def item_blueprint(db, item_type):
    """Fixture for creating a basic item blueprint."""
    unique_id = uuid.uuid4().hex
    ib = ItemBlueprint(
        name=f"Test Blueprint {unique_id}",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=10,
    )
    db.session.add(ib)
    db.session.commit()
    return ib


@pytest.fixture(scope="function")
def item(db, item_blueprint):
    """Fixture for creating a basic item."""
    i = Item(
        blueprint_id=item_blueprint.id,
        item_id=1,
    )
    db.session.add(i)
    db.session.commit()
    return i


@pytest.fixture(scope="function")
def exotic_substance(db):
    """Fixture for creating a basic exotic substance."""
    unique_id = uuid.uuid4().hex
    es = ExoticSubstance(
        name=f"Test Substance {unique_id}",
        type=ScienceType.GENERIC.value,
        wiki_slug=f"test-substance-{unique_id}",
    )
    db.session.add(es)
    db.session.commit()
    return es


@pytest.fixture(scope="function")
def sample_tag(db_session):
    """Fixture for creating a basic sample tag."""
    unique_id = uuid.uuid4().hex
    st = SampleTag(name=f"Test Tag {unique_id}")
    db_session.add(st)
    db_session.commit()
    return st


@pytest.fixture(scope="function")
def sample(db_session, sample_tag):
    """Fixture for creating a basic sample."""
    unique_id = uuid.uuid4().hex
    s = Sample(
        name=f"Test Sample {unique_id}",
        description="A test sample",
        type=ScienceType.GENERIC.value,
        tags=[sample_tag],
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture(scope="function")
def condition(db_session):
    """Fixture for creating a basic condition."""
    unique_id = uuid.uuid4().hex
    c = Condition(
        name=f"Test Condition {unique_id}",
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def cybernetic(db_session):
    """Fixture for creating a basic cybernetic."""
    unique_id = uuid.uuid4().hex
    c = Cybernetic(
        name=f"Test Cybernetic {unique_id}",
        neural_shock_value=5,
        wiki_slug=f"test-cybernetic-{unique_id}",
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def mod(db_session, item_type):
    """Fixture for creating a basic mod."""
    unique_id = uuid.uuid4().hex
    m = Mod(
        name=f"Test Mod {unique_id}",
        wiki_slug=f"test-mod-{unique_id}",
    )
    # Use merge to handle session conflicts
    item_type_merged = db_session.merge(item_type)
    m.item_types.append(item_type_merged)
    db_session.add(m)
    db_session.commit()
    return m


@pytest.fixture(scope="function")
def mod_obj(db_session, item_type):
    """Fixture for creating a mod object."""
    unique_id = uuid.uuid4().hex
    m = Mod(
        name=f"Test Mod Object {unique_id}",
        wiki_slug=f"test-mod-{unique_id}",
    )
    # Use merge to handle session conflicts
    item_type_merged = db_session.merge(item_type)
    m.item_types.append(item_type_merged)
    db_session.add(m)
    db_session.commit()
    return m


@pytest.fixture(scope="function")
def character_with_faction(db_session, regular_user, faction, species):
    """Fixture for creating a character with a faction."""
    c = Character(
        user_id=regular_user.id,
        name="Faction Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
        bank_account=500,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def admin_character(db_session, regular_user, faction, species):
    """Fixture for creating an admin character."""
    c = Character(
        user_id=regular_user.id,
        name="Admin Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
        bank_account=500,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def downtime_pack_enter_downtime(db_session, downtime_period, character_with_faction):
    """Fixture for creating a downtime pack in enter downtime status."""
    pack = DowntimePack(
        character_id=character_with_faction.id,
        period_id=downtime_period.id,
        status=DowntimeTaskStatus.ENTER_DOWNTIME,
    )
    db_session.add(pack)
    db_session.commit()
    return pack


@pytest.fixture(scope="function")
def research_project_with_stage(db_session):
    """Fixture for creating a research project with a stage."""
    project = Research(project_name="Test Project with Stage", type="artefact")
    db_session.add(project)
    db_session.commit()

    stage = ResearchStage(
        research_id=project.id,
        name="Test Stage",
        description="A test stage",
        stage_number=1,
    )
    db_session.add(stage)
    db_session.commit()

    return project


@pytest.fixture(scope="function")
def research_stage(db_session, research_project_with_stage):
    """Fixture for creating a research stage."""
    stage = ResearchStage(
        research_id=research_project_with_stage.id,
        name="Test Stage 2",
        description="A test stage",
        stage_number=2,
    )
    db_session.add(stage)
    db_session.commit()
    return stage


@pytest.fixture(scope="function")
def character_research_with_stage(
    db_session, character_with_faction, research_project_with_stage, research_stage
):
    """Fixture for assigning a character to a research project with stage."""
    cr = CharacterResearch(
        character_id=character_with_faction.id,
        research_id=research_project_with_stage.id,
    )
    db_session.add(cr)
    db_session.commit()

    crs = CharacterResearchStage(
        character_research_id=cr.id,
        stage_id=research_stage.id,
    )
    db_session.add(crs)
    db_session.commit()

    return cr


@pytest.fixture(scope="function")
def user_admin(db_session):
    """Fixture for creating an admin user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"admin.user.{unique_id}@example.com",
        first_name="Admin",
        surname="User",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    assign_role_to_user(user, "admin", db_session)
    return user


@pytest.fixture(scope="function")
def verified_login(test_client, rules_team_user):
    """Fixture for a verified login session."""
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True
    return rules_team_user


@pytest.fixture(scope="function")
def character_tag(db_session):
    """Fixture for creating a character tag."""
    unique_id = uuid.uuid4().hex
    ct = CharacterTag(name=f"Test Character Tag {unique_id}")
    db_session.add(ct)
    db_session.commit()
    return ct


@pytest.fixture(scope="function")
def prerequisite_skill(db_session):
    """Fixture for creating a prerequisite skill."""
    unique_id = uuid.uuid4().hex
    ps = Skill(
        name=f"Prerequisite Skill {unique_id}",
        description="A prerequisite skill for testing",
        base_cost=3,
        skill_type="GENERAL",
    )
    db_session.add(ps)
    db_session.commit()
    return ps


@pytest.fixture(scope="function")
def event(db_session):
    """Fixture for creating a bookable event."""
    event = Event(
        event_number="TEST999",
        name="Test Event",
        event_type="mainline",
        description="A test event for ticket purchasing.",
        early_booking_deadline=datetime.now() + timedelta(days=30),
        booking_deadline=datetime.now() + timedelta(days=40),
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db_session.add(event)
    db_session.commit()
    return event


@pytest.fixture(scope="function")
def group_type(db_session):
    """Fixture for creating a basic group type."""
    unique_id = uuid.uuid4().hex
    gt = GroupType(
        name=f"Test Group Type {unique_id}",
        description="A test group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=False,
        income_substance_cost=0,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={"items": 50, "chits": 50},
    )
    db_session.add(gt)
    db_session.commit()
    return gt


def create_test_group(
    db_session, group_type, name=None, bank_account=0, is_active=True, faction=None
):
    """Helper function to create a test group with a faction."""
    unique_id = uuid.uuid4().hex

    if faction is None:
        # Create a test faction
        from models.database.faction import Faction

        faction = Faction(
            name=f"Test Faction {unique_id}",
            wiki_slug=f"test-faction-{unique_id}",
            allow_player_characters=True,
        )
        db_session.add(faction)
        db_session.flush()  # Get the faction ID

    group_name = name or f"Test Group {unique_id}"
    g = Group(
        name=group_name,
        group_type_id=group_type.id,
        faction_id=faction.id,
        bank_account=bank_account,
        is_active=is_active,
    )
    db_session.add(g)
    db_session.flush()  # Get the group ID
    return g


@pytest.fixture(scope="function")
def group(db_session, group_type):
    """Fixture for creating a basic group."""
    unique_id = uuid.uuid4().hex

    # Create a test faction
    from models.database.faction import Faction

    faction = Faction(
        name=f"Test Faction {unique_id}",
        wiki_slug=f"test-faction-{unique_id}",
        allow_player_characters=True,
    )
    db_session.add(faction)
    db_session.flush()  # Get the faction ID

    g = Group(
        name=f"Test Group {unique_id}",
        group_type_id=group_type.id,
        faction_id=faction.id,
        bank_account=500,
    )
    db_session.add(g)
    db_session.commit()
    return g


@pytest.fixture(scope="function")
def character_with_group(db_session, regular_user, faction, species, group):
    """Fixture for creating a character with a group."""
    c = Character(
        user_id=regular_user.id,
        name="Group Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
        bank_account=500,
        group_id=group.id,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(scope="function")
def medicament(db_session):
    """Fixture for creating a basic medicament."""
    unique_id = uuid.uuid4().hex
    m = Medicament(
        name=f"Test Medicament {unique_id}",
        wiki_slug=f"test-medicament-{unique_id}",
    )
    db_session.add(m)
    db_session.commit()
    return m


@pytest.fixture(scope="function")
def item_blueprint_obj(db_session, item_type):
    """Fixture for creating an item blueprint object."""
    unique_id = uuid.uuid4().hex
    ib = ItemBlueprint(
        name=f"Test Blueprint Object {unique_id}",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=20,
        purchaseable=True,
    )
    db_session.add(ib)
    db_session.commit()
    return ib


@pytest.fixture(scope="function")
def plot_team_user(db_session):
    """Fixture for creating a plot team user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"plot.team.{unique_id}@example.com",
        first_name="Plot",
        surname="Team",
        email_verified=True,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    assign_role_to_user(user, "plot_team", db_session)
    return user


@pytest.fixture(scope="function")
def authenticated_plot_team_user(test_client, plot_team_user):
    """Fixture for an authenticated plot team user."""
    with test_client.session_transaction() as session:
        session["_user_id"] = plot_team_user.id
        session["_fresh"] = True
    return plot_team_user


@pytest.fixture(scope="function")
def authenticated_rules_team_user(test_client, user_rules_team):
    """Fixture for an authenticated rules team user."""
    with test_client.session_transaction() as session:
        session["_user_id"] = user_rules_team.id
        session["_fresh"] = True
    return user_rules_team


@pytest.fixture(scope="function")
def wiki_index_page(db_session):
    """Fixture for creating a wiki index page."""
    page = WikiPage(
        title="Test Index Page",
        slug="index",
    )
    db_session.add(page)
    db_session.commit()

    # Create a version for the page
    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
    )
    db_session.add(version)
    db_session.commit()

    # Create a section with content
    section = WikiSection(
        version_id=version.id,
        id=1,
        order=0,
        title="Test Section",
        content="Test content",
    )
    db_session.add(section)
    db_session.commit()

    return page


@pytest.fixture(scope="function")
def print_template_obj(db_session, new_user):
    """Fixture for creating a print template object."""
    from models.enums import PrintTemplateType

    unique_id = uuid.uuid4().hex
    pt = PrintTemplate(
        type_name=f"Test Print Template {unique_id}",
        type=PrintTemplateType.ITEM_CARD.value,
        front_html="<div>Front Template</div>",
        back_html="<div>Back Template</div>",
        css_styles="body { font-family: Arial; }",
        created_by_user_id=new_user.id,
    )
    db_session.add(pt)
    db_session.commit()
    return pt
