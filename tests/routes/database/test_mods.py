import pytest
from flask import url_for
from models.database.mods import Mod
from models.database.item_type import ItemType
from models.wiki import WikiPage
from models.enums import Role
import uuid
from werkzeug.datastructures import MultiDict

def test_mods_list_unauthorized(test_client, db):
    response = test_client.get('/db/mods/')
    assert response.status_code == 200
    assert b'Mod' in response.data or b'mod' in response.data
    assert b'Create Mod' not in response.data

def test_mods_list_authorized(test_client, verified_login, db):
    response = test_client.get('/db/mods/')
    assert response.status_code == 200
    assert b'Mod' in response.data or b'mod' in response.data
    assert b'Create Mod' in response.data

def test_mods_create_get_authorized(test_client, verified_login, db):
    response = test_client.get('/db/mods/new')
    assert response.status_code == 200
    assert b'Mod' in response.data or b'mod' in response.data

def test_mods_create_post_authorized(test_client, verified_login, item_type, db):
    unique_name = f"Mod {uuid.uuid4()}"
    unique_slug = f"mod-{uuid.uuid4()}"
    post_data = MultiDict([
        ('name', unique_name),
        ('wiki_slug', unique_slug),
        ('item_types', str(item_type.id)),
    ])
    response = test_client.post('/db/mods/new', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert b'Mod created successfully' in response.data
    mod = Mod.query.filter_by(name=unique_name).first()
    assert mod is not None
    assert item_type in mod.item_types

def test_mods_create_missing_fields(test_client, verified_login, db):
    post_data = MultiDict([
        ('name', ''),
        ('wiki_slug', ''),
    ])
    response = test_client.post('/db/mods/new', data=post_data, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert b'Name and wiki page are required' in response.data

def test_mods_create_unauthorized(test_client, db):
    response = test_client.get('/db/mods/new')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_mods_edit_get_authorized(test_client, verified_login, mod_obj, db):
    response = test_client.get(f'/db/mods/{mod_obj.id}/edit')
    assert response.status_code == 200
    assert bytes(mod_obj.name, 'utf-8') in response.data

def test_mods_edit_post_authorized(test_client, verified_login, mod_obj, item_type, db):
    new_name = f"Updated Mod {uuid.uuid4()}"
    new_slug = f"updated-mod-{uuid.uuid4()}"
    post_data = MultiDict([
        ('name', new_name),
        ('wiki_slug', new_slug),
        ('item_types', str(item_type.id)),
    ])
    response = test_client.post(f'/db/mods/{mod_obj.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert b'Mod updated successfully' in response.data
    db.session.expire_all()
    updated = Mod.query.get(mod_obj.id)
    assert updated.name == new_name
    assert updated.wiki_slug == new_slug
    assert item_type in updated.item_types

def test_mods_edit_missing_fields(test_client, verified_login, mod_obj, db):
    post_data = MultiDict([
        ('name', ''),
        ('wiki_slug', ''),
    ])
    response = test_client.post(f'/db/mods/{mod_obj.id}/edit', data=post_data, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert b'Name and wiki page are required' in response.data

def test_mods_edit_unauthorized(test_client, mod_obj, db):
    response = test_client.get(f'/db/mods/{mod_obj.id}/edit')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_mods_edit_not_found(test_client, verified_login, db):
    response = test_client.get('/db/mods/99999/edit')
    assert response.status_code == 404 
