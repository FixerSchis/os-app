from unittest.mock import patch

from models.tools.user import User


def test_settings_get(test_client, authenticated_user):
    """Test GET request to settings page."""
    response = test_client.get("/settings/")
    assert response.status_code == 200


def test_settings_update_profile(test_client, authenticated_user, db):
    """Test updating profile information."""
    response = test_client.post(
        "/settings/",
        data={
            "form_type": "profile",
            "first_name": "Updated",
            "surname": "Name",
            "pronouns_subject": "they",
            "pronouns_object": "them",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Check that user was updated by querying the database
    db.session.refresh(authenticated_user)
    assert authenticated_user.first_name == "Updated"
    assert authenticated_user.surname == "Name"
    assert authenticated_user.pronouns_subject == "they"
    assert authenticated_user.pronouns_object == "them"


def test_settings_update_notifications(test_client, authenticated_user, db):
    """Test updating notification preferences."""
    response = test_client.post(
        "/settings/",
        data={
            "form_type": "notifications",
            "notify_downtime_pack_enter": "1",
            "notify_downtime_completed": "0",
            "notify_new_event": "1",
            "notify_event_ticket_assigned": "0",
            "notify_event_details_updated": "1",
            "notify_wiki_published": "0",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Check that notification preferences were updated
    db.session.refresh(authenticated_user)
    assert authenticated_user.notify_downtime_pack_enter is True
    assert authenticated_user.notify_downtime_completed is False
    assert authenticated_user.notify_new_event is True
    assert authenticated_user.notify_event_ticket_assigned is False
    assert authenticated_user.notify_event_details_updated is True
    assert authenticated_user.notify_wiki_published is False


def test_toggle_dark_mode_endpoint(test_client, authenticated_user, db):
    """Test the toggle dark mode API endpoint."""
    # Start with dark mode enabled
    authenticated_user.dark_mode_preference = True
    db.session.commit()

    # Test toggling to light mode
    response = test_client.post("/settings/toggle-dark-mode", json={"theme": "light"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["dark_mode"] is False

    # Check database was updated
    db.session.refresh(authenticated_user)
    assert authenticated_user.dark_mode_preference is False

    # Test toggling back to dark mode
    response = test_client.post("/settings/toggle-dark-mode", json={"theme": "dark"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["dark_mode"] is True

    # Check database was updated
    db.session.refresh(authenticated_user)
    assert authenticated_user.dark_mode_preference is True


def test_toggle_dark_mode_fallback(test_client, authenticated_user, db):
    """Test the toggle dark mode endpoint with fallback behavior."""
    # Start with dark mode enabled
    authenticated_user.dark_mode_preference = True
    db.session.commit()

    # Test without theme parameter (should toggle)
    response = test_client.post("/settings/toggle-dark-mode", json={})

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["dark_mode"] is False  # Should toggle from True to False

    # Check database was updated
    db.session.refresh(authenticated_user)
    assert authenticated_user.dark_mode_preference is False


def test_toggle_dark_mode_unauthenticated(test_client):
    """Test toggle dark mode endpoint when user is not authenticated."""
    response = test_client.post("/settings/toggle-dark-mode", json={"theme": "dark"})
    assert response.status_code == 302  # Should redirect to login page


def test_user_dark_mode_default(test_client, db):
    """Test that new users have dark mode enabled by default."""
    # Create a new user
    user = User(email="newuser@example.com", first_name="New", surname="User")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Check that dark mode preference is True by default
    assert user.dark_mode_preference is True


def test_change_email_get(test_client, authenticated_user):
    """Test GET request to change email page."""
    response = test_client.get("/settings/change-email")
    assert response.status_code == 200


def test_change_email_success(test_client, authenticated_user):
    """Test successful email change request."""
    with patch("routes.settings.send_email_change_verification") as mock_send_email:
        with patch.object(
            authenticated_user,
            "request_email_change",
            return_value=(True, "test_token_123"),
        ):
            with patch.object(authenticated_user, "check_password", return_value=True):
                response = test_client.post(
                    "/settings/change-email",
                    data={
                        "new_email": "unique_new_email@example.com",
                        "password": "password123",
                    },
                    follow_redirects=True,
                )

                assert response.status_code == 200
                mock_send_email.assert_called_once()


def test_change_email_missing_fields(test_client, authenticated_user):
    """Test email change with missing fields."""
    response = test_client.post(
        "/settings/change-email",
        data={
            "new_email": "newemail@example.com"
            # Missing password
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should show error message


def test_change_email_wrong_password(test_client, authenticated_user):
    """Test email change with wrong password."""
    response = test_client.post(
        "/settings/change-email",
        data={"new_email": "newemail@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should show error message


def test_change_email_invalid_email(test_client, authenticated_user):
    """Test email change with invalid email."""
    with patch.object(
        authenticated_user,
        "request_email_change",
        return_value=(False, "Invalid email format"),
    ):
        response = test_client.post(
            "/settings/change-email",
            data={"new_email": "invalid-email", "password": "password123"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Should show error message


def test_change_email_duplicate_email(test_client, authenticated_user):
    """Test email change with duplicate email."""
    with patch.object(
        authenticated_user,
        "request_email_change",
        return_value=(False, "Email already registered"),
    ):
        response = test_client.post(
            "/settings/change-email",
            data={"new_email": "existing@example.com", "password": "password123"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Should show error message


def test_change_email_send_failure(test_client, authenticated_user):
    """Test email change when sending verification email fails."""
    with patch.object(authenticated_user, "request_email_change", return_value=(True, "token123")):
        with patch(
            "routes.settings.send_email_change_verification",
            side_effect=Exception("Email service down"),
        ):
            response = test_client.post(
                "/settings/change-email",
                data={"new_email": "newemail@example.com", "password": "password123"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Should show error message about email sending failure


def test_confirm_email_change_success(test_client, authenticated_user):
    """Test successful email change confirmation."""
    with patch.object(
        authenticated_user,
        "confirm_email_change",
        return_value=(True, "old@example.com"),
    ):
        response = test_client.get("/settings/change-email/valid_token", follow_redirects=True)
        assert response.status_code == 200


def test_confirm_email_change_invalid_token(test_client, authenticated_user):
    """Test email change confirmation with invalid token."""
    with patch.object(authenticated_user, "confirm_email_change", return_value=(False, None)):
        response = test_client.get("/settings/change-email/invalid_token", follow_redirects=True)
        assert response.status_code == 200
        # Should show error message


def test_settings_unauthenticated(test_client):
    """Test settings page when user is not authenticated."""
    response = test_client.get("/settings/", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login


def test_change_email_unauthenticated(test_client):
    """Test change email page when user is not authenticated."""
    response = test_client.get("/settings/change-email", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login


def test_confirm_email_change_unauthenticated(test_client):
    """Test confirm email change when user is not authenticated."""
    response = test_client.get("/settings/change-email/token", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login
