import pytest
from app import create_app
from models.extensions import db as _db
from config import TestConfig
from models.tools.user import User
from models.tools.character import Character
from models.tools.downtime import DowntimePeriod, DowntimePack
from models.enums import DowntimeStatus, DowntimeTaskStatus
from models.tools.research import Research, CharacterResearch
import uuid

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """A database for the tests."""
    with app.app_context():
        yield _db
        # The transaction is rolled back after each test
        _db.session.rollback()

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
def character(db, new_user):
    """Fixture for creating a character for the new_user."""
    c = Character(
        user_id=new_user.id,
        name='Test Character',
        status='Active'
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