from unittest.mock import MagicMock, patch

from utils.decorators import email_verified_required, has_active_character_required


# Tests for deprecated roles_required decorator removed
def test_has_active_character_required_with_active_character():
    """Test has_active_character_required decorator with active character."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_active_character.return_value = True

    @has_active_character_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.flash") as mock_flash:
            with patch("utils.decorators.redirect") as mock_redirect:
                with patch("utils.decorators.url_for") as mock_url_for:
                    mock_url_for.return_value = "/characters"
                    result = test_function()
                    assert result == "success"
                    mock_flash.assert_not_called()
                    mock_redirect.assert_not_called()


def test_has_active_character_required_without_active_character():
    """Test has_active_character_required decorator without active character."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_active_character.return_value = False

    @has_active_character_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.flash") as mock_flash:
            with patch("utils.decorators.redirect") as mock_redirect:
                with patch("utils.decorators.url_for") as mock_url_for:
                    mock_url_for.return_value = "/characters"
                    test_function()
                    mock_flash.assert_called_once()
                    mock_redirect.assert_called_once_with("/characters")


def test_email_verified_required_with_verified_email():
    """Test email_verified_required decorator with verified email."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.email_verified = True

    @email_verified_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.flash") as mock_flash:
            with patch("utils.decorators.redirect") as mock_redirect:
                with patch("utils.decorators.url_for") as mock_url_for:
                    mock_url_for.return_value = "/verify"
                    result = test_function()
                    assert result == "success"
                    mock_flash.assert_not_called()
                    mock_redirect.assert_not_called()


def test_email_verified_required_without_verified_email():
    """Test email_verified_required decorator without verified email."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.email_verified = False

    @email_verified_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.flash") as mock_flash:
            with patch("utils.decorators.redirect") as mock_redirect:
                with patch("utils.decorators.url_for") as mock_url_for:
                    mock_url_for.return_value = "/verify"
                    test_function()
                    mock_flash.assert_called_once()
                    mock_redirect.assert_called_once_with("/verify")
