import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from models.database.cybernetic import Cybernetic
from models.database.faction import Faction
from models.database.mods import Mod
from models.database.skills import Skill
from models.database.species import Species
from models.enums import Role
from models.event import Event
from models.tools.user import User


def test_register_get(test_client, db):
    """Test GET request to registration page."""
    response = test_client.get("/auth/register")
    assert response.status_code == 200


def test_register_success_first_user(test_client, db, wiki_index_page):
    """Test successful registration of the first user (owner)."""
    # Create required default data that the registration process expects

    # Create default species
    species = Species(
        name="Ascendancy Terran",
        wiki_page="ascendancy-terran",
        permitted_factions="[]",
        body_hits_type="locational",
        body_hits=5,
        death_count=3,
    )
    db.session.add(species)

    # Create default faction
    faction = Faction(
        name="Terran Ascendancy",
        wiki_slug="terran-ascendancy",
        allow_player_characters=True,
    )
    db.session.add(faction)

    # Create a default mod
    mod = Mod(name="Default Mod", wiki_slug="default-mod")
    db.session.add(mod)

    # Create default cybernetic
    cybernetic = Cybernetic(
        name="Neural Interface", neural_shock_value=0, wiki_slug="neural-interface"
    )
    db.session.add(cybernetic)

    # Create some skills
    skill1 = Skill(name="Engineering", description="Engineering skill", base_cost=5)
    skill2 = Skill(name="Other Skill", description="Another skill", base_cost=3)
    db.session.add_all([skill1, skill2])

    # Create a default event
    event = Event(
        event_number="1",
        name="Test Event",
        event_type="mainline",
        description="A test event",
        early_booking_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        start_date=datetime.now(timezone.utc) + timedelta(days=45),
        end_date=datetime.now(timezone.utc) + timedelta(days=47),
        location="Test Location",
        standard_ticket_price=50.00,
        early_booking_ticket_price=45.00,
        child_ticket_price_12_15=25.00,
        child_ticket_price_7_11=15.00,
        child_ticket_price_under_7=0.00,
    )
    db.session.add(event)

    db.session.commit()

    with patch("routes.auth.send_verification_email"):
        response = test_client.post(
            "/auth/register",
            data={
                "email": "first_user@example.com",
                "password": "password123",
                "first_name": "Test",
                "surname": "User",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that user was created
        user = User.query.filter_by(email="first_user@example.com").first()
        assert user is not None
        assert user.first_name == "Test"
        assert user.surname == "User"
        assert user.has_role(Role.OWNER.value)
        assert user.email_verified is True
        assert user.player_id == 1


def test_register_duplicate_email(test_client, db, new_user):
    """Test registration with duplicate email."""
    response = test_client.post(
        "/auth/register",
        data={
            "email": new_user.email,
            "password": "password123",
            "first_name": "Test",
            "surname": "User",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect back to register page with flash message


def test_register_subsequent_user(test_client, db, new_user):
    """Test registration of subsequent users (not owner)."""
    with patch("routes.auth.send_verification_email") as mock_send_email:
        response = test_client.post(
            "/auth/register",
            data={
                "email": "subsequent_user@example.com",
                "password": "password123",
                "first_name": "Test2",
                "surname": "User2",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that user was created
        user = User.query.filter_by(email="subsequent_user@example.com").first()
        assert user is not None
        assert user.first_name == "Test2"
        assert user.surname == "User2"
        assert not user.has_role(Role.OWNER.value)
        assert user.email_verified is False
        # The registration logic gets the highest player_id and adds 1
        # Since new_user already exists, the new user should have player_id = max + 1
        if new_user.player_id is not None:
            assert user.player_id > new_user.player_id
        else:
            assert user.player_id is not None

        # Check that verification email was sent
        mock_send_email.assert_called_once_with(user)


def test_login_get(test_client, db):
    """Test GET request to login page."""
    response = test_client.get("/auth/login")
    assert response.status_code == 200


def test_login_success(test_client, new_user, db):
    """Test successful login."""
    response = test_client.post(
        "/auth/login",
        data={"email": new_user.email, "password": "password123"},
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_login_invalid_credentials(test_client, db):
    """Test login with invalid credentials."""
    response = test_client.post(
        "/auth/login",
        data={"email": "nonexistent@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should show flash message about invalid credentials


def test_login_unverified_email(test_client, db):
    """Test login with unverified email."""
    user = User(
        email="unverified@example.com",
        first_name="Test",
        surname="User",
        email_verified=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    response = test_client.post(
        "/auth/login",
        data={"email": "unverified@example.com", "password": "password123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect to verification required page


def test_logout(test_client, authenticated_user, db, wiki_index_page):
    """Test logout functionality."""
    response = test_client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


def test_verify_email_authenticated_success(test_client, authenticated_user, db, wiki_index_page):
    """Test email verification when user is authenticated."""
    token = authenticated_user.generate_verification_token()

    response = test_client.get(f"/auth/verify/{token}", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


@pytest.fixture
def unverified_authenticated_user(test_client, db):
    """Fixture for an authenticated user who is not email verified."""
    unique_id = uuid.uuid4()
    user = User(
        email=f"unverified.user.{unique_id}@example.com",
        first_name="Unverified",
        surname="User",
        email_verified=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True
    return user


def test_verify_email_authenticated_invalid_token(test_client, unverified_authenticated_user, db):
    """Test email verification with invalid token when authenticated."""
    response = test_client.get("/auth/verify/invalid_token", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/verification-required" in response.location


def test_verify_email_unauthenticated_success(test_client, db, wiki_index_page):
    """Test email verification when user is not authenticated."""
    user = User(
        email="verify_test@example.com",
        first_name="Test",
        surname="User",
        email_verified=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    token = user.generate_verification_token()

    response = test_client.get(f"/auth/verify/{token}", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


def test_verify_email_unauthenticated_invalid_token(test_client, db):
    """Test email verification with invalid token when not authenticated."""
    response = test_client.get("/auth/verify/invalid_token", follow_redirects=True)
    assert response.status_code == 200


def test_verification_required_authenticated_unverified(test_client, db):
    """Test verification required page when user is authenticated but not verified."""
    user = User(
        email="verification_required@example.com",
        first_name="Test",
        surname="User",
        email_verified=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True

    response = test_client.get("/auth/verification-required")
    assert response.status_code == 200


def test_verification_required_authenticated_verified(
    test_client, authenticated_user, db, wiki_index_page
):
    """Test verification required page when user is authenticated and verified."""
    response = test_client.get("/auth/verification-required", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


def test_verification_required_unauthenticated(test_client, db):
    """Test verification required page when user is not authenticated."""
    response = test_client.get("/auth/verification-required", follow_redirects=True)
    assert response.status_code == 200


def test_resend_verification_success(test_client, db):
    """Test resending verification email."""
    user = User(
        email="resend_verification@example.com",
        first_name="Test",
        surname="User",
        email_verified=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = user.id
        session["_fresh"] = True

    with patch("routes.auth.send_verification_email") as mock_send_email:
        with patch("routes.auth.current_user", user):
            response = test_client.get("/auth/resend-verification", follow_redirects=True)
            assert response.status_code == 200
            mock_send_email.assert_called_once_with(user)


def test_resend_verification_already_verified(test_client, authenticated_user, db, wiki_index_page):
    """Test resending verification email when already verified."""
    response = test_client.get("/auth/resend-verification", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


def test_forgot_password_get(test_client, db):
    """Test GET request to forgot password page."""
    response = test_client.get("/auth/forgot-password")
    assert response.status_code == 200


def test_forgot_password_success(test_client, new_user, db):
    """Test successful forgot password request."""
    with patch("routes.auth.send_password_reset_email") as mock_send_email:
        response = test_client.post(
            "/auth/forgot-password",
            data={"email": new_user.email},
            follow_redirects=True,
        )

        assert response.status_code == 200
        mock_send_email.assert_called_once_with(new_user)


def test_forgot_password_nonexistent_email(test_client, db):
    """Test forgot password with nonexistent email."""
    response = test_client.post(
        "/auth/forgot-password",
        data={"email": "nonexistent@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should show flash message about email sent (for security)


def test_forgot_password_no_email(test_client, db):
    """Test forgot password with no email."""
    response = test_client.post("/auth/forgot-password", data={}, follow_redirects=True)
    assert response.status_code == 200


def test_forgot_password_authenticated(test_client, authenticated_user, db, wiki_index_page):
    """Test forgot password when user is authenticated."""
    response = test_client.get("/auth/forgot-password", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"


def test_reset_password_get_valid_token(test_client, db):
    """Test GET request to reset password with valid token."""
    user = User(email="reset_token_test@example.com", first_name="Test", surname="User")
    user.set_password("password123")
    user.generate_reset_token()
    db.session.add(user)
    db.session.commit()

    # Mock the datetime comparison to avoid timezone issues
    with patch("routes.auth.datetime") as mock_datetime:
        mock_datetime.now.return_value = user.reset_token_expires - timedelta(hours=1)
        response = test_client.get(f"/auth/reset-password/{user.reset_token}")
        assert response.status_code == 200


def test_reset_password_get_invalid_token(test_client, db):
    """Test reset password GET with invalid token."""
    response = test_client.get("/auth/reset-password/invalid_token", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_reset_password_success(test_client, db):
    """Test successful password reset."""
    user = User(email="reset_success@example.com", first_name="Test", surname="User")
    user.set_password("oldpassword")
    user.generate_reset_token()
    db.session.add(user)
    db.session.commit()

    with patch.object(user, "reset_password", return_value=True) as mock_reset:
        with patch("routes.auth.datetime") as mock_datetime:
            mock_datetime.now.return_value = user.reset_token_expires - timedelta(hours=1)
            response = test_client.post(
                f"/auth/reset-password/{user.reset_token}",
                data={
                    "password": "newpassword123",
                    "confirm_password": "newpassword123",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            mock_reset.assert_called_once_with(user.reset_token, "newpassword123")


def test_reset_password_passwords_dont_match(test_client, db):
    """Test password reset with mismatched passwords."""
    user = User(email="reset_mismatch@example.com", first_name="Test", surname="User")
    user.set_password("oldpassword")
    user.generate_reset_token()
    db.session.add(user)
    db.session.commit()

    with patch("routes.auth.datetime") as mock_datetime:
        mock_datetime.now.return_value = user.reset_token_expires - timedelta(hours=1)
        response = test_client.post(
            f"/auth/reset-password/{user.reset_token}",
            data={
                "password": "newpassword123",
                "confirm_password": "differentpassword",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200


def test_reset_password_missing_fields(test_client, db):
    """Test password reset with missing password fields."""
    user = User(email="reset_missing@example.com", first_name="Test", surname="User")
    user.set_password("oldpassword")
    user.generate_reset_token()
    db.session.add(user)
    db.session.commit()

    with patch("routes.auth.datetime") as mock_datetime:
        mock_datetime.now.return_value = user.reset_token_expires - timedelta(hours=1)
        response = test_client.post(
            f"/auth/reset-password/{user.reset_token}", data={}, follow_redirects=True
        )
        assert response.status_code == 200


def test_reset_password_authenticated(test_client, authenticated_user, db, wiki_index_page):
    """Test reset password when user is authenticated."""
    response = test_client.get("/auth/reset-password/token", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/"
