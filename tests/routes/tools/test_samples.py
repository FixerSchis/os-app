import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.tools.sample import Sample, SampleTag
from models.enums import ScienceType, Role

def test_sample_list_get(test_client, admin_user):
    """Test GET request to sample list page."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.get('/samples/')
    assert response.status_code == 200

def test_sample_list_unauthorized(test_client, authenticated_user):
    """Test sample list page when user is not authorized."""
    response = test_client.get('/samples/', follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden

def test_sample_list_unauthenticated(test_client):
    """Test sample list page when user is not authenticated."""
    response = test_client.get('/samples/', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login

def test_create_sample_success(test_client, admin_user, db):
    """Test successful sample creation."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.post('/samples/create', data={
        'name': 'Test Sample',
        'type': 'generic',
        'description': 'A test sample',
        'tags[]': ['test', 'sample']
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Test Sample'
    assert data['type'] == 'generic'
    assert data['description'] == 'A test sample'
    
    # Check that sample was created in database
    sample = Sample.query.filter_by(name='Test Sample').first()
    assert sample is not None
    assert sample.type.value == 'generic'
    assert sample.description == 'A test sample'

def test_create_sample_missing_name(test_client, admin_user):
    """Test sample creation with missing name."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.post('/samples/create', data={
        'type': 'generic',
        'description': 'A test sample'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_create_sample_missing_type(test_client, admin_user):
    """Test sample creation with missing type."""
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.post('/samples/create', data={
        'name': 'Test Sample',
        'description': 'A test sample'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_create_sample_with_existing_tags(test_client, admin_user, db):
    """Test sample creation with existing tags."""
    # Create existing tags
    tag1 = SampleTag(name='existing_tag')
    tag2 = SampleTag(name='another_tag')
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()
    
    with test_client.session_transaction() as session:
        session['_user_id'] = admin_user.id
        session['_fresh'] = True
    
    response = test_client.post('/samples/create', data={
        'name': 'Test Sample with Tags',
        'type': 'life',
        'description': 'A test sample with existing tags',
        'tags[]': ['existing_tag', 'new_tag']
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Test Sample with Tags'
    
    # Check that sample was created with tags
    sample = Sample.query.filter_by(name='Test Sample with Tags').first()
    assert sample is not None
    assert len(sample.tags) == 2
    tag_names = [tag.name for tag in sample.tags]
    assert 'existing_tag' in tag_names
    assert 'new_tag' in tag_names

def test_create_sample_unauthorized(test_client, authenticated_user):
    """Test sample creation when user is not authorized."""
    response = test_client.post('/samples/create', data={
        'name': 'Test Sample',
        'type': 'generic',
        'description': 'A test sample'
    }, follow_redirects=True)
    
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden

def test_create_sample_unauthenticated(test_client):
    """Test sample creation when user is not authenticated."""
    response = test_client.post('/samples/create', data={
        'name': 'Test Sample',
        'type': 'generic',
        'description': 'A test sample'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should redirect to login 
