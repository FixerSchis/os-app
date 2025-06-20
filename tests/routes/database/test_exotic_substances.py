import pytest
from flask import url_for
from models.database.exotic_substances import ExoticSubstance
from models.enums import Role, ScienceType
import uuid
from werkzeug.datastructures import MultiDict

def test_exotic_substances_list_unauthorized(test_client, db):
    response = test_client.get('/db/exotic-substances/')
    assert response.status_code == 200
    assert b'Exotic' in response.data or b'exotic' in response.data
    assert b'New Exotic Substance' not in response.data

def test_exotic_substances_list_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/exotic-substances/')
        assert response.status_code == 200
        assert b'Exotic' in response.data or b'exotic' in response.data

def test_exotic_substances_create_get_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/exotic-substances/new')
        assert response.status_code == 200
        assert b'Exotic' in response.data or b'exotic' in response.data

def test_exotic_substances_create_post_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        unique_name = f"Exotic Substance {uuid.uuid4()}"
        post_data = MultiDict([
            ('name', unique_name),
            ('type', ScienceType.GENERIC.value),
            ('wiki_slug', f'exotic-substance-{uuid.uuid4()}')
        ])
        response = c.post('/db/exotic-substances/new', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Exotic substance created' in response.data
        substance = ExoticSubstance.query.filter_by(name=unique_name).first()
        assert substance is not None
        assert substance.type == ScienceType.GENERIC

def test_exotic_substances_edit_get_authorized(test_client, rules_team_user, exotic_substance, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get(f'/db/exotic-substances/{exotic_substance.id}/edit')
        assert response.status_code == 200
        assert bytes(exotic_substance.name, 'utf-8') in response.data

def test_exotic_substances_edit_post_authorized(test_client, rules_team_user, exotic_substance, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        new_name = f"Updated Exotic Substance {uuid.uuid4()}"
        post_data = MultiDict([
            ('name', new_name),
            ('type', ScienceType.LIFE.value),
            ('wiki_slug', f'updated-exotic-substance-{uuid.uuid4()}')
        ])
        response = c.post(f'/db/exotic-substances/{exotic_substance.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Exotic substance updated' in response.data
        db.session.expire_all()
        updated = ExoticSubstance.query.get(exotic_substance.id)
        assert updated.name == new_name
        assert updated.type == ScienceType.LIFE

def test_exotic_substances_create_missing_fields(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        post_data = MultiDict([
            ('name', ''),
            ('type', ''),
            ('wiki_slug', '')
        ])
        response = c.post('/db/exotic-substances/new', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'All fields are required' in response.data

def test_exotic_substances_edit_missing_fields(test_client, rules_team_user, exotic_substance, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        post_data = MultiDict([
            ('name', ''),
            ('type', ''),
            ('wiki_slug', '')
        ])
        response = c.post(f'/db/exotic-substances/{exotic_substance.id}/edit', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'All fields are required' in response.data

def test_exotic_substances_create_invalid_type(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        unique_name = f"Exotic Substance {uuid.uuid4()}"
        post_data = MultiDict([
            ('name', unique_name),
            ('type', 'invalid_type'),
            ('wiki_slug', f'exotic-substance-{uuid.uuid4()}')
        ])
        response = c.post('/db/exotic-substances/new', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Invalid substance type' in response.data

def test_exotic_substances_edit_invalid_type(test_client, rules_team_user, exotic_substance, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        new_name = f"Updated Exotic Substance {uuid.uuid4()}"
        post_data = MultiDict([
            ('name', new_name),
            ('type', 'invalid_type'),
            ('wiki_slug', f'updated-exotic-substance-{uuid.uuid4()}')
        ])
        response = c.post(f'/db/exotic-substances/{exotic_substance.id}/edit', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Invalid substance type' in response.data

def test_exotic_substances_edit_not_found(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/exotic-substances/99999/edit')
        assert response.status_code == 404 
