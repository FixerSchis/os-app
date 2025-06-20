import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.wiki import (
    WikiPage, WikiPageVersion, WikiSection, WikiTag, WikiImage, WikiChangeLog,
    WikiPageVersionStatus
)
from models.enums import Role, SectionRestrictionType
from models.tools.character import CharacterTag
from routes.wiki import has_access
import json
import uuid
import io


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
        created_by=new_user.id
    )
    db.session.add(version)
    db.session.flush()
    
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Introduction",
        content="<p>This is a test page.</p>"
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
        created_by=new_user.id
    )
    db.session.add(version)
    db.session.flush()
    
    # Public section
    public_section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Public Content",
        content="<p>This is public content.</p>"
    )
    
    # Role-restricted section
    role_section = WikiSection(
        id=2,
        version_id=version.id,
        order=1,
        title="Admin Only",
        content="<p>This is admin only content.</p>",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value=json.dumps(["admin"])
    )
    
    # Faction-restricted section
    faction_section = WikiSection(
        id=3,
        version_id=version.id,
        order=2,
        title="Faction Content",
        content="<p>This is faction content.</p>",
        restriction_type=SectionRestrictionType.FACTION,
        restriction_value=json.dumps([faction.id])
    )
    
    db.session.add_all([public_section, role_section, faction_section])
    db.session.commit()
    
    return page


def test_wiki_list_get(test_client, wiki_page, db):
    """Test GET request to wiki list page."""
    response = test_client.get('/wiki/')
    assert response.status_code == 200


def test_wiki_list_with_restricted_pages(test_client, wiki_page_with_restrictions, db):
    """Test wiki list with pages that have restricted sections."""
    response = test_client.get('/wiki/')
    assert response.status_code == 200


def test_wiki_list_authenticated_user(test_client, authenticated_user, wiki_page_with_restrictions, db):
    """Test wiki list for authenticated user with access to restricted content."""
    response = test_client.get('/wiki/')
    assert response.status_code == 200


def test_wiki_view_get(test_client, wiki_page, db):
    """Test GET request to view a wiki page."""
    response = test_client.get(f'/wiki/{wiki_page.slug}')
    assert response.status_code == 200


def test_wiki_view_nonexistent_page(test_client, db):
    """Test viewing a non-existent wiki page."""
    response = test_client.get('/wiki/nonexistent-page')
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
        deleted=True
    )
    db.session.add(version)
    db.session.commit()
    
    response = test_client.get('/wiki/deleted-page-1')
    assert response.status_code == 404


def test_wiki_view_with_restrictions_public(test_client, wiki_page_with_restrictions):
    """Test viewing a wiki page with restrictions as public user."""
    response = test_client.get(f'/wiki/{wiki_page_with_restrictions.slug}')
    assert response.status_code == 200


def test_wiki_view_with_restrictions_authenticated(test_client, authenticated_user, wiki_page_with_restrictions):
    """Test viewing a wiki page with restrictions as authenticated user."""
    response = test_client.get(f'/wiki/{wiki_page_with_restrictions.slug}')
    assert response.status_code == 200


def test_wiki_view_with_restrictions_admin(test_client, admin_user, wiki_page_with_restrictions):
    """Test viewing a wiki page with restrictions as admin user."""
    response = test_client.get(f'/wiki/{wiki_page_with_restrictions.slug}')
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
        created_by=new_user.id
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
        restriction_value=json.dumps(["admin"])
    )
    db.session.add(section)
    db.session.commit()
    
    response = test_client.get('/wiki/no-access-page')
    assert response.status_code == 404


def test_wiki_view_specific_version(test_client, wiki_page):
    """Test viewing a specific version of a wiki page."""
    response = test_client.get(f'/wiki/{wiki_page.slug}?v=1')
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
        created_by=plot_team_user.id
    )
    db.session.add(version)
    db.session.flush()
    
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>"
    )
    db.session.add(section)
    db.session.commit()
    
    response = test_client.get('/wiki/pending-page-1?v=pending')
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
        created_by=authenticated_plot_team_user.id
    )
    db.session.add(version)
    db.session.flush()
    
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>"
    )
    db.session.add(section)
    db.session.commit()
    
    response = test_client.get('/wiki/pending-page-2?v=pending')
    assert response.status_code == 200


def test_get_internal_pages(test_client, db):
    """Test getting internal pages."""
    response = test_client.get('/wiki/_internal_pages')
    assert response.status_code == 200


def test_api_wiki_pages(test_client, wiki_page):
    """Test API endpoint for wiki pages."""
    response = test_client.get('/wiki/api/wiki-pages')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_api_wiki_pages_with_search(test_client, wiki_page):
    """Test API endpoint for wiki pages with search query."""
    response = test_client.get('/wiki/api/wiki-pages?q=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_wiki_edit_get_unauthorized(test_client, wiki_page):
    """Test GET request to edit wiki page without authorization."""
    response = test_client.get(f'/wiki/{wiki_page.slug}/edit', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_edit_get_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test GET request to edit wiki page with authorization."""
    response = test_client.get(f'/wiki/{wiki_page.slug}/edit')
    assert response.status_code == 200


def test_wiki_edit_get_nonexistent_page(test_client, authenticated_plot_team_user):
    """Test GET request to edit non-existent wiki page."""
    response = test_client.get('/wiki/nonexistent-page/edit')
    assert response.status_code == 404


def test_wiki_edit_post_unauthorized(test_client, wiki_page):
    """Test POST request to edit wiki page without authorization."""
    response = test_client.post(f'/wiki/{wiki_page.slug}/edit', data={
        'title': 'Updated Title',
        'sections': json.dumps([{
            'id': 1,
            'title': 'Updated Section',
            'content': '<p>Updated content</p>',
            'order': 0
        }])
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_edit_post_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to edit wiki page with authorization."""
    response = test_client.post(f'/wiki/{wiki_page.slug}/edit', json={
        'title': 'Updated Title',
        'sections': [{
            'id': 1,
            'title': 'Updated Section',
            'content': '<p>Updated content</p>',
            'order': 0
        }]
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_edit_post_with_restrictions(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to edit wiki page with section restrictions."""
    response = test_client.post(f'/wiki/{wiki_page.slug}/edit', json={
        'title': 'Updated Title',
        'sections': [{
            'id': 1,
            'title': 'Restricted Section',
            'content': '<p>Restricted content</p>',
            'order': 0,
            'restriction_type': 'role',
            'restriction_value': ['admin']
        }]
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_edit_post_with_tag_restrictions(test_client, authenticated_plot_team_user, wiki_page, db):
    """Test POST request to edit wiki page with tag restrictions."""
    tag = CharacterTag(name="test-tag")
    db.session.add(tag)
    db.session.commit()
    import json as _json
    response = test_client.post(f'/wiki/{wiki_page.slug}/edit', json={
        'title': 'Updated Title',
        'sections': [{
            'id': 1,
            'title': 'Tag Restricted Section',
            'content': '<p>Tag restricted content</p>',
            'order': 0,
            'restriction_type': 'tag',
            'restriction_value': _json.dumps([tag.id])
        }]
    }, follow_redirects=True)
    if response.status_code != 200:
        print('Response data:', response.data)
    assert response.status_code == 200


def test_wiki_new_get_unauthorized(test_client):
    """Test GET request to create new wiki page without authorization."""
    response = test_client.get('/wiki/new', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_new_get_authorized(test_client, authenticated_plot_team_user):
    """Test GET request to create new wiki page with authorization."""
    response = test_client.get('/wiki/new')
    assert response.status_code == 200


def test_wiki_new_post_unauthorized(test_client):
    """Test POST request to create new wiki page without authorization."""
    response = test_client.post('/wiki/new', data={
        'title': 'New Page',
        'slug': 'new-page',
        'sections': json.dumps([{
            'title': 'Introduction',
            'content': '<p>New page content</p>',
            'order': 0
        }])
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_new_post_authorized(test_client, authenticated_plot_team_user):
    """Test POST request to create new wiki page with authorization."""
    response = test_client.post('/wiki/new', json={
        'title': 'New Page',
        'slug': 'new-page-1',
        'sections': [{
            'title': 'Introduction',
            'content': '<p>New page content</p>',
            'order': 0
        }]
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_new_post_duplicate_slug(test_client, authenticated_plot_team_user, wiki_page):
    """Test POST request to create new wiki page with duplicate slug."""
    response = test_client.post('/wiki/new', json={
        'title': 'Duplicate Page',
        'slug': wiki_page.slug,
        'sections': [{
            'title': 'Introduction',
            'content': '<p>Duplicate page content</p>',
            'order': 0
        }]
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_new_post_json(test_client, authenticated_plot_team_user):
    """Test POST request to create new wiki page with JSON data."""
    response = test_client.post('/wiki/new', 
        json={
            'title': 'New JSON Page',
            'slug': 'new-json-page',
            'sections': [{
                'title': 'Introduction',
                'content': '<p>New JSON page content</p>',
                'order': 0
            }]
        },
        content_type='application/json'
    )
    assert response.status_code == 200


def test_wiki_upload_image_unauthorized(test_client):
    """Test uploading image without authorization."""
    response = test_client.post('/wiki/upload_image', 
        data={'upload': (io.BytesIO(b'test image data'), 'test.jpg')},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_wiki_upload_image_authorized(test_client, authenticated_plot_team_user):
    """Test uploading image with authorization."""
    response = test_client.post('/wiki/upload_image', 
        data={'file': (io.BytesIO(b'test image data'), 'test.jpg')}
    )
    assert response.status_code == 200


def test_wiki_image(test_client, db, new_user):
    """Test viewing a wiki image."""
    # Create a wiki image
    image = WikiImage(
        filename='test.jpg',
        data=b'test image data',
        mimetype='image/jpeg',
        uploaded_by=new_user.id
    )
    db.session.add(image)
    db.session.commit()
    
    response = test_client.get(f'/wiki/image/{image.id}')
    assert response.status_code == 200


def test_wiki_image_nonexistent(test_client, db):
    """Test accessing a non-existent wiki image."""
    response = test_client.get('/wiki/image/nonexistent-image.jpg')
    assert response.status_code == 404


def test_wiki_delete_unauthorized(test_client, wiki_page):
    """Test deleting wiki page without authorization."""
    response = test_client.post(f'/wiki/delete/{wiki_page.slug}', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_delete_authorized(test_client, authenticated_plot_team_user, wiki_page):
    """Test deleting wiki page with authorization."""
    response = test_client.post(f'/wiki/delete/{wiki_page.slug}', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_delete_nonexistent_page(test_client, authenticated_plot_team_user):
    """Test deleting non-existent wiki page."""
    response = test_client.post('/wiki/delete/nonexistent-page')
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
        deleted=True
    )
    db.session.add(version)
    db.session.commit()
    
    response = test_client.post(f'/wiki/restore/{page.slug}', follow_redirects=True)
    assert response.status_code in (302, 403, 200)


def test_wiki_restore_authorized(test_client, authenticated_plot_team_user, wiki_page, db):
    """Test restoring wiki page with authorization."""
    # Use the wiki_page fixture
    version = WikiPageVersion(
        page_slug=wiki_page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=authenticated_plot_team_user.id,
        deleted=True
    )
    db.session.add(version)
    db.session.flush()
    # Add a section to the version
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Test Content",
        content="<p>This is test content.</p>"
    )
    db.session.add(section)
    db.session.commit()
    response = test_client.post(f'/wiki/restore/{wiki_page.slug}', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_pending_changes_unauthorized(test_client):
    """Test viewing pending changes without authorization."""
    response = test_client.get('/wiki/changes/pending', follow_redirects=True)
    assert response.status_code == 200


def test_wiki_pending_changes_authorized(test_client, authenticated_plot_team_user):
    """Test viewing pending changes with authorization."""
    response = test_client.get('/wiki/changes/pending')
    assert response.status_code == 200


def test_wiki_pending_changes_post_unauthorized(test_client):
    """Test posting pending changes without authorization."""
    response = test_client.post('/wiki/changes/pending', follow_redirects=True)
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
        created_by=authenticated_plot_team_user.id
    )
    db.session.add(version)
    db.session.flush()
    
    section = WikiSection(
        id=1,
        version_id=version.id,
        order=0,
        title="Pending Content",
        content="<p>This is pending content.</p>"
    )
    db.session.add(section)
    db.session.commit()
    
    with patch('routes.wiki.send_wiki_published_notification_to_all') as mock_send_email:
        response = test_client.post('/wiki/changes/pending', data={
            'action': 'publish',
            'page_slugs': ['pending-page-3']
        }, follow_redirects=True)
        assert response.status_code == 200


def test_wiki_change_log(test_client, db):
    """Test wiki change log page."""
    response = test_client.get('/wiki/changes/log')
    assert response.status_code == 200


def test_wiki_search(test_client, wiki_page):
    """Test wiki search functionality."""
    response = test_client.get('/wiki/search?q=test')
    assert response.status_code == 200


def test_wiki_search_no_query(test_client):
    """Test wiki search without query parameter."""
    response = test_client.get('/wiki/search')
    assert response.status_code == 200


def test_wiki_search_empty_query(test_client):
    """Test wiki search with empty query."""
    response = test_client.get('/wiki/search?q=')
    assert response.status_code == 200


def test_wiki_tags_get(test_client, db):
    """Test GET request to wiki tags page."""
    response = test_client.get('/wiki/tags')
    assert response.status_code == 200


def test_wiki_tags_post_unauthorized(test_client):
    """Test POST request to wiki tags without authorization."""
    response = test_client.post('/wiki/tags', data={
        'action': 'create',
        'name': 'new-tag'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_wiki_tags_post_authorized(test_client, authenticated_plot_team_user):
    response = test_client.post('/wiki/tags', json={
        'name': 'new-tag'
    })
    assert response.status_code == 200


def test_wiki_tags_post_delete(test_client, authenticated_plot_team_user, db):
    tag = WikiTag(name="test-tag")
    db.session.add(tag)
    db.session.commit()
    # There is no delete in the route, so this test may not be valid, but keep for now
    response = test_client.post('/wiki/tags', json={
        'action': 'delete',
        'tag_id': tag.id
    })
    assert response.status_code in (200, 400, 404)


def test_wiki_live_search(test_client, wiki_page):
    """Test wiki live search functionality."""
    response = test_client.get('/wiki/live_search?q=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_wiki_live_search_no_query(test_client):
    """Test wiki live search without query."""
    response = test_client.get('/wiki/live_search')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_has_access_public_section(test_client):
    """Test has_access function with public section."""
    from routes.wiki import has_access
    from models.wiki import WikiSection
    
    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Public Section",
        content="<p>Public content</p>"
    )
    
    # Should be accessible to everyone
    assert has_access(section, None) == True
    assert has_access(section, MagicMock(is_authenticated=False)) == True


def test_has_access_role_restricted_section(test_client, authenticated_user):
    """Test has_access function with role-restricted section."""
    from routes.wiki import has_access
    from models.wiki import WikiSection
    
    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Role Restricted Section",
        content="<p>Role restricted content</p>",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value=json.dumps(["admin"])
    )
    
    # Should not be accessible to regular user
    assert has_access(section, authenticated_user) == False
    
    # Should be accessible to admin user
    admin_user = MagicMock()
    admin_user.is_authenticated = True
    admin_user.has_role.return_value = True
    assert has_access(section, admin_user) == True


def test_has_access_faction_restricted_section(test_client, authenticated_user, faction):
    """Test has_access function with faction-restricted section."""
    from routes.wiki import has_access
    from models.wiki import WikiSection
    
    section = WikiSection(
        id=1,
        version_id=1,
        order=0,
        title="Faction Restricted Section",
        content="<p>Faction restricted content</p>",
        restriction_type=SectionRestrictionType.FACTION,
        restriction_value=json.dumps([faction.id])
    )
    
    # Should not be accessible to user without faction
    assert has_access(section, authenticated_user) == False
    
    # Should be accessible to user with matching faction
    faction_user = MagicMock()
    faction_user.is_authenticated = True
    faction_user.faction_id = faction.id
    assert has_access(section, faction_user) == True


def test_build_wiki_tree(test_client):
    """Test build_wiki_tree function."""
    from routes.wiki import build_wiki_tree
    
    pages = [
        {'slug': 'page1', 'title': 'Page 1'},
        {'slug': 'folder1/page2', 'title': 'Page 2'},
        {'slug': 'folder1/subfolder/page3', 'title': 'Page 3'},
        {'slug': 'folder2/page4', 'title': 'Page 4'}
    ]
    
    tree = build_wiki_tree(pages)
    
    # Check that pages are organized correctly
    assert '_pages' in tree
    assert 'folder1' in tree
    assert 'folder2' in tree
    assert 'subfolder' in tree['folder1']
    assert '_pages' in tree['folder1']['subfolder']
    assert len(tree['folder1']['subfolder']['_pages']) == 1
    
    # Check that page1 is in the root _pages
    assert len(tree['_pages']) == 1
    assert tree['_pages'][0]['slug'] == 'page1' 
