import uuid

import pytest
from flask import url_for

from models.database.item_type import ItemType
from models.database.mods import Mod
from models.wiki import WikiPage, WikiPageVersion, WikiPageVersionStatus, WikiSection, WikiTag


def test_mods_list_unauthorized(test_client, db):
    response = test_client.get("/db/mods/")
    assert response.status_code == 200
    assert b"Mod" in response.data or b"mod" in response.data


def test_mods_list_authorized(test_client, verified_login, db):
    response = test_client.get("/db/mods/")
    assert response.status_code == 200
    assert b"Mod" in response.data or b"mod" in response.data
    assert b"Create Mod" in response.data


def test_mod_description_formatting(db):
    """Test the mod description formatting functions."""
    # Create a mod with a simple description
    mod = Mod(name="Test Mod", wiki_slug="test-mod", description="[{num} charges]")
    db.session.add(mod)
    db.session.commit()

    # Test format_applied
    assert mod.format_applied(1) == "[1 charges]"
    assert mod.format_applied(3) == "[3 charges]"

    # Test format_unapplied
    assert mod.format_unapplied() == "[1 charges]"

    # Test with mathematical operations
    mod2 = Mod(name="Time Mod", wiki_slug="time-mod", description="[{num * 30}s]")
    db.session.add(mod2)
    db.session.commit()

    assert mod2.format_applied(1) == "[30s]"
    assert mod2.format_applied(2) == "[60s]"
    assert mod2.format_applied(3) == "[90s]"
    assert mod2.format_unapplied() == "[30s]"

    # Test with no description
    mod3 = Mod(name="No Description Mod", wiki_slug="no-desc-mod")
    db.session.add(mod3)
    db.session.commit()

    assert mod3.format_applied(1) == "No Description Mod (1)"
    assert mod3.format_unapplied() == "No Description Mod"


def test_mod_creation_with_description(test_client, verified_login, db):
    """Test creating a mod with a description."""
    # Create wiki page
    tag = WikiTag(name="mod")
    db.session.add(tag)
    wiki_page = WikiPage(slug="test-mod", title="Test Mod", tags=[tag])
    db.session.add(wiki_page)
    db.session.flush()

    wiki_version = WikiPageVersion(
        page_slug="test-mod",
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
    )
    db.session.add(wiki_version)
    db.session.flush()

    wiki_section = WikiSection(
        id=str(uuid.uuid4()),
        version_id=wiki_version.id,
        order=0,
        title="Test Mod",
        content="<p>Test mod description.</p>",
    )
    db.session.add(wiki_section)
    db.session.commit()

    # Create item type
    item_type = ItemType(name="Test Type", id_prefix="TT")
    db.session.add(item_type)
    db.session.commit()

    response = test_client.post(
        "/db/mods/new",
        data={
            "name": "Test Mod",
            "wiki_slug": "test-mod",
            "description": "[{num * 30}s]",
            "item_types": [str(item_type.id)],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Mod created successfully" in response.data

    # Check that the mod was created with the description
    mod = Mod.query.filter_by(name="Test Mod").first()
    assert mod is not None
    assert mod.description == "[{num * 30}s]"
    assert mod.format_applied(1) == "[30s]"
    assert mod.format_applied(2) == "[60s]"


def test_mod_edit_with_description(test_client, verified_login, db):
    """Test editing a mod's description."""
    # Create wiki page
    tag = WikiTag(name="mod")
    db.session.add(tag)
    wiki_page = WikiPage(slug="test-mod", title="Test Mod", tags=[tag])
    db.session.add(wiki_page)
    db.session.flush()

    wiki_version = WikiPageVersion(
        page_slug="test-mod",
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
    )
    db.session.add(wiki_version)
    db.session.flush()

    wiki_section = WikiSection(
        id=str(uuid.uuid4()),
        version_id=wiki_version.id,
        order=0,
        title="Test Mod",
        content="<p>Test mod description.</p>",
    )
    db.session.add(wiki_section)
    db.session.commit()

    # Create mod
    mod = Mod(name="Test Mod", wiki_slug="test-mod", description="[{num} charges]")
    db.session.add(mod)
    db.session.commit()

    # Edit the mod
    response = test_client.post(
        f"/db/mods/{mod.id}/edit",
        data={
            "name": "Updated Test Mod",
            "wiki_slug": "test-mod",
            "description": "[{num * 30}s]",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Mod updated successfully" in response.data

    # Check that the mod was updated
    mod = Mod.query.get(mod.id)
    assert mod.name == "Updated Test Mod"
    assert mod.description == "[{num * 30}s]"
    assert mod.format_applied(1) == "[30s]"
    assert mod.format_applied(2) == "[60s]"
