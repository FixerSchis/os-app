import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models.database.conditions import Condition, ConditionStage
from models.enums import Role
import json
import uuid
from flask_login import login_user
from werkzeug.datastructures import MultiDict


@pytest.fixture
def condition_with_stages(db, new_user):
    """Fixture for creating a condition with stages."""
    unique_name = f"Test Condition {uuid.uuid4()}"
    condition = Condition(name=unique_name)
    db.session.add(condition)
    db.session.flush()
    
    stage1 = ConditionStage(
        condition_id=condition.id,
        stage_number=1,
        rp_effect="You feel dizzy",
        diagnosis="Minor vertigo",
        cure="Rest",
        duration=2
    )
    stage2 = ConditionStage(
        condition_id=condition.id,
        stage_number=2,
        rp_effect="Severe dizziness",
        diagnosis="Advanced vertigo",
        cure="Medicine",
        duration=4
    )
    
    db.session.add_all([stage1, stage2])
    db.session.commit()
    
    return condition


def test_conditions_list_get(test_client, new_user, condition_with_stages):
    """Test GET request to conditions list page."""
    with test_client.session_transaction() as session:
        session['_user_id'] = new_user.id
        session['_fresh'] = True
    response = test_client.get(f'/db/conditions/')
    assert response.status_code == 200


def test_conditions_list_with_edit_permission(test_client, rules_team_user, condition_with_stages):
    """Test conditions list when user has edit permission."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/db/conditions/')
    assert response.status_code == 200


def test_conditions_create_get_unauthorized(test_client):
    """Test GET request to create condition without authorization."""
    response = test_client.get(f'/db/conditions/new', follow_redirects=True)
    assert response.status_code == 200


def test_conditions_create_get_authorized(test_client, rules_team_user):
    """Test GET request to create condition with authorization."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/db/conditions/new')
    assert response.status_code in (200, 302)


def test_conditions_create_post_unauthorized(test_client):
    """Test POST request to create condition without authorization."""
    response = test_client.post(f'/db/conditions/new', data={
        'name': 'Test Condition',
        'stages': ['1'],
        'rp_effect_1': 'You feel dizzy',
        'diagnosis_1': 'Minor vertigo',
        'cure_1': 'Rest',
        'duration_1': '2'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_conditions_create_post_authorized(test_client, rules_team_user, db):
    """Test POST request to create condition with authorization."""
    from models.enums import Role
    print('Role.RULES_TEAM:', Role.RULES_TEAM)
    print('Role.RULES_TEAM.value:', getattr(Role.RULES_TEAM, 'value', None))
    print('User roles:', rules_team_user.roles)
    print('User email_verified:', rules_team_user.email_verified)
    with test_client as c:
        # Log in via the actual login route
        login_response = c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        print('Login response status:', login_response.status_code)
        # Now make the POST request to create the condition
        post_data = MultiDict([
            ('name', 'New Test Condition'),
            ('stages', '1'),
            ('stages', '2'),
            ('rp_effect_1', 'You feel dizzy'),
            ('diagnosis_1', 'Minor vertigo'),
            ('cure_1', 'Rest'),
            ('duration_1', '2'),
            ('rp_effect_2', 'Severe dizziness'),
            ('diagnosis_2', 'Advanced vertigo'),
            ('cure_2', 'Medicine'),
            ('duration_2', '4')
        ])
        response = c.post(f'/db/conditions/new', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')
        print('Response data:', response.data)
        assert response.status_code == 200
        condition = Condition.query.filter_by(name='New Test Condition').first()
        assert condition is not None
        assert len(condition.stages) == 2
        stage1 = next((s for s in condition.stages if s.stage_number == 1), None)
        assert stage1 is not None
        assert stage1.rp_effect == 'You feel dizzy'
        assert stage1.duration == 2


def test_conditions_create_post_missing_name(test_client, rules_team_user):
    """Test POST request to create condition with missing name."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/new', data={
        'stages': ['1'],
        'rp_effect_1': 'You feel dizzy',
        'diagnosis_1': 'Minor vertigo',
        'cure_1': 'Rest',
        'duration_1': '2'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_create_post_database_error(test_client, rules_team_user, db):
    """Test POST request to create condition with database error."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    # Create a condition with the same name to cause a unique constraint error
    existing_condition = Condition(name='Duplicate Condition')
    db.session.add(existing_condition)
    db.session.commit()
    
    response = test_client.post(f'/db/conditions/new', data={
        'name': 'Duplicate Condition',  # This will cause a unique constraint error
        'stages': ['1'],
        'rp_effect_1': 'You feel dizzy',
        'diagnosis_1': 'Minor vertigo',
        'cure_1': 'Rest',
        'duration_1': '2'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_edit_get_unauthorized(test_client, condition_with_stages):
    """Test GET request to edit condition without authorization."""
    response = test_client.get(f'/db/conditions/{condition_with_stages.id}/edit', follow_redirects=True)
    assert response.status_code == 200


def test_conditions_edit_get_authorized(test_client, rules_team_user, condition_with_stages):
    """Test GET request to edit condition with authorization."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/db/conditions/{condition_with_stages.id}/edit')
    assert response.status_code in (200, 302)


def test_conditions_edit_get_nonexistent(test_client, rules_team_user):
    """Test GET request to edit non-existent condition."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.get(f'/db/conditions/99999/edit')
    assert response.status_code in (404, 302)


def test_conditions_edit_post_unauthorized(test_client, condition_with_stages):
    """Test POST request to edit condition without authorization."""
    response = test_client.post(f'/db/conditions/{condition_with_stages.id}/edit', data={
        'name': 'Updated Condition',
        'stages': ['1'],
        'rp_effect_1': 'Updated effect',
        'diagnosis_1': 'Updated diagnosis',
        'cure_1': 'Updated cure',
        'duration_1': '3'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_conditions_edit_post_authorized(test_client, rules_team_user, condition_with_stages, db):
    """Test POST request to edit condition with authorization."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/{condition_with_stages.id}/edit', data={
        'name': 'Updated Condition',
        'stages': ['1', '2'],
        'rp_effect_1': 'Updated effect 1',
        'diagnosis_1': 'Updated diagnosis 1',
        'cure_1': 'Updated cure 1',
        'duration_1': '3',
        'rp_effect_2': 'Updated effect 2',
        'diagnosis_2': 'Updated diagnosis 2',
        'cure_2': 'Updated cure 2',
        'duration_2': '5'
    }, follow_redirects=True)
    
    if response.status_code != 200:
        print('Response data:', response.data)
    assert response.status_code == 200
    
    # Check that condition was updated
    db.session.refresh(condition_with_stages)
    if condition_with_stages.name != 'Updated Condition':
        print('Condition name:', condition_with_stages.name)
    assert condition_with_stages.name == 'Updated Condition'
    if len(condition_with_stages.stages) != 2:
        print('Stages:', condition_with_stages.stages)
    assert len(condition_with_stages.stages) == 2
    
    stage1 = next((s for s in condition_with_stages.stages if s.stage_number == 1), None)
    assert stage1 is not None
    assert stage1.rp_effect == 'Updated effect 1'
    assert stage1.duration == 3


def test_conditions_edit_post_missing_name(test_client, rules_team_user, condition_with_stages):
    """Test POST request to edit condition with missing name."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/{condition_with_stages.id}/edit', data={
        'stages': ['1'],
        'rp_effect_1': 'Updated effect',
        'diagnosis_1': 'Updated diagnosis',
        'cure_1': 'Updated cure',
        'duration_1': '3'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_edit_post_nonexistent(test_client, rules_team_user):
    """Test POST request to edit non-existent condition."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/99999/edit', data={
        'name': 'Updated Condition',
        'stages': ['1'],
        'rp_effect_1': 'Updated effect',
        'diagnosis_1': 'Updated diagnosis',
        'cure_1': 'Updated cure',
        'duration_1': '3'
    })
    assert response.status_code == 404


def test_conditions_edit_post_database_error(test_client, rules_team_user, condition_with_stages, db):
    """Test POST request to edit condition with database error."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    # Create another condition with the name we're trying to update to
    existing_condition = Condition(name='Duplicate Name')
    db.session.add(existing_condition)
    db.session.commit()
    
    response = test_client.post(f'/db/conditions/{condition_with_stages.id}/edit', data={
        'name': 'Duplicate Name',  # This will cause a unique constraint error
        'stages': ['1'],
        'rp_effect_1': 'Updated effect',
        'diagnosis_1': 'Updated diagnosis',
        'cure_1': 'Updated cure',
        'duration_1': '3'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_edit_post_remove_stages(test_client, rules_team_user, condition_with_stages, db):
    """Test POST request to edit condition and remove stages."""
    from werkzeug.datastructures import MultiDict
    import uuid
    with test_client as c:
        # Log in via the actual login route
        login_response = c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)
        
        unique_name = f"Updated Condition {uuid.uuid4()}"
        # Initially has 2 stages, remove one
        post_data = MultiDict([
            ('name', unique_name),
            ('stages', '1'),  # Only one stage now
            ('rp_effect_1', 'Updated effect'),
            ('diagnosis_1', 'Updated diagnosis'),
            ('cure_1', 'Updated cure'),
            ('duration_1', '3')
        ])
        response = c.post(f'/db/conditions/{condition_with_stages.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')

        if response.status_code != 200:
            print('Response data:', response.data)
        assert response.status_code == 200

        db.session.expire_all()
        updated_condition = Condition.query.get(condition_with_stages.id)
        if len(updated_condition.stages) != 1:
            print('Stages:', updated_condition.stages)
        assert len(updated_condition.stages) == 1


def test_conditions_edit_post_add_stages(test_client, rules_team_user, condition_with_stages, db):
    """Test POST request to edit condition and add stages."""
    from werkzeug.datastructures import MultiDict
    import uuid
    with test_client as c:
        # Log in via the actual login route
        login_response = c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)

        unique_name = f"Updated Condition {uuid.uuid4()}"
        # Initially has 2 stages, add a third
        post_data = MultiDict([
            ('name', unique_name),
            ('stages', '1'),
            ('stages', '2'),
            ('stages', '3'),  # Three stages now
            ('rp_effect_1', 'Effect 1'),
            ('diagnosis_1', 'Diagnosis 1'),
            ('cure_1', 'Cure 1'),
            ('duration_1', '2'),
            ('rp_effect_2', 'Effect 2'),
            ('diagnosis_2', 'Diagnosis 2'),
            ('cure_2', 'Cure 2'),
            ('duration_2', '4'),
            ('rp_effect_3', 'Effect 3'),
            ('diagnosis_3', 'Diagnosis 3'),
            ('cure_3', 'Cure 3'),
            ('duration_3', '6')
        ])
        response = c.post(f'/db/conditions/{condition_with_stages.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')

        if response.status_code != 200:
            print('Response data:', response.data)
        assert response.status_code == 200

        db.session.expire_all()
        updated_condition = Condition.query.get(condition_with_stages.id)
        if len(updated_condition.stages) != 3:
            print('Stages:', updated_condition.stages)
        assert len(updated_condition.stages) == 3


def test_conditions_create_post_invalid_duration(test_client, rules_team_user):
    """Test POST request to create condition with invalid duration."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/new', data={
        'name': 'Test Condition',
        'stages': ['1'],
        'rp_effect_1': 'You feel dizzy',
        'diagnosis_1': 'Minor vertigo',
        'cure_1': 'Rest',
        'duration_1': 'invalid'  # Invalid duration
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_edit_post_invalid_duration(test_client, rules_team_user, condition_with_stages):
    """Test POST request to edit condition with invalid duration."""
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/{condition_with_stages.id}/edit', data={
        'name': 'Updated Condition',
        'stages': ['1'],
        'rp_effect_1': 'Updated effect',
        'diagnosis_1': 'Updated diagnosis',
        'cure_1': 'Updated cure',
        'duration_1': 'invalid'  # Invalid duration
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_conditions_create_post_empty_stages(test_client, rules_team_user, db):
    """Test POST request to create condition with no stages."""
    import uuid
    unique_name = f"Test Condition Empty Stages {uuid.uuid4()}"
    
    with test_client.session_transaction() as session:
        session['_user_id'] = rules_team_user.id
        session['_fresh'] = True
    
    response = test_client.post(f'/db/conditions/new', data={
        'name': unique_name
        # No stages data
    }, follow_redirects=True)
    
    if response.status_code != 200:
        print('Response data:', response.data)
    assert response.status_code == 200
    
    # Check that condition was created without stages
    condition = Condition.query.filter_by(name=unique_name).first()
    assert condition is not None
    assert len(condition.stages) == 0


def test_conditions_edit_post_empty_stages(test_client, rules_team_user, condition_with_stages, db):
    """Test POST request to edit condition and remove all stages."""
    from werkzeug.datastructures import MultiDict
    import uuid
    with test_client as c:
        # Log in via the actual login route
        login_response = c.post('/auth/login', data={
            'email': rules_team_user.email,
            'password': 'password123',
        }, follow_redirects=True)

        unique_name = f"Updated Condition {uuid.uuid4()}"
        post_data = MultiDict([
            ('name', unique_name)
            # No stages data - empty stages
        ])
        response = c.post(f'/db/conditions/{condition_with_stages.id}/edit', data=post_data, follow_redirects=True, content_type='application/x-www-form-urlencoded')

        if response.status_code != 200:
            print('Response data:', response.data)
        assert response.status_code == 200

        db.session.expire_all()
        updated_condition = Condition.query.get(condition_with_stages.id)
        if len(updated_condition.stages) != 0:
            print('Stages:', updated_condition.stages)
        assert len(updated_condition.stages) == 0 
