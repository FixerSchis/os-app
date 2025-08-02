from datetime import datetime

import pytest
from flask import url_for

from models.database.faction import Faction
from models.database.reputation_briefing import ReputationBriefing, ReputationBriefingLevel
from models.enums import ReputationBriefingStatus, Role
from models.event import Event
from models.tools.character import Character, CharacterStatus
from models.tools.event_ticket import EventTicket
from models.tools.user import User


class TestReputationBriefingsRoutes:
    """Test reputation briefings routes."""

    def test_index_admin_view(self, test_client, plot_team_user, db_session):
        """Test admin view of reputation briefings."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.index"))
        assert response.status_code == 200
        assert b"Reputation Briefings" in response.data

    def test_index_user_view(self, test_client, regular_user, db_session):
        """Test user view of reputation briefings."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.index"))
        assert response.status_code == 200
        assert b"Reputation Briefings" in response.data

    def test_create_get_plot_team(self, test_client, plot_team_user, db_session):
        """Test create briefing GET for plot team user."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.create"))
        assert response.status_code == 200
        assert b"Create Reputation Briefing" in response.data

    def test_create_get_regular_user(self, test_client, regular_user, db_session):
        """Test create briefing GET for regular user (should be forbidden)."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.create"))
        assert response.status_code == 302

    def test_create_post_save_as_draft(self, test_client, plot_team_user, db_session):
        """Test creating a briefing and saving as draft."""
        # Create test data
        event = Event(
            event_number="TEST001",
            name="Test Event",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction", wiki_slug="test-faction")
        db_session.add_all([event, faction])
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        data = {
            "event_id": event.id,
            "faction_id": faction.id,
            "subject": "Test Briefing",
            "reputation_required_0": "1",
            "content_0": "Test content for reputation 1",
            "action": "save_as_draft",
        }

        response = test_client.post(url_for("reputation_briefings.create"), data=data)
        assert response.status_code == 302  # Redirect after success

        # Check that briefing was created
        briefing = ReputationBriefing.query.filter_by(subject="Test Briefing").first()
        assert briefing is not None
        assert briefing.status.value == ReputationBriefingStatus.INCOMPLETE.value
        assert len(briefing.levels) == 1
        assert briefing.levels[0].reputation_required == 1
        assert briefing.levels[0].content == "Test content for reputation 1"

    def test_create_post_save_and_send(self, test_client, plot_team_user, db_session):
        """Test creating a briefing and sending it."""
        # Create test data
        event = Event(
            event_number="TEST002",
            name="Test Event 2",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 2", wiki_slug="test-faction-2")
        db_session.add_all([event, faction])
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        data = {
            "event_id": event.id,
            "faction_id": faction.id,
            "subject": "Test Briefing 2",
            "reputation_required_0": "2",
            "content_0": "Test content for reputation 2",
            "action": "save_and_send",
        }

        response = test_client.post(url_for("reputation_briefings.create"), data=data)
        assert response.status_code == 302  # Redirect after success

        # Check that briefing was created and sent
        briefing = ReputationBriefing.query.filter_by(subject="Test Briefing 2").first()
        assert briefing is not None
        assert briefing.status.value == ReputationBriefingStatus.SUBMITTED.value
        assert len(briefing.levels) == 1
        assert briefing.levels[0].reputation_required == 2
        assert briefing.levels[0].content == "Test content for reputation 2"

    def test_create_post_missing_fields(self, test_client, plot_team_user, db_session):
        """Test creating a briefing with missing fields."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        data = {
            "event_id": "",
            "faction_id": "",
            "subject": "",
            "action": "save_as_draft",
        }

        response = test_client.post(url_for("reputation_briefings.create"), data=data)
        assert response.status_code == 302  # Redirect after error
        # Should show error message

    def test_create_post_no_levels(self, test_client, plot_team_user, db_session):
        """Test creating a briefing with no levels."""
        # Create test data
        event = Event(
            event_number="TEST003",
            name="Test Event 3",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 3", wiki_slug="test-faction-3")
        db_session.add_all([event, faction])
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        data = {
            "event_id": event.id,
            "faction_id": faction.id,
            "subject": "Test Briefing 3",
            "action": "save_as_draft",
        }

        response = test_client.post(url_for("reputation_briefings.create"), data=data)
        assert response.status_code == 302  # Redirect after error
        # Should show error message about requiring at least one level

    def test_edit_get_plot_team(self, test_client, plot_team_user, db_session):
        """Test edit briefing GET for plot team user."""
        # Create test briefing
        event = Event(
            event_number="TEST004",
            name="Test Event 4",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 4", wiki_slug="test-faction-4")
        db_session.add_all([event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 4",
            status=ReputationBriefingStatus.INCOMPLETE,
            created_by_user_id=plot_team_user.id,
        )
        level = ReputationBriefingLevel(
            reputation_required=1,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.edit", briefing_id=briefing.id))
        assert response.status_code == 200
        assert b"Edit Reputation Briefing" in response.data

    def test_edit_get_submitted_briefing(self, test_client, plot_team_user, db_session):
        """Test edit briefing GET for submitted briefing (should be forbidden)."""
        # Create test briefing
        event = Event(
            event_number="TEST005",
            name="Test Event 5",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 5", wiki_slug="test-faction-5")
        db_session.add_all([event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 5",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=plot_team_user.id,
        )

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.edit", briefing_id=briefing.id))
        assert response.status_code == 200  # Allow edit of submitted briefing

    def test_view_briefing_plot_team(self, test_client, plot_team_user, db_session):
        """Test viewing a briefing as plot team user."""
        # Create test briefing
        event = Event(
            event_number="TEST006",
            name="Test Event 6",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 6", wiki_slug="test-faction-6")
        db_session.add_all([event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 6",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=plot_team_user.id,
        )
        level = ReputationBriefingLevel(
            reputation_required=1,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.view", briefing_id=briefing.id))
        assert response.status_code == 200
        assert b"Test Briefing 6" in response.data

    def test_view_briefing_regular_user_eligible(self, test_client, regular_user, db_session):
        """Test viewing a briefing as regular user with eligible character."""
        # Create test data
        event = Event(
            event_number="TEST007",
            name="Test Event 7",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 7", wiki_slug="test-faction-7")
        character = Character(
            user_id=regular_user.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )

        db_session.add_all([event, faction, character])
        db_session.commit()

        # Create character reputation with committed character ID
        from models.tools.character import CharacterReputation

        reputation = CharacterReputation(
            character_id=character.id,
            faction_id=faction.id,
            value=2,
        )

        # Create event ticket with committed character ID
        ticket = EventTicket(
            event_id=event.id,
            character_id=character.id,
            user_id=regular_user.id,
            ticket_type="adult",
            price_paid=50.0,
            assigned_by_id=regular_user.id,
        )

        # Create briefing with committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 7",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=regular_user.id,
        )
        level = ReputationBriefingLevel(
            reputation_required=1,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add_all([reputation, ticket, briefing])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 7",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=regular_user.id,
        )
        level = ReputationBriefingLevel(
            reputation_required=1,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.view", briefing_id=briefing.id))
        assert response.status_code == 200
        assert b"Test Briefing 7" in response.data

    def test_view_briefing_regular_user_not_eligible(self, test_client, regular_user, db_session):
        """Test viewing a briefing as regular user without eligible character."""
        # Create test briefing
        event = Event(
            event_number="TEST008",
            name="Test Event 8",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 8", wiki_slug="test-faction-8")
        db_session.add_all([event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 8",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=regular_user.id,
        )
        level = ReputationBriefingLevel(
            reputation_required=5,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.view", briefing_id=briefing.id))
        assert response.status_code == 302  # Redirect after error

    def test_reopen_discarded_briefing(self, test_client, plot_team_user, db_session):
        """Test reopening a discarded briefing."""
        # Create test briefing
        event = Event(
            event_number="TEST009",
            name="Test Event 9",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction 9", wiki_slug="test-faction-9")
        db_session.add_all([event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing 9",
            status=ReputationBriefingStatus.DISCARDED,
            created_by_user_id=plot_team_user.id,
        )

        db_session.add(briefing)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = plot_team_user.id
            sess["_fresh"] = True

        response = test_client.get(url_for("reputation_briefings.reopen", briefing_id=briefing.id))
        assert response.status_code == 302  # Redirect after success

        # Check that briefing was reopened - query from global session
        from models.extensions import db

        global_briefing = db.session.get(ReputationBriefing, briefing.id)
        assert global_briefing.status.value == ReputationBriefingStatus.INCOMPLETE.value


class TestReputationBriefingModels:
    """Test reputation briefing models."""

    def test_briefing_creation(self, db_session):
        """Test creating a reputation briefing."""
        user = User(email="test@example.com", first_name="Test", surname="User")
        user.set_password("password")
        event = Event(
            event_number="TEST001",
            name="Test Event",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction", wiki_slug="test-faction")

        db_session.add_all([user, event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing",
            status=ReputationBriefingStatus.INCOMPLETE,
            created_by_user_id=user.id,
        )

        level = ReputationBriefingLevel(
            reputation_required=1,
            content="Test content",
        )
        briefing.levels.append(level)

        db_session.add(briefing)
        db_session.commit()

        assert briefing.id is not None
        assert briefing.status.value == ReputationBriefingStatus.INCOMPLETE.value
        assert len(briefing.levels) == 1
        assert briefing.levels[0].reputation_required == 1

    def test_briefing_get_by_status_order(self, db_session):
        """Test getting briefings ordered by status."""
        user = User(email="test@example.com", first_name="Test", surname="User")
        user.set_password("password")
        event = Event(
            event_number="TEST001",
            name="Test Event",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction", wiki_slug="test-faction")

        db_session.add_all([user, event, faction])
        db_session.commit()

        # Now create the briefings with the committed IDs
        briefing1 = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Submitted Briefing",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=user.id,
        )
        briefing2 = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Incomplete Briefing",
            status=ReputationBriefingStatus.INCOMPLETE,
            created_by_user_id=user.id,
        )
        briefing3 = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Discarded Briefing",
            status=ReputationBriefingStatus.DISCARDED,
            created_by_user_id=user.id,
        )

        db_session.add_all([briefing1, briefing2, briefing3])
        db_session.commit()

        briefings = ReputationBriefing.get_by_status_order()

        # Should be ordered: incomplete, submitted, discarded
        assert briefings[0].status.value == ReputationBriefingStatus.INCOMPLETE.value
        assert briefings[1].status.value == ReputationBriefingStatus.SUBMITTED.value
        assert briefings[2].status.value == ReputationBriefingStatus.DISCARDED.value

    def test_briefing_can_edit(self, db_session, plot_team_user):
        """Test briefing can_edit method."""
        user = User(email="test@example.com", first_name="Test", surname="User")
        user.set_password("password")

        event = Event(
            event_number="TEST001",
            name="Test Event",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction", wiki_slug="test-faction")

        db_session.add_all([user, event, faction])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing",
            status=ReputationBriefingStatus.INCOMPLETE,
            created_by_user_id=user.id,
        )

        db_session.add(briefing)
        db_session.commit()

        # Plot team should be able to edit incomplete briefing
        assert briefing.can_edit(plot_team_user) is True

        # Regular user should not be able to edit
        assert briefing.can_edit(user) is False

        # Submitted briefing should also be editable by plot team
        briefing.status = ReputationBriefingStatus.SUBMITTED
        assert briefing.can_edit(plot_team_user) is True

    def test_briefing_get_eligible_characters(self, db_session):
        """Test getting eligible characters for a briefing."""
        user = User(email="test@example.com", first_name="Test", surname="User")
        user.set_password("password")
        event = Event(
            event_number="TEST001",
            name="Test Event",
            event_type="mainline",
            early_booking_deadline=datetime(2025, 2, 1),
            booking_deadline=datetime(2025, 2, 15),
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 3),
            standard_ticket_price=50.0,
            early_booking_ticket_price=45.0,
            child_ticket_price_12_15=25.0,
            child_ticket_price_7_11=15.0,
            child_ticket_price_under_7=0.0,
        )
        faction = Faction(name="Test Faction", wiki_slug="test-faction")

        db_session.add_all([user, event, faction])
        db_session.commit()

        # Now create characters with the committed user ID
        character1 = Character(
            user_id=user.id,
            name="Character 1",
            status=CharacterStatus.ACTIVE.value,
        )
        character2 = Character(
            user_id=user.id,
            name="Character 2",
            status=CharacterStatus.ACTIVE.value,
        )
        character3 = Character(
            user_id=user.id,
            name="Character 3",
            status=CharacterStatus.ACTIVE.value,
        )

        db_session.add_all([character1, character2, character3])
        db_session.commit()

        # Create reputations with committed character IDs
        from models.tools.character import CharacterReputation

        reputation1 = CharacterReputation(
            character_id=character1.id,
            faction_id=faction.id,
            value=3,
        )
        reputation2 = CharacterReputation(
            character_id=character2.id,
            faction_id=faction.id,
            value=1,
        )
        # Character 3 has no reputation

        # Create event tickets with committed character IDs
        ticket1 = EventTicket(
            event_id=event.id,
            character_id=character1.id,
            user_id=user.id,
            ticket_type="adult",
            price_paid=50.0,
            assigned_by_id=user.id,
        )
        ticket2 = EventTicket(
            event_id=event.id,
            character_id=character2.id,
            user_id=user.id,
            ticket_type="adult",
            price_paid=50.0,
            assigned_by_id=user.id,
        )
        # Character 3 has no ticket

        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=user.id,
        )

        # Add levels with different reputation requirements
        level1 = ReputationBriefingLevel(
            reputation_required=1,
            content="Level 1 content",
        )
        level2 = ReputationBriefingLevel(
            reputation_required=3,
            content="Level 3 content",
        )
        briefing.levels.append(level1)
        briefing.levels.append(level2)

        db_session.add_all([reputation1, reputation2, ticket1, ticket2, briefing])
        db_session.commit()

        # Now create the briefing with the committed IDs
        briefing = ReputationBriefing(
            event_id=event.id,
            faction_id=faction.id,
            subject="Test Briefing",
            status=ReputationBriefingStatus.SUBMITTED,
            created_by_user_id=user.id,
        )

        # Add levels with different reputation requirements
        level1 = ReputationBriefingLevel(
            reputation_required=1,
            content="Level 1 content",
        )
        level2 = ReputationBriefingLevel(
            reputation_required=3,
            content="Level 3 content",
        )
        briefing.levels.append(level1)
        briefing.levels.append(level2)

        db_session.add(briefing)
        db_session.commit()

        eligible_characters = briefing.get_eligible_characters()

        # Should only include characters with sufficient reputation and tickets
        assert len(eligible_characters) == 2
        character_ids = [c.id for c in eligible_characters]
        assert character1.id in character_ids
        assert character2.id in character_ids
        assert character3.id not in character_ids
