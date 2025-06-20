import pytest
from flask import url_for
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.mods import Mod
from models.enums import Role, PrintTemplateType
import uuid
from werkzeug.datastructures import MultiDict
from datetime import datetime, timedelta

@pytest.fixture
def print_template_obj(db, rules_team_user):
    from models.tools.print_template import PrintTemplate
    # Only create if not exists
    template = PrintTemplate.query.filter_by(type=PrintTemplateType.ITEM_CARD.value).first()
    if not template:
        template = PrintTemplate(
            type=PrintTemplateType.ITEM_CARD.value,
            type_name=f"Item Template {uuid.uuid4()}",
            front_html="<div>Front {{ item.full_code }}</div>",
            back_html="<div>Back {{ item.full_code }}</div>",
            css_styles="body { color: black; }",
            has_back_side=True,
            created_by_user_id=rules_team_user.id
        )
        db.session.add(template)
        db.session.commit()
    return template

def test_items_list_unauthorized(test_client, db):
    response = test_client.get('/db/items/')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_items_list_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/items/')
        assert response.status_code == 200
        assert b'Item' in response.data or b'item' in response.data

def test_items_create_get_authorized(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/items/create')
        assert response.status_code == 200
        assert b'Item' in response.data or b'item' in response.data

def test_items_create_post_authorized(test_client, rules_team_user, item_blueprint, mod, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        expiry = int((datetime.now() + timedelta(days=30)).timestamp())
        post_data = MultiDict([
            ('blueprint_id', str(item_blueprint.id)),
            ('expiry', str(expiry)),
            ('mods_applied[]', str(mod.id)),
        ])
        response = c.post('/db/items/create', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Item created successfully' in response.data
        item = Item.query.filter_by(blueprint_id=item_blueprint.id, item_id=1).first()
        assert item is not None
        assert item.expiry == expiry

def test_items_create_missing_blueprint(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        post_data = MultiDict([
            ('blueprint_id', ''),
            ('expiry', ''),
        ])
        response = c.post('/db/items/create', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Blueprint is required' in response.data

def test_items_create_unauthorized(test_client, db):
    response = test_client.get('/db/items/create')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_items_edit_get_authorized(test_client, rules_team_user, item, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get(f'/db/items/{item.id}/edit')
        assert response.status_code == 200
        assert bytes(str(item.item_id), 'utf-8') in response.data

def test_items_edit_post_authorized(test_client, rules_team_user, item, item_blueprint, mod, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        new_expiry = int((datetime.now() + timedelta(days=60)).timestamp())
        post_data = MultiDict([
            ('blueprint_id', str(item_blueprint.id)),
            ('expiry', str(new_expiry)),
            ('mods_applied[]', str(mod.id)),
        ])
        response = c.post(f'/db/items/{item.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Item updated successfully' in response.data
        db.session.expire_all()
        updated = Item.query.get(item.id)
        assert updated.expiry == new_expiry

def test_items_edit_missing_blueprint(test_client, rules_team_user, item, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        post_data = MultiDict([
            ('blueprint_id', ''),
            ('expiry', ''),
        ])
        response = c.post(f'/db/items/{item.id}/edit', data=post_data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert b'Blueprint is required' in response.data

def test_items_edit_unauthorized(test_client, item, db):
    response = test_client.get(f'/db/items/{item.id}/edit')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_items_edit_not_found(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get('/db/items/99999/edit')
        assert response.status_code == 404

def test_items_delete_authorized(test_client, rules_team_user, item, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.post(f'/db/items/{item.id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Item deleted successfully' in response.data
        deleted_item = Item.query.get(item.id)
        assert deleted_item is None

def test_items_delete_unauthorized(test_client, item, db):
    response = test_client.post(f'/db/items/{item.id}/delete')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_items_delete_not_found(test_client, rules_team_user, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.post('/db/items/99999/delete', follow_redirects=True)
        assert response.status_code == 404

def test_items_find_by_code_success(test_client, item, db):
    print(f"DEBUG: item.full_code = {item.full_code}")
    response = test_client.get(f'/db/items/find_by_code?full_code={item.full_code}')
    assert response.status_code == 200
    assert bytes(str(item.item_id), 'utf-8') in response.data

def test_items_find_by_code_missing_code(test_client, db):
    response = test_client.get('/db/items/find_by_code')
    assert response.status_code == 400
    assert b'Missing full_code' in response.data

def test_items_find_by_code_invalid_format(test_client, db):
    response = test_client.get('/db/items/find_by_code?full_code=invalid')
    assert response.status_code == 404
    assert b'Item not found' in response.data

def test_items_find_by_code_not_found(test_client, db):
    response = test_client.get('/db/items/find_by_code?full_code=IT0000-000')
    assert response.status_code == 404
    assert b'Item not found' in response.data

def test_items_engineering_cost_item_maintain(test_client, item, db):
    response = test_client.post('/db/items/engineering_cost', json={'item_id': item.id, 'action': 'maintain'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'cost' in data
    assert isinstance(data['cost'], (int, float))

def test_items_engineering_cost_item_modify(test_client, item, db):
    response = test_client.post('/db/items/engineering_cost', json={'item_id': item.id, 'action': 'modify'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'cost' in data
    assert isinstance(data['cost'], (int, float))

def test_items_engineering_cost_blueprint_maintain(test_client, item_blueprint, db):
    response = test_client.post('/db/items/engineering_cost', json={'blueprint_id': item_blueprint.id, 'action': 'maintain'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'cost' in data
    assert isinstance(data['cost'], (int, float))

def test_items_engineering_cost_blueprint_modify(test_client, item_blueprint, db):
    response = test_client.post('/db/items/engineering_cost', json={'blueprint_id': item_blueprint.id, 'action': 'modify'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'cost' in data
    assert isinstance(data['cost'], (int, float))

def test_items_engineering_cost_invalid_action(test_client, item, db):
    response = test_client.post('/db/items/engineering_cost', json={'item_id': item.id, 'action': 'invalid'})
    assert response.status_code == 400
    assert b'Invalid action' in response.data

def test_items_engineering_cost_no_id(test_client, db):
    response = test_client.post('/db/items/engineering_cost', json={'action': 'maintain'})
    assert response.status_code == 400
    assert b'No item_id or blueprint_id provided' in response.data

def test_items_view_unauthorized(test_client, item, print_template_obj, db):
    response = test_client.get(f'/db/items/{item.id}/view')
    assert response.status_code == 200

def test_items_view_authorized(test_client, rules_team_user, item, print_template_obj, db):
    with test_client as c:
        c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        response = c.get(f'/db/items/{item.id}/view')
        assert response.status_code == 200
        assert bytes(str(item.item_id), 'utf-8') in response.data

def test_items_view_not_found(test_client, db):
    response = test_client.get('/db/items/99999/view')
    assert response.status_code == 404 
