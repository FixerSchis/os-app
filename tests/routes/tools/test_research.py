import pytest
from flask import url_for
from models.tools.research import Research, ResearchStage, ResearchStageRequirement, CharacterResearch, CharacterResearchStage, CharacterResearchStageRequirement
from models.tools.character import Character
from models.tools.user import User
from models.tools.sample import SampleTag
from models.database.faction import Faction
from models.database.species import Species
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.exotic_substances import ExoticSubstance
from models.enums import Role, CharacterStatus, ResearchType, ScienceType, ResearchRequirementType
from models.extensions import db
import uuid
import json

def login_user(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

class TestResearchAccess:
    def test_research_list_unauthorized(self, test_client):
        response = test_client.get('/research/')
        assert response.status_code == 302  # Redirect to login

    def test_research_list_authorized(self, test_client, user_rules_team):
        login_user(test_client, user_rules_team)
        response = test_client.get('/research/')
        assert response.status_code == 200

    def test_research_create_unauthorized(self, test_client):
        response = test_client.get('/research/create')
        assert response.status_code == 302  # Redirect to login

    def test_research_create_authorized(self, test_client, user_rules_team):
        login_user(test_client, user_rules_team)
        response = test_client.get('/research/create')
        assert response.status_code == 200

class TestResearchCRUD:
    def test_create_research_success(self, test_client, user_rules_team, item_type):
        login_user(test_client, user_rules_team)
        unique_name = f"Test Research {uuid.uuid4().hex[:8]}"
        response = test_client.post('/research/create', data={
            'project_name': unique_name,
            'type': 'invention',
            'description': 'Test research description',
            'blueprint_id': str(item_type.id)
        }, follow_redirects=True)
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_create_artefact_research_new(self, test_client, user_rules_team, item_type):
        login_user(test_client, user_rules_team)
        unique_name = f"Test Artefact {uuid.uuid4().hex[:8]}"
        response = test_client.post('/research/create', data={
            'project_name': unique_name,
            'type': 'artefact',
            'description': 'Test artefact research',
            'blueprint_id': str(item_type.id)
        }, follow_redirects=True)
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_create_artefact_research_existing(self, test_client, user_rules_team, item):
        login_user(test_client, user_rules_team)
        unique_name = f"Test Artefact {uuid.uuid4().hex[:8]}"
        response = test_client.post('/research/create', data={
            'project_name': unique_name,
            'type': 'artefact',
            'description': 'Test artefact research',
            'item_id': str(item.id)
        }, follow_redirects=True)
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_edit_research_get(self, test_client, user_rules_team, research_project_with_stage):
        login_user(test_client, user_rules_team)
        response = test_client.get(f'/research/{research_project_with_stage.id}/edit')
        assert response.status_code == 200
        assert research_project_with_stage.project_name.encode() in response.data

class TestResearchAPI:
    def test_api_blueprints(self, test_client, user_rules_team, item_blueprint):
        login_user(test_client, user_rules_team)
        response = test_client.get('/research/api/blueprints')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0

    def test_api_exotics(self, test_client, user_rules_team, exotic_substance):
        login_user(test_client, user_rules_team)
        response = test_client.get('/research/api/exotics')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0

class TestResearchAssignees:
    def test_assignees_list(self, test_client, user_rules_team, research_project_with_stage):
        login_user(test_client, user_rules_team)
        response = test_client.get(f'/research/{research_project_with_stage.id}/assignees')
        assert response.status_code == 200

    def test_remove_assignee(self, test_client, user_rules_team, research_project_with_stage, character_research_with_stage):
        login_user(test_client, user_rules_team)
        response = test_client.post(f'/research/{research_project_with_stage.id}/assignees/{character_research_with_stage.id}/remove', follow_redirects=True)
        assert response.status_code == 200

    def test_edit_progress_get(self, test_client, user_rules_team, research_project_with_stage, character_research_with_stage):
        login_user(test_client, user_rules_team)
        response = test_client.get(f'/research/{research_project_with_stage.id}/assignees/{character_research_with_stage.id}/progress')
        assert response.status_code == 200

class TestResearchProjectInfo:
    def test_project_info_forbidden(self, test_client, regular_user, research_project_with_stage, character_with_faction):
        # Assign the research to the character owned by regular_user
        from models.tools.research import CharacterResearch
        from models.tools.research import ResearchStage
        stage = ResearchStage.query.filter_by(research_id=research_project_with_stage.id).first()
        cr = CharacterResearch(
            character_id=character_with_faction.id,
            research_id=research_project_with_stage.id,
            current_stage_id=stage.id
        )
        from models.extensions import db
        db.session.add(cr)
        db.session.commit()
        
        login_user(test_client, regular_user)
        response = test_client.get(f'/research/{research_project_with_stage.id}')
        assert response.status_code in (302, 403, 404)  # Should not be accessible to regular users

    def test_project_info_not_found(self, test_client, regular_user):
        login_user(test_client, regular_user)
        response = test_client.get('/research/99999')
        assert response.status_code in (302, 403, 404)
