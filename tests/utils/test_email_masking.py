import pytest

from utils.mask_email import mask_email


def test_mask_email_standard():
    """Test standard email masking."""
    assert mask_email("testemailperson@address.com") == "tes****@address.com"


def test_mask_email_short_local():
    """Test email with short local part."""
    assert mask_email("ab@example.com") == "a****@example.com"
    assert mask_email("xyz@domain.org") == "x****@domain.org"


def test_mask_email_single_char_local():
    """Test email with single character local part."""
    assert mask_email("a@test.com") == "a****@test.com"


def test_mask_email_edge_cases():
    """Test edge cases."""
    # Empty email
    assert mask_email("") == ""

    # No @ symbol
    assert mask_email("invalidemail") == "invalidemail"

    # None value
    assert mask_email(None) == ""


def test_mask_email_various_formats():
    """Test various email formats."""
    assert mask_email("john.doe@company.co.uk") == "joh****@company.co.uk"
    assert mask_email("user123@domain.net") == "use****@domain.net"
    assert mask_email("test@localhost") == "tes****@localhost"
