import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from config import TestConfig

# Database and extensions
from models.extensions import db as _db
from models.wiki import WikiPage, WikiPageVersion, WikiSection, WikiImage, WikiChangeLog, WikiTag, wiki_changelog_versions, wiki_page_tags
from models.event import Event
from models.enums import CharacterStatus, DowntimeStatus, DowntimeTaskStatus, ScienceType, Role, GroupType
from models.database.skills import Skill
from models.database.species import Ability, Species
from models.database.faction import Faction
from models.database.item import Item, item_mods_applied
from models.database.mods import Mod, mod_type_restrictions
from models.database.item_blueprint import ItemBlueprint, item_blueprint_mods
from models.database.conditions import ConditionStage, Condition
from models.database.cybernetic import Cybernetic, CharacterCybernetic
from models.database.exotic_substances import ExoticSubstance
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.tools.downtime import DowntimePeriod, DowntimePack
from models.tools.user import User
from models.tools.character import CharacterTag, CharacterSkill, Character, CharacterAuditLog, CharacterReputation, CharacterCondition, character_tags, setup_relationships
from models.tools.role import user_roles
from models.tools.sample import SampleTag, Sample, sample_sample_tags
from models.tools.research import Research, ResearchStage, ResearchStageRequirement, CharacterResearch, CharacterResearchStage, CharacterResearchStageRequirement
from models.tools.group import Group, GroupInvite
from models.tools.message import Message
from models.tools.print_template import PrintTemplate
from models.tools.event_ticket import EventTicket

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app = create_app(TestConfig)
    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def db(app):
    """A database for the tests."""
    with app.app_context():
        setup_relationships()
        # Create all tables for this test
        _db.create_all()
        yield _db
        # Clean up after each test
        _db.session.close()
        _db.drop_all()

@pytest.fixture(scope='function')
def test_client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def new_user(db):
    """Fixture for creating a new user and adding them to the database."""
    unique_id = uuid.uuid4()
    user = User(
        email=f'test.user.{unique_id}@example.com',
        first_name='Test',
        surname='User',
        email_verified=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def authenticated_user(test_client, new_user):
    """Fixture for an authenticated user."""
    with test_client.session_transaction() as session:
        session['_user_id'] = new_user.id
        session['_fresh'] = True
    return new_user

@pytest.fixture(scope='function')
def admin_user(db, authenticated_user):
    """Fixture for an authenticated admin user."""
    authenticated_user.add_role('admin')
    db.session.add(authenticated_user)
    db.session.commit()
    return authenticated_user

@pytest.fixture(scope='function')
def character(db, new_user, species):
    """Fixture for creating a character for the new_user."""
    c = Character(
        user_id=new_user.id,
        name='Test Character',
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id
    )
    db.session.add(c)
    db.session.commit()
    return c

@pytest.fixture(scope='function')
def downtime_period(db):
    """Fixture for creating a downtime period."""
    period = DowntimePeriod(status=DowntimeStatus.PENDING)
    db.session.add(period)
    db.session.commit()
    return period

@pytest.fixture(scope='function')
def research_project(db):
    """Fixture for creating a research project."""
    project = Research(project_name='Test Project', type='artefact')
    db.session.add(project)
    db.session.commit()
    return project

@pytest.fixture(scope='function')
def downtime_pack(db, character, downtime_period):
    """Fixture for creating a downtime pack for a character."""
    pack = DowntimePack(
        character_id=character.id,
        period_id=downtime_period.id,
        status=DowntimeTaskStatus.ENTER_DOWNTIME
    )
    db.session.add(pack)
    db.session.commit()
    return pack

@pytest.fixture(scope='function')
def character_research(db, character, research_project):
    """Fixture for assigning a character to a research project."""
    cr = CharacterResearch(
        character_id=character.id,
        research_id=research_project.id
    )
    db.session.add(cr)
    db.session.commit()
    return cr

@pytest.fixture(scope='function')
def skill(db):
    """Fixture for creating a basic skill."""
    unique_id = uuid.uuid4().hex
    s = Skill(name=f'Test Skill {unique_id}', description='A skill for testing', base_cost=5, skill_type='GENERAL')
    db.session.add(s)
    db.session.commit()
    return s

@pytest.fixture(scope='function')
def species(db, faction):
    """Fixture for creating a basic species."""
    unique_id = uuid.uuid4().hex
    s = Species(
        name=f'Test Species {unique_id}', 
        wiki_page=f'test-species-{unique_id}',
        permitted_factions=f'[{faction.id}]',
        body_hits_type='locational',
        body_hits=5,
        death_count=3
    )
    db.session.add(s)
    db.session.commit()
    return s

@pytest.fixture(scope='function')
def faction(db):
    """Fixture for creating a basic faction."""
    unique_id = uuid.uuid4().hex
    f = Faction(name=f'Test Faction {unique_id}', wiki_slug=f'test-faction-{unique_id}', allow_player_characters=True)
    db.session.add(f)
    db.session.commit()
    return f

@pytest.fixture(scope='function')
def npc_user(db):
    """Fixture for creating an NPC user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f'npc.user.{unique_id}@example.com',
        first_name='NPC',
        surname='User',
        email_verified=True
    )
    user.set_password('password')
    user.add_role('npc')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def sample_user(db):
    """Fixture for creating a sample user."""
    unique_id = uuid.uuid4()
    user = User(
        email=f'sample.user.{unique_id}@example.com',
        first_name='Sample',
        surname='User',
        email_verified=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def sample_character(db, sample_user, species):
    """Fixture for creating a sample character."""
    c = Character(
        user_id=sample_user.id,
        name='Sample Character',
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id
    )
    db.session.add(c)
    db.session.commit()
    return c

@pytest.fixture(scope='function')
def regular_user(db):
    """Create a regular user without special permissions."""
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Regular",
        surname="User"
    )
    user.username = f"user_{uuid.uuid4().hex[:8]}"
    if hasattr(user, 'set_password'):
        user.set_password('password123')
    else:
        user.password = 'password123'
    user.roles = ''
    db.session.add(user)
    db.session.commit()
    return user

# Additional common fixtures to consolidate duplications

@pytest.fixture(scope='function')
def rules_team_user(db):
    """Create a user with rules team role."""
    user = User(
        email=f"rules_team_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Rules",
        surname="Team"
    )
    user.username = f"rules_team_{uuid.uuid4().hex[:8]}"
    if hasattr(user, 'set_password'):
        user.set_password('password123')
    else:
        user.password = 'password123'
    user.roles = Role.RULES_TEAM.value
    user.player_id = uuid.uuid4().int >> 96
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def user_rules_team(db):
    """Create a user with rules team role (alternative name)."""
    user = User(
        email=f"rules_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Rules",
        surname="Team"
    )
    user.username = f"rules_{uuid.uuid4().hex[:8]}"
    user.set_password('password123')
    user.roles = Role.RULES_TEAM.value
    user.player_id = uuid.uuid4().int >> 96
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def downtime_team_user(db):
    """Create a user with downtime team role."""
    user = User(
        email=f"downtime_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Downtime",
        surname="Team"
    )
    user.username = f"downtime_{uuid.uuid4().hex[:8]}"
    user.set_password('password123')
    user.roles = Role.DOWNTIME_TEAM.value
    user.player_id = uuid.uuid4().int >> 96
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def other_user(db):
    """Create another regular user."""
    user = User(
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Other",
        surname="User"
    )
    user.username = f"other_{uuid.uuid4().hex[:8]}"
    user.set_password('password123')
    user.player_id = uuid.uuid4().int >> 96
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def item_type(db):
    """Create a test item type."""
    item_type = ItemType(
        name=f"Test Item Type {uuid.uuid4().hex[:8]}",
        id_prefix="IT"
    )
    db.session.add(item_type)
    db.session.commit()
    return item_type

@pytest.fixture(scope='function')
def item_blueprint(db, item_type):
    """Create a test item blueprint."""
    blueprint = ItemBlueprint(
        name=f"Test Blueprint {uuid.uuid4().hex[:8]}",
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100
    )
    db.session.add(blueprint)
    db.session.commit()
    return blueprint

@pytest.fixture(scope='function')
def item(db, item_blueprint):
    """Create a test item."""
    item = Item(blueprint_id=item_blueprint.id, item_id=1)
    db.session.add(item)
    db.session.commit()
    return item

@pytest.fixture(scope='function')
def exotic_substance(db):
    """Create a test exotic substance."""
    exotic = ExoticSubstance(
        name=f"Test Exotic {uuid.uuid4().hex[:8]}",
        type="generic",
        wiki_slug=f"test-exotic-{uuid.uuid4().hex[:8]}"
    )
    db.session.add(exotic)
    db.session.commit()
    return exotic

@pytest.fixture(scope='function')
def sample_tag(db):
    """Create a test sample tag."""
    tag = SampleTag(name=f"Test Tag {uuid.uuid4().hex[:8]}")
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture(scope='function')
def sample(db, sample_tag):
    """Create a test sample."""
    sample = Sample(
        name=f"Test Sample {uuid.uuid4().hex[:8]}",
        type=ScienceType.GENERIC.value
    )
    db.session.add(sample)
    db.session.commit()
    sample.tags.append(sample_tag)
    db.session.commit()
    return sample

@pytest.fixture(scope='function')
def condition(db):
    """Create a test condition."""
    cond = Condition(name=f"Test Condition {uuid.uuid4().hex[:8]}")
    db.session.add(cond)
    db.session.commit()
    return cond

@pytest.fixture(scope='function')
def cybernetic(db):
    """Create a test cybernetic."""
    cyber = Cybernetic(
        name=f"Test Cybernetic {uuid.uuid4().hex[:8]}",
        neural_shock_value=1,
        adds_engineering_mods=0,
        adds_engineering_downtime=0,
        adds_science_downtime=0,
        science_type=ScienceType.GENERIC.value,
        wiki_slug=f"test-cybernetic-{uuid.uuid4().hex[:8]}"
    )
    db.session.add(cyber)
    db.session.commit()
    return cyber

@pytest.fixture(scope='function')
def mod(db):
    """Create a test mod."""
    from models.database.mods import Mod
    unique_name = f"Test Mod {uuid.uuid4().hex[:8]}"
    unique_slug = f"test-mod-{uuid.uuid4().hex[:8]}"
    mod = Mod(
        name=unique_name,
        wiki_slug=unique_slug
    )
    db.session.add(mod)
    db.session.commit()
    return mod

@pytest.fixture(scope='function')
def character_with_faction(db, regular_user, faction, species):
    """Create a character with faction for the regular_user."""
    character = Character(
        user_id=regular_user.id,
        name=f"Test Character {uuid.uuid4().hex[:8]}",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
        bank_account=500
    )
    db.session.add(character)
    db.session.commit()
    return character

@pytest.fixture(scope='function')
def admin_character(db, regular_user, faction, species):
    """Create an admin character and its user in the same session as regular_user."""
    from models.tools.user import User
    from models.enums import Role
    admin_user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Admin",
        surname="User"
    )
    admin_user.username = f"admin_{uuid.uuid4().hex[:8]}"
    admin_user.set_password('password123')
    admin_user.roles = Role.USER_ADMIN.value
    db.session.add(admin_user)
    db.session.commit()
    unique_id = uuid.uuid4().hex[:8]
    character = Character(
        user_id=admin_user.id,
        name=f"Admin Character {unique_id}",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
        bank_account=1000
    )
    db.session.add(character)
    db.session.commit()
    return character

@pytest.fixture(scope='function')
def downtime_pack_enter_downtime(db, downtime_period, character_with_faction):
    """Create a downtime pack in ENTER_DOWNTIME status."""
    pack = DowntimePack(
        period_id=downtime_period.id,
        character_id=character_with_faction.id,
        status=DowntimeTaskStatus.ENTER_DOWNTIME
    )
    db.session.add(pack)
    db.session.commit()
    return pack

@pytest.fixture(scope='function')
def research_project_with_stage(db):
    """Create a research project with a stage."""
    unique_id = uuid.uuid4().hex[:8]
    research = Research(
        project_name=f"Test Research {unique_id}",
        type="invention",
        description="Test research description"
    )
    db.session.add(research)
    db.session.flush()
    # Always create a stage for the research
    from models.tools.research import ResearchStage
    stage = ResearchStage(
        research_id=research.id,
        stage_number=1,
        name="Test Stage",
        description="Test stage description"
    )
    db.session.add(stage)
    db.session.commit()
    return research

@pytest.fixture(scope='function')
def research_stage(db, research_project_with_stage):
    """Get the first stage for a research project."""
    from models.tools.research import ResearchStage
    return ResearchStage.query.filter_by(research_id=research_project_with_stage.id).first()

@pytest.fixture(scope='function')
def character_research_with_stage(db, character_with_faction, research_project_with_stage, research_stage):
    """Fixture for assigning a character to a research project with a stage."""
    cr = CharacterResearch(
        character_id=character_with_faction.id,
        research_id=research_project_with_stage.id,
        current_stage_id=research_stage.id
    )
    db.session.add(cr)
    db.session.commit()
    return cr

# Additional fixtures to consolidate duplications found across test files

@pytest.fixture(scope='function')
def user_admin(db):
    """Create a user with user_admin role."""
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        email_verified=True,
        first_name="Admin",
        surname="User"
    )
    user.username = f"admin_{uuid.uuid4().hex[:8]}"
    user.set_password('password123')
    user.roles = Role.USER_ADMIN.value
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def verified_login(test_client, rules_team_user):
    """Fixture for verified login with rules team user."""
    test_client.post('/auth/login', data={
        'email': rules_team_user.email,
        'password': 'password123',
    }, follow_redirects=True)
    return rules_team_user

@pytest.fixture(scope='function')
def character_tag(db):
    """Create a test character tag."""
    from models.tools.character import CharacterTag
    tag = CharacterTag(
        name=f"Test Tag {uuid.uuid4().hex[:8]}"
    )
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture(scope='function')
def prerequisite_skill(db):
    """Create a prerequisite skill."""
    skill = Skill(
        name=f"Prerequisite Skill {uuid.uuid4().hex[:8]}",
        description="Prerequisite skill description",
        skill_type="GENERAL",
        base_cost=5,
        can_purchase_multiple=False,
        cost_increases=False
    )
    db.session.add(skill)
    db.session.commit()
    return skill

@pytest.fixture(scope='function')
def group(db):
    """Create a test group."""
    from models.tools.group import Group
    from models.enums import GroupType
    unique_id = uuid.uuid4().hex[:8]
    group = Group(
        name=f"Test Group {unique_id}",
        type=GroupType.MILITARY.value,
        bank_account=500
    )
    db.session.add(group)
    db.session.commit()
    return group

@pytest.fixture(scope='function')
def character_with_group(db, regular_user, faction, species, group):
    """Create a test character that belongs to a group."""
    unique_id = uuid.uuid4().hex[:8]
    character = Character(
        user_id=regular_user.id,
        name=f"Group Character {unique_id}",
        status=CharacterStatus.ACTIVE.value,
        faction_id=faction.id,
        species_id=species.id,
        group_id=group.id,
        bank_account=500
    )
    db.session.add(character)
    db.session.commit()
    return character

@pytest.fixture(scope='function')
def medicament(db):
    """Create a test medicament."""
    from models.database.medicaments import Medicament
    unique_name = f"Medicament {uuid.uuid4()}"
    unique_slug = f"medicament-{uuid.uuid4()}"
    medicament = Medicament(
        name=unique_name,
        wiki_slug=unique_slug
    )
    db.session.add(medicament)
    db.session.commit()
    return medicament

@pytest.fixture(scope='function')
def item_blueprint_obj(db, item_type):
    """Create a test item blueprint with mods."""
    from models.database.mods import Mod
    unique_name = f"Blueprint {uuid.uuid4()}"
    mod = Mod(
        name=f"Mod {uuid.uuid4()}",
        wiki_slug=f"mod-{uuid.uuid4()}"
    )
    mod.item_types.append(item_type)
    db.session.add(mod)
    
    blueprint = ItemBlueprint(
        name=unique_name,
        item_type_id=item_type.id,
        blueprint_id=1,
        base_cost=100
    )
    blueprint.mods_applied.append(mod)
    db.session.add(blueprint)
    db.session.commit()
    return blueprint

@pytest.fixture(scope='function')
def mod_obj(db, item_type):
    """Create a test mod with item types."""
    unique_name = f"Mod {uuid.uuid4()}"
    unique_slug = f"mod-{uuid.uuid4()}"
    mod = Mod(
        name=unique_name,
        wiki_slug=unique_slug
    )
    mod.item_types.append(item_type)
    db.session.add(mod)
    db.session.commit()
    return mod

@pytest.fixture(scope='function')
def plot_team_user(db, new_user):
    """Fixture for creating a plot team user."""
    new_user.add_role(Role.PLOT_TEAM.value)
    db.session.commit()
    return new_user

@pytest.fixture(scope='function')
def authenticated_plot_team_user(test_client, plot_team_user):
    """Fixture for an authenticated plot team user."""
    with test_client.session_transaction() as session:
        session['_user_id'] = plot_team_user.id
        session['_fresh'] = True
    return plot_team_user

@pytest.fixture(scope='function')
def wiki_index_page(db):
    from models.wiki import WikiPage, WikiPageVersion, WikiPageVersionStatus, WikiSection
    wiki_page = WikiPage(slug="index", title="Index Page")
    db.session.add(wiki_page)
    db.session.flush()
    version = WikiPageVersion(
        page_slug=wiki_page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=1
    )
    db.session.add(version)
    db.session.flush()
    section = WikiSection(
        version_id=version.id,
        id=1,
        order=0,
        title="Welcome",
        content="Welcome to the index page!"
    )
    db.session.add(section)
    db.session.commit()
    return wiki_page 