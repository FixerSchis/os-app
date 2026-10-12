import io
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from models.enums import CharacterStatus, SectionRestrictionType
from models.tools.character import Character, CharacterTag
from models.wiki import (
    WikiChangeLog,
    WikiImage,
    WikiPage,
    WikiPageVersion,
    WikiPageVersionStatus,
    WikiSection,
    WikiTag,
)


@pytest.fixture
def wiki_page(db, new_user):
    """Fixture for creating a wiki page with published version and sections."""
    slug = f"test-page-{uuid.uuid4().hex}"
    page = WikiPage(slug=slug, title="Test Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
    )
    db.session.add(version)
    db.session.flush()

    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Introduction",
        content="<p>This is a test page.</p>",
    )
    db.session.add(section)
    db.session.commit()

    return page


@pytest.fixture
def wiki_page_with_restrictions(db, new_user, faction, species):
    """Fixture for creating a wiki page with restricted sections."""
    slug = f"restricted-page-{uuid.uuid4().hex}"
    page = WikiPage(slug=slug, title="Restricted Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
    )
    db.session.add(version)
    db.session.flush()

    # Public section
    public_section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Public Content",
        content="<p>This is public content.</p>",
    )

    # Role-restricted section
    role_section = WikiSection(
        id=2,
        version_id=version.id,
        order=1,
        title="Admin Only",
        content="<p>This is admin only content.</p>",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value=json.dumps(["admin"]),
    )

    # Faction-restricted section
    faction_section = WikiSection(
        id=3,
        version_id=version.id,
        order=2,
        title="Faction Content",
        content="<p>This is faction content.</p>",
        restriction_type=SectionRestrictionType.FACTION,
        restriction_value=json.dumps([faction.id]),
    )

    db.session.add_all([public_section, role_section, faction_section])
    db.session.commit()

    return page


def test_wiki_list_get(test_client, wiki_page, db):
    """Test GET request to wiki list page."""
    response = test_client.get("/wiki/")
    assert response.status_code == 200


def test_wiki_list_with_restricted_pages(test_client, wiki_page_with_restrictions, db):
    """Test wiki list with pages that have restricted sections."""
    response = test_client.get("/wiki/")
    assert response.status_code == 200


def test_wiki_list_authenticated_user(
    test_client, authenticated_user, wiki_page_with_restrictions, db
):
    """Test wiki list for authenticated user with access to restricted content."""
    response = test_client.get("/wiki/")
    assert response.status_code == 200


def test_wiki_view_get(test_client, wiki_page, db):
    """Test GET request to view a wiki page."""
    response = test_client.get(f"/wiki/{wiki_page.slug}")
    assert response.status_code == 200


def test_wiki_view_nonexistent_page(test_client, db):
    """Test viewing a non-existent wiki page."""
    response = test_client.get("/wiki/nonexistent-page")
    assert response.status_code == 404


def test_wiki_view_deleted_page(test_client, db, new_user):
    """Test viewing a deleted wiki page."""
    page = WikiPage(slug="deleted-page-1", title="Deleted Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
        deleted=True,
    )
    db.session.add(version)
    db.session.commit()

    response = test_client.get("/wiki/deleted-page-1")
    assert response.status_code == 404


def test_wiki_view_with_restrictions_public(test_client, wiki_page_with_restrictions):
    """Test viewing a wiki page with restrictions as public user."""
    response = test_client.get(f"/wiki/{wiki_page_with_restrictions.slug}")
    assert response.status_code == 200


def test_wiki_view_with_restrictions_authenticated(
    test_client, authenticated_user, wiki_page_with_restrictions
):
    """Test viewing a wiki page with restrictions as authenticated user."""
    response = test_client.get(f"/wiki/{wiki_page_with_restrictions.slug}")
    assert response.status_code == 200


def test_wiki_view_with_restrictions_admin(test_client, admin_user, wiki_page_with_restrictions):
    """Test viewing a wiki page with restrictions as admin user."""
    response = test_client.get(f"/wiki/{wiki_page_with_restrictions.slug}")
    assert response.status_code == 200


def test_wiki_view_no_access(test_client, db, new_user):
    """Test viewing a wiki page where user has no access to any sections."""
    page = WikiPage(slug="no-access-page", title="No Access Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
    )
    db.session.add(version)
    db.session.flush()

    # Only admin-restricted section
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Admin Only",
        content="<p>Admin only content.</p>",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value=json.dumps(["admin"]),
    )
    db.session.add(section)
    db.session.commit()

    response = test_client.get("/wiki/no-access-page")
    assert response.status_code == 404


def test_wiki_view_specific_version(test_client, wiki_page):
    """Test viewing a specific version of a wiki page."""
    response = test_client.get(f"/wiki/{wiki_page.slug}?v=1")
    assert response.status_code == 200


def test_wiki_view_pending_version_unauthorized(test_client, db, new_user, plot_team_user):
    """Test viewing pending version without authorization."""
    page = WikiPage(slug="pending-page-1", title="Pending Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PENDING,
        created_by=plot_team_user.id,
    )
    db.session.add(version)
    db.session.flush()

    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>",
    )
    db.session.add(section)
    db.session.commit()

    response = test_client.get("/wiki/pending-page-1?v=pending")
    assert response.status_code in (302, 404)


def test_wiki_view_pending_version_authorized(test_client, authenticated_plot_team_user, db):
    """Test viewing pending version with authorization."""
    page = WikiPage(slug="pending-page-2", title="Pending Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PENDING,
        created_by=authenticated_plot_team_user.id,
    )
    db.session.add(version)
    db.session.flush()

    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>",
    )
    db.session.add(section)
    db.session.commit()

    response = test_client.get("/wiki/pending-page-2?v=pending")
    assert response.status_code == 200


def test_get_internal_pages(test_client, db):
    """Test getting internal pages."""
    response = test_client.get("/wiki/_internal_pages")
    assert response.status_code == 200


def test_api_wiki_pages(test_client, wiki_page):
    """Test API endpoint for wiki pages."""
    response = test_client.get("/wiki/api/wiki-pages")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_api_wiki_pages_with_search(test_client, wiki_page):
    """Test API endpoint for wiki pages with search query."""
    response = test_client.get("/wiki/api/wiki-pages?q=test")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_wiki_edit_get_unauthorized(test_client, wiki_page):
    """Test GET request to edit wiki page without authorization."""
    response = test_client.get(f"/wiki/{wiki_page.slug}/edit", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_edit_get_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test GET request to edit wiki page with authorization."""
    response = test_client.get(f"/wiki/{wiki_page.slug}/edit")
    assert response.status_code == 200


def test_wiki_edit_get_nonexistent_page(test_client, authenticated_plot_team_user):
    """Test GET request to edit non-existent wiki page."""
    response = test_client.get("/wiki/nonexistent-page/edit")
    assert response.status_code == 404


def test_wiki_edit_post_unauthorized(test_client, wiki_page):
    """Test POST request to edit wiki page without authorization."""
    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        data={
            "title": "Updated Title",
            "sections": json.dumps(
                [
                    {
                        "id": 1,
                        "title": "Updated Section",
                        "content": "<p>Updated content</p>",
                        "order": 0,
                    }
                ]
            ),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_edit_post_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to edit wiki page with authorization."""
    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Updated Section",
                    "content": "<p>Updated content</p>",
                    "order": 0,
                }
            ],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_edit_assigns_integer_ids_to_new_sections(
    test_client, authenticated_plot_team_user, wiki_page, db
):
    """New sections get integer ids and a later save updates them in place."""
    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Introduction",
                    "content": "<p>Original</p>",
                    "order": 0,
                },
                {
                    "id": None,
                    "title": "Added",
                    "content": "<p>First new section</p>",
                    "order": 1,
                },
                {
                    "title": "Also added",
                    "content": "<p>Second new section</p>",
                    "order": 2,
                },
            ],
        },
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    db.session.expire_all()
    pending = (
        WikiPageVersion.query.filter_by(
            page_slug=wiki_page.slug,
            status=WikiPageVersionStatus.PENDING,
        )
        .order_by(WikiPageVersion.version_number.desc())
        .one()
    )
    sections = list(pending.sections.order_by(WikiSection.order))
    assert [section.id for section in sections] == [1, 2, 3]
    assert all(isinstance(section.id, int) for section in sections)

    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Introduction",
                    "content": "<p>Original</p>",
                    "order": 0,
                },
                {
                    "id": "2",
                    "title": "Added",
                    "content": "<p>Edited new section</p>",
                    "order": 1,
                },
                {
                    "id": 3,
                    "title": "Also added",
                    "content": "<p>Second new section</p>",
                    "order": 2,
                },
            ],
        },
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    db.session.expire_all()
    pending = (
        WikiPageVersion.query.filter_by(
            page_slug=wiki_page.slug,
            status=WikiPageVersionStatus.PENDING,
        )
        .order_by(WikiPageVersion.version_number.desc())
        .one()
    )
    sections = {section.id: section for section in pending.sections}
    assert set(sections) == {1, 2, 3}
    assert sections[1].content == "<p>Original</p>"
    assert sections[2].content == "<p>Edited new section</p>"
    assert sections[2].title == "Added"
    assert pending.sections.count() == 3


def test_wiki_new_post_assigns_integer_section_ids(test_client, authenticated_plot_team_user):
    """A new page stores integer section ids instead of generated UUID strings."""
    slug = f"new-sections-{uuid.uuid4().hex}"
    response = test_client.post(
        "/wiki/new",
        json={
            "title": "New Sections",
            "slug": slug,
            "sections": [
                {"title": "One", "content": "<p>One</p>", "order": 0},
                {"id": None, "title": "Two", "content": "<p>Two</p>", "order": 1},
            ],
        },
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    page = WikiPage.query.filter_by(slug=slug).one()
    sections = list(page.versions.one().sections.order_by(WikiSection.order))
    assert [section.id for section in sections] == [1, 2]
    assert sections[0].title == "One"
    assert sections[1].content == "<p>Two</p>"


def test_wiki_edit_post_with_restrictions(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to edit wiki page with section restrictions."""
    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Restricted Section",
                    "content": "<p>Restricted content</p>",
                    "order": 0,
                    "restriction_type": "role",
                    "restriction_value": ["admin"],
                }
            ],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_edit_post_with_tag_restrictions(
    test_client, authenticated_plot_team_user, wiki_page, db
):
    """Test POST request to edit wiki page with tag restrictions."""
    tag = CharacterTag(name="test-tag")
    db.session.add(tag)
    db.session.commit()
    import json as _json

    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Tag Restricted Section",
                    "content": "<p>Tag restricted content</p>",
                    "order": 0,
                    "restriction_type": "tag",
                    "restriction_value": _json.dumps([tag.id]),
                }
            ],
        },
        follow_redirects=True,
    )
    if response.status_code != 200:
        print("Response data:", response.data)
    assert response.status_code == 200


def test_wiki_new_get_unauthorized(test_client):
    """Test GET request to create new wiki page without authorization."""
    response = test_client.get("/wiki/new", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_new_get_authorized(test_client, authenticated_plot_team_user):
    """Test GET request to create new wiki page with authorization."""
    response = test_client.get("/wiki/new")
    assert response.status_code == 200


def test_wiki_new_post_unauthorized(test_client):
    """Test POST request to create new wiki page without authorization."""
    response = test_client.post(
        "/wiki/new",
        data={
            "title": "New Page",
            "slug": "new-page",
            "sections": json.dumps(
                [
                    {
                        "title": "Introduction",
                        "content": "<p>New page content</p>",
                        "order": 0,
                    }
                ]
            ),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_new_post_authorized(test_client, authenticated_plot_team_user):
    """Test POST request to create new wiki page with authorization."""
    response = test_client.post(
        "/wiki/new",
        json={
            "title": "New Page",
            "slug": "new-page-1",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "<p>New page content</p>",
                    "order": 0,
                }
            ],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_new_post_duplicate_slug(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to create new wiki page with duplicate slug."""
    response = test_client.post(
        "/wiki/new",
        json={
            "title": "Duplicate Page",
            "slug": wiki_page.slug,
            "sections": [
                {
                    "title": "Introduction",
                    "content": "<p>Duplicate page content</p>",
                    "order": 0,
                }
            ],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_new_post_json(test_client, authenticated_plot_team_user):
    """Test POST request to create new wiki page with JSON data."""
    response = test_client.post(
        "/wiki/new",
        json={
            "title": "New JSON Page",
            "slug": "new-json-page",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "<p>New JSON page content</p>",
                    "order": 0,
                }
            ],
        },
        content_type="application/json",
    )
    assert response.status_code == 200


def test_wiki_upload_image_unauthorized(test_client):
    """Test uploading image without authorization."""
    response = test_client.post(
        "/wiki/upload_image",
        data={"upload": (io.BytesIO(b"test image data"), "test.jpg")},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_upload_image_authorized(test_client, authenticated_plot_team_user):
    """Test uploading image with authorization."""
    response = test_client.post(
        "/wiki/upload_image",
        data={"file": (io.BytesIO(b"test image data"), "test.jpg")},
    )
    assert response.status_code == 200


def test_wiki_image(test_client, db, new_user):
    """Test viewing a wiki image."""
    # Create a wiki image
    image = WikiImage(
        filename="test.jpg",
        data=b"test image data",
        mimetype="image/jpeg",
        uploaded_by=new_user.id,
    )
    db.session.add(image)
    db.session.commit()

    response = test_client.get(f"/wiki/image/{image.id}")
    assert response.status_code == 200


def test_wiki_image_nonexistent(test_client, db):
    """Test accessing a non-existent wiki image."""
    response = test_client.get("/wiki/image/nonexistent-image.jpg")
    assert response.status_code == 404


def test_wiki_delete_unauthorized(test_client, wiki_page):
    """Test deleting wiki page without authorization."""
    response = test_client.post(f"/wiki/delete/{wiki_page.slug}", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_delete_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test deleting wiki page with authorization."""
    response = test_client.post(f"/wiki/delete/{wiki_page.slug}", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_delete_nonexistent_page(test_client, authenticated_plot_team_user):
    """Test deleting non-existent wiki page."""
    response = test_client.post("/wiki/delete/nonexistent-page")
    assert response.status_code == 404


def test_wiki_restore_unauthorized(test_client, db, new_user):
    """Test restoring a wiki page without authorization."""
    # Create a deleted page
    page = WikiPage(slug="restore-test", title="Restore Test")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
        deleted=True,
    )
    db.session.add(version)
    db.session.commit()

    response = test_client.post(f"/wiki/restore/{page.slug}", follow_redirects=True)
    assert response.status_code in (302, 403, 200)


def test_wiki_restore_authorized(test_client, authenticated_plot_team_user, wiki_page, db):
    """Test restoring wiki page with authorization."""
    # Use the wiki_page fixture
    version = WikiPageVersion(
        page_slug=wiki_page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=authenticated_plot_team_user.id,
        deleted=True,
    )
    db.session.add(version)
    db.session.flush()
    # Add a section to the version
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Test Content",
        content="<p>This is test content.</p>",
    )
    db.session.add(section)
    db.session.commit()
    response = test_client.post(f"/wiki/restore/{wiki_page.slug}", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_pending_changes_unauthorized(test_client):
    """Test viewing pending changes without authorization."""
    response = test_client.get("/wiki/changes/pending", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_pending_changes_authorized(test_client, authenticated_plot_team_user):
    """Test viewing pending changes with authorization."""
    response = test_client.get("/wiki/changes/pending")
    assert response.status_code == 200


def test_wiki_pending_changes_post_unauthorized(test_client):
    """Test posting pending changes without authorization."""
    response = test_client.post("/wiki/changes/pending", follow_redirects=True)
    assert response.status_code == 200


def test_wiki_pending_changes_post_authorized(test_client, authenticated_plot_team_user, db):
    """Test posting pending changes with authorization."""
    # Create a page with pending version
    page = WikiPage(slug="pending-page-3", title="Pending Page")
    db.session.add(page)
    db.session.flush()

    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PENDING,
        created_by=authenticated_plot_team_user.id,
    )
    db.session.add(version)
    db.session.flush()

    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>",
    )
    db.session.add(section)
    db.session.commit()

    response = test_client.post(
        "/wiki/changes/pending",
        data={"action": "publish", "page_slugs": ["pending-page-3"]},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_change_log(test_client, db):
    """Test wiki change log page."""
    response = test_client.get("/wiki/changes/log")
    assert response.status_code == 200


def test_wiki_search(test_client, wiki_page):
    """Test wiki search functionality."""
    response = test_client.get("/wiki/search?q=test")
    assert response.status_code == 200


def test_wiki_search_no_query(test_client):
    """Test wiki search without query parameter."""
    response = test_client.get("/wiki/search")
    assert response.status_code == 200


def test_wiki_search_empty_query(test_client):
    """Test wiki search with empty query."""
    response = test_client.get("/wiki/search?q=")
    assert response.status_code == 200


def test_wiki_tags_get(test_client, db):
    """Test GET request to wiki tags page."""
    response = test_client.get("/wiki/tags")
    assert response.status_code == 200


def test_wiki_tags_post_unauthorized(test_client):
    """Test POST request to wiki tags without authorization."""
    response = test_client.post(
        "/wiki/tags",
        data={"action": "create", "name": "new-tag"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_wiki_tags_post_authorized(test_client, authenticated_plot_team_user):
    response = test_client.post("/wiki/tags", json={"name": "new-tag"})
    assert response.status_code == 200


def test_wiki_tags_post_delete(test_client, authenticated_plot_team_user, db):
    tag = WikiTag(name="test-tag")
    db.session.add(tag)
    db.session.commit()
    # There is no delete in the route, so this test may not be valid, but keep for now
    response = test_client.post("/wiki/tags", json={"action": "delete", "tag_id": tag.id})
    assert response.status_code in (200, 400, 404)


def test_wiki_live_search(test_client, wiki_page):
    """Test wiki live search functionality."""
    response = test_client.get("/wiki/live_search?q=test")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_wiki_live_search_no_query(test_client):
    """Test wiki live search without query."""
    response = test_client.get("/wiki/live_search")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_has_access_public_section(test_client):
    """Test has_access function with public section."""
    from models.wiki import WikiSection
    from routes.wiki import has_access

    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Public Section",
        content="<p>Public content</p>",
    )

    # Should be accessible to everyone
    assert has_access(section, None) is True
    assert has_access(section, MagicMock(is_authenticated=False)) is True


def test_has_access_role_restricted_section(test_client, authenticated_user):
    """Test has_access function with role-restricted section."""
    from models.wiki import WikiSection
    from routes.wiki import has_access

    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Role Restricted Section",
        content="<p>Role restricted content</p>",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value=json.dumps(["admin"]),
    )

    # Should not be accessible to regular user
    assert has_access(section, authenticated_user) is False

    # Should be accessible to admin user with appropriate permissions
    admin_user = MagicMock()
    admin_user.is_authenticated = True
    admin_user.has_permission.return_value = True
    assert has_access(section, admin_user) is True


def test_has_access_faction_restricted_section(test_client, authenticated_user, faction):
    """Test has_access function with faction-restricted section."""
    from models.wiki import WikiSection
    from routes.wiki import has_access

    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Faction Restricted Section",
        content="<p>Faction restricted content</p>",
        restriction_type=SectionRestrictionType.FACTION,
        restriction_value=json.dumps([faction.id]),
    )

    # Should not be accessible to user without faction
    assert has_access(section, authenticated_user) is False

    # Should be accessible to user with matching faction
    faction_user = MagicMock()
    faction_user.is_authenticated = True
    faction_user.faction_id = faction.id
    assert has_access(section, faction_user) is True


def test_build_wiki_tree(test_client):
    """Test build_wiki_tree function."""
    from routes.wiki import build_wiki_tree

    pages = [
        {"slug": "page1", "title": "Page 1"},
        {"slug": "folder1/page2", "title": "Page 2"},
        {"slug": "folder1/subfolder/page3", "title": "Page 3"},
        {"slug": "folder2/page4", "title": "Page 4"},
    ]

    tree = build_wiki_tree(pages)

    # Check that pages are organized correctly
    assert "_pages" in tree
    assert "folder1" in tree
    assert "folder2" in tree
    assert "subfolder" in tree["folder1"]
    assert "_pages" in tree["folder1"]["subfolder"]
    assert len(tree["folder1"]["subfolder"]["_pages"]) == 1

    # Check that page1 is in the root _pages
    assert len(tree["_pages"]) == 1
    assert tree["_pages"][0]["slug"] == "page1"


class _GateCharacter:
    def __init__(self, name, **kwargs):
        self.name = name
        self.faction_id = kwargs.get("faction_id")
        self.species_id = kwargs.get("species_id")
        self.skills = kwargs.get("skills", [])
        self.cybernetics = kwargs.get("cybernetics", [])
        self.tags = kwargs.get("tags", [])
        self.reputation = kwargs.get("reputation", {})

    def get_reputation(self, faction_id):
        return self.reputation.get(faction_id, 0)


class _SkillLink:
    def __init__(self, skill_id):
        self.skill_id = skill_id


class _Record:
    def __init__(self, record_id):
        self.id = record_id


class _GateUser:
    def __init__(self, characters, editor=False):
        self.id = id(self)
        self.is_authenticated = True
        self._characters = characters
        self._editor = editor

    def has_permission(self, name):
        return self._editor and name == "wiki.edit"

    def get_active_characters(self):
        return list(self._characters)


@pytest.mark.parametrize(
    ("restriction_type", "restriction_value", "matching_kwargs", "other_kwargs"),
    [
        (SectionRestrictionType.FACTION, [3], {"faction_id": 3}, {"faction_id": 9}),
        (SectionRestrictionType.SPECIES, [4], {"species_id": 4}, {"species_id": 8}),
        (
            SectionRestrictionType.SKILL,
            [5],
            {"skills": [_SkillLink(5)]},
            {"skills": [_SkillLink(6)]},
        ),
        (
            SectionRestrictionType.CYBERNETIC,
            [7],
            {"cybernetics": [_Record(7)]},
            {"cybernetics": []},
        ),
        (SectionRestrictionType.TAG, [2], {"tags": [_Record(2)]}, {"tags": [_Record(1)]}),
        (
            SectionRestrictionType.REPUTATION,
            [3, 10],
            {"reputation": {3: 10}},
            {"reputation": {3: 9}},
        ),
    ],
)
def test_has_access_allows_any_matching_active_character(
    test_client, restriction_type, restriction_value, matching_kwargs, other_kwargs
):
    """Character gates pass when any active character meets them."""
    from routes.wiki import has_access, visible_character_names

    matching = _GateCharacter("Matching Character", **matching_kwargs)
    other = _GateCharacter("Other Character", **other_kwargs)
    section = WikiSection(
        restriction_type=restriction_type,
        restriction_value=json.dumps(restriction_value),
        content="<p>Restricted</p>",
    )

    user = _GateUser([other, matching])
    assert has_access(section, user) is True
    assert visible_character_names(section, user) == ["Matching Character"]

    everyone = _GateUser(
        [matching, _GateCharacter("Also Matching", **matching_kwargs)],
    )
    assert has_access(section, everyone) is True
    assert visible_character_names(section, everyone) is None

    only_one = _GateUser([matching])
    assert has_access(section, only_one) is True
    assert visible_character_names(section, only_one) is None

    nobody = _GateUser([other, _GateCharacter("Also Out", **other_kwargs)])
    assert has_access(section, nobody) is False
    assert visible_character_names(section, nobody) is None

    editor = _GateUser([other, matching], editor=True)
    assert has_access(section, editor) is True
    assert visible_character_names(section, editor) == ["Matching Character"]

    editor_without_match = _GateUser(
        [other, _GateCharacter("Also Out", **other_kwargs)],
        editor=True,
    )
    assert has_access(section, editor_without_match) is True
    assert visible_character_names(section, editor_without_match) is None


def _publish_wiki_page(db, owner, slug, sections):
    page = WikiPage(slug=slug, title=slug)
    db.session.add(page)
    db.session.flush()
    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=owner.id,
    )
    db.session.add(version)
    db.session.flush()
    for index, section in enumerate(sections, start=1):
        section.version_id = version.id
        section.id = index
        section.order = index
        db.session.add(section)
    db.session.commit()
    return page


def test_wiki_names_characters_with_partial_section_access(
    test_client, db, authenticated_user, species, faction
):
    """A section names the active characters who can see it when others cannot."""
    outsider = Character(
        user_id=authenticated_user.id,
        name="Outsider Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
    )
    member = Character(
        user_id=authenticated_user.id,
        name="Faction Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    db.session.add_all([outsider, member])
    page = _publish_wiki_page(
        db,
        authenticated_user,
        f"partial-access-{uuid.uuid4().hex}",
        [
            WikiSection(title="Public Content", content="<p>Public body</p>"),
            WikiSection(
                title="Faction Content",
                content="<p>Secret body</p>",
                restriction_type=SectionRestrictionType.FACTION,
                restriction_value=json.dumps([faction.id]),
            ),
        ],
    )

    response = test_client.get(f"/wiki/{page.slug}")
    assert response.status_code == 200
    assert b"Faction Content" in response.data
    assert b"Characters with access: Faction Character" in response.data
    assert b"Characters with access: Outsider Character" not in response.data
    assert b"Outsider Character, Faction Character" not in response.data
    assert b"Faction Character, Outsider Character" not in response.data


def test_wiki_omits_character_list_when_every_active_character_has_access(
    test_client, db, authenticated_user, species, faction
):
    """No access note when every active character can see the section."""
    first = Character(
        user_id=authenticated_user.id,
        name="First Member",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    second = Character(
        user_id=authenticated_user.id,
        name="Second Member",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    db.session.add_all([first, second])
    page = _publish_wiki_page(
        db,
        authenticated_user,
        f"full-access-{uuid.uuid4().hex}",
        [
            WikiSection(
                title="Faction Content",
                content="<p>Shared body</p>",
                restriction_type=SectionRestrictionType.FACTION,
                restriction_value=json.dumps([faction.id]),
            ),
        ],
    )

    response = test_client.get(f"/wiki/{page.slug}")
    assert response.status_code == 200
    assert b"Faction Content" in response.data
    assert b"Characters with access:" not in response.data


def test_wiki_omits_character_list_for_a_single_active_character(
    test_client, db, authenticated_user, species, faction
):
    """A player with one active character sees a gated section without an access note."""
    character = Character(
        user_id=authenticated_user.id,
        name="Only Character",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    db.session.add(character)
    page = _publish_wiki_page(
        db,
        authenticated_user,
        f"single-access-{uuid.uuid4().hex}",
        [
            WikiSection(
                title="Faction Content",
                content="<p>Solo body</p>",
                restriction_type=SectionRestrictionType.FACTION,
                restriction_value=json.dumps([faction.id]),
            ),
        ],
    )

    response = test_client.get(f"/wiki/{page.slug}")
    assert response.status_code == 200
    assert b"Faction Content" in response.data
    assert b"Characters with access:" not in response.data


def test_wiki_ignores_inactive_characters_for_section_access(
    test_client, db, authenticated_user, species, faction
):
    """A developing character does not open a section for the user's active character."""
    active = Character(
        user_id=authenticated_user.id,
        name="Active Outsider",
        status=CharacterStatus.ACTIVE.value,
        species_id=species.id,
    )
    developing = Character(
        user_id=authenticated_user.id,
        name="Developing Member",
        status=CharacterStatus.DEVELOPING.value,
        species_id=species.id,
        faction_id=faction.id,
    )
    db.session.add_all([active, developing])
    page = _publish_wiki_page(
        db,
        authenticated_user,
        f"inactive-access-{uuid.uuid4().hex}",
        [
            WikiSection(title="Public Content", content="<p>Public body</p>"),
            WikiSection(
                title="Faction Content",
                content="<p>Secret body</p>",
                restriction_type=SectionRestrictionType.FACTION,
                restriction_value=json.dumps([faction.id]),
            ),
        ],
    )

    response = test_client.get(f"/wiki/{page.slug}")
    assert response.status_code == 200
    assert b"Public Content" in response.data
    assert b"Faction Content" not in response.data
    assert b"Developing Member" not in response.data


_STORED_XSS = (
    "<p>Visible wiki text <strong>bold</strong></p>"
    "<script>wiki-xss-marker</script>"
    '<img src="x" onerror="wiki-xss-marker">'
    '<a href="javascript:wiki-xss-marker">bad</a>'
    '<p onclick="wiki-xss-marker">Hi</p>'
)


def test_wiki_edit_strips_script_before_save(test_client, authenticated_plot_team_user, wiki_page):
    """Editor HTML is sanitized before it is stored on the section."""
    response = test_client.post(
        f"/wiki/{wiki_page.slug}/edit",
        json={
            "title": "Updated Title",
            "sections": [
                {
                    "id": 1,
                    "title": "Updated Section",
                    "content": (
                        "<p>Visible <strong>bold</strong></p>"
                        "<ul><li>item</li></ul>"
                        '<a href="https://example.com" target="_blank">site</a>'
                        "<script>wiki-xss-marker</script>"
                        '<img src="x" onerror="wiki-xss-marker">'
                        '<a href="javascript:wiki-xss-marker">bad</a>'
                    ),
                    "order": 0,
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    pending = (
        WikiPageVersion.query.filter_by(
            page_slug=wiki_page.slug,
            status=WikiPageVersionStatus.PENDING,
        )
        .order_by(WikiPageVersion.version_number.desc())
        .first()
    )
    stored = pending.sections.filter_by(id=1).one().content
    assert "<strong>bold</strong>" in stored
    assert "<ul><li>item</li></ul>" in stored
    assert 'href="https://example.com"' in stored
    assert 'target="_blank"' in stored
    assert "wiki-xss-marker" not in stored
    assert "<script" not in stored
    assert "javascript:" not in stored
    assert "onerror" not in stored


def test_wiki_edit_page_omits_stored_script(
    test_client, authenticated_plot_team_user, wiki_page, db
):
    """Stored markup cannot break out of the editor textarea."""
    section = wiki_page.versions.first().sections.first()
    section.content = (
        '</textarea><img src=x onerror="wiki-xss-marker"><script>wiki-xss-marker</script>'
    )
    db.session.commit()

    response = test_client.get(f"/wiki/{wiki_page.slug}/edit")

    assert response.status_code == 200
    assert b"wiki-xss-marker" not in response.data


def test_wiki_view_strips_stored_script(test_client, wiki_page, db):
    """Pages saved before sanitizing still do not run script for visitors."""
    section = wiki_page.versions.first().sections.first()
    section.content = _STORED_XSS
    db.session.commit()

    response = test_client.get(f"/wiki/{wiki_page.slug}")

    assert response.status_code == 200
    assert b"Visible wiki text" in response.data
    assert b"<strong>bold</strong>" in response.data
    assert b"wiki-xss-marker" not in response.data
    assert b"javascript:" not in response.data
    assert b"onclick" not in response.data


def test_wiki_search_escapes_titles_and_excerpts(test_client, wiki_page, db):
    """Search highlights are escaped before <mark> is inserted."""
    wiki_page.title = "Findme <script>wiki-xss-marker</script>"
    section = wiki_page.versions.first().sections.first()
    section.title = 'Findme <img src=x onerror="wiki-xss-marker">'
    section.content = "<p>Findme</p><script>wiki-xss-marker</script>"
    db.session.commit()

    response = test_client.get("/wiki/search?q=Findme")

    assert response.status_code == 200
    assert b"<mark>Findme</mark>" in response.data
    assert b"<script>wiki-xss-marker</script>" not in response.data
    assert b"&lt;script&gt;wiki-xss-marker&lt;/script&gt;" in response.data
    assert b'onerror="wiki-xss-marker"' not in response.data
    assert b"onerror=&quot;wiki-xss-marker&quot;" in response.data


def test_wiki_change_log_strips_stored_script(test_client, db, new_user):
    """Change log messages are sanitized when rendered."""
    db.session.add(
        WikiChangeLog(
            user_id=new_user.id,
            message="<p>Shipped <strong>now</strong></p><script>wiki-xss-marker</script>",
        )
    )
    db.session.commit()

    response = test_client.get("/wiki/changes/log")

    assert response.status_code == 200
    assert b"Shipped" in response.data
    assert b"<strong>now</strong>" in response.data
    assert b"wiki-xss-marker" not in response.data


def test_wiki_publish_strips_changelog_script(test_client, authenticated_plot_team_user, db):
    """Publish stores a sanitized change log message."""
    slug = f"publish-xss-{uuid.uuid4().hex}"
    page = WikiPage(slug=slug, title="Publish XSS")
    db.session.add(page)
    db.session.flush()
    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PENDING,
        created_by=authenticated_plot_team_user.id,
    )
    db.session.add(version)
    db.session.flush()
    db.session.add(
        WikiSection(
            id=1,
            version_id=version.id,
            order=0,
            title="Pending",
            content="<p>Pending body</p>",
        )
    )
    db.session.commit()

    response = test_client.post(
        "/wiki/changes/pending",
        data={
            "selected_pages": slug,
            "changelog": "<p>Shipped</p><script>wiki-xss-marker</script>",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    log = WikiChangeLog.query.one()
    assert "<p>Shipped</p>" in log.message
    assert "wiki-xss-marker" not in log.message
    assert "<script" not in log.message


def test_wiki_publish_rejects_script_only_changelog(test_client, authenticated_plot_team_user):
    """A change log that is only a script is rejected."""
    response = test_client.post(
        "/wiki/changes/pending",
        data={
            "selected_pages": "missing",
            "changelog": "<script>wiki-xss-marker</script>",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert WikiChangeLog.query.count() == 0
    assert b"Change log message is required." in response.data
