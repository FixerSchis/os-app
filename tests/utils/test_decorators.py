from unittest.mock import MagicMock, patch

from models.enums import Role
from utils.decorators import admin_required, owner_required, roles_required


def test_roles_required_with_valid_role():
    """Test roles_required decorator with a user who has the required role."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = True

    @roles_required(roles=[Role.ADMIN.value])
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"
        mock_user.has_role.assert_called_with(Role.ADMIN.value)


def test_roles_required_without_valid_role():
    """Test roles_required decorator with a user who doesn't have the required role."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = False

    @roles_required(roles=[Role.ADMIN.value])
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.flash") as mock_flash:
            with patch("utils.decorators.abort") as mock_abort:
                test_function()
                mock_flash.assert_called_once()
                # Check that abort was called with 403, but don't care about call count
                assert mock_abort.call_args_list[0][0][0] == 403


def test_roles_required_unauthenticated():
    """Test roles_required decorator with an unauthenticated user."""
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    @roles_required(roles=[Role.ADMIN.value])
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        with patch("utils.decorators.redirect") as mock_redirect:
            with patch("utils.decorators.url_for") as mock_url_for:
                mock_url_for.return_value = "/login"
                test_function()
                mock_redirect.assert_called_once_with("/login")


def test_roles_required_with_custom_condition():
    """Test roles_required decorator with a custom condition function."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = False
    mock_user.player_id = 1

    def custom_condition(user):
        return user.player_id == 1

    @roles_required(condition_func=custom_condition)
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"


def test_roles_required_with_both_roles_and_condition():
    """Test roles_required decorator with both roles and custom condition."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = False
    mock_user.player_id = 1

    def custom_condition(user):
        return user.player_id == 1

    @roles_required(roles=[Role.ADMIN.value], condition_func=custom_condition)
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"


def test_admin_required_decorator():
    """Test admin_required decorator."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = True

    @admin_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"
        mock_user.has_role.assert_called_with(Role.ADMIN.value)


def test_owner_required_decorator():
    """Test owner_required decorator."""
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = True

    @owner_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"
        mock_user.has_role.assert_called_with(Role.OWNER.value)


def test_user_admin_required_decorator():
    """Test user_admin_required decorator."""
    from utils.decorators import user_admin_required

    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.has_role.return_value = True

    @user_admin_required
    def test_function():
        return "success"

    with patch("utils.decorators.current_user", mock_user):
        result = test_function()
        assert result == "success"
        mock_user.has_role.assert_called_with(Role.USER_ADMIN.value)


def test_has_active_character_required_with_active_character():
    """Test has_active_character_required decorator with active character."""
    from utils.decorators import has_active_character_required

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
    from utils.decorators import has_active_character_required

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
    from utils.decorators import email_verified_required

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
    from utils.decorators import email_verified_required

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
