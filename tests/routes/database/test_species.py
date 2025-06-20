import pytest
from flask import url_for
from models.database.species import Species, Ability
from models.database.faction import Faction
from models.database.skills import Skill
from models.enums import Role, BodyHitsType, AbilityType
from models.tools.user import User
import uuid
import json
from models.database.item_type import ItemType

def login_user(client, email, password):
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

class TestSpeciesList:
    def test_species_list_unauthorized(self, test_client, species):
        response = test_client.get('/db/species/')
        assert response.status_code == 200
        assert b'Test Species' not in response.data or b'Species' in response.data

    def test_species_list_authorized(self, test_client, rules_team_user, species):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            response = c.get('/db/species/')
            assert response.status_code == 200
            assert species.name.encode() in response.data

class TestNewSpecies:
    def test_new_species_get_unauthorized(self, test_client):
        response = test_client.get('/db/species/new')
        assert response.status_code == 302  # Redirect to login

    def test_new_species_get_authorized(self, test_client, rules_team_user):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            response = c.get('/db/species/new')
            assert response.status_code == 200
            assert b'Create Species' in response.data

    def test_new_species_post_valid_data(self, test_client, rules_team_user, faction, skill):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            unique_name = f"Species {uuid.uuid4().hex[:8]}"
            post_data = {
                'name': unique_name,
                'wiki_page': f"wiki-{uuid.uuid4().hex[:8]}",
                'body_hits_type': BodyHitsType.GLOBAL.value,
                'body_hits': '5',
                'death_count': '2',
                'permitted_factions': str(faction.id),
                'keywords': 'test,unit',
                'ability_name[0]': 'Test Ability',
                'ability_type[0]': AbilityType.GENERIC.value,
                'ability_description[0]': 'A generic ability',
            }
            response = c.post('/db/species/new', data=post_data, follow_redirects=True)
            assert response.status_code == 200
            assert unique_name.encode() in response.data

    def test_new_species_post_missing_fields(self, test_client, rules_team_user):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            post_data = {
                'name': '',
                'wiki_page': '',
                'body_hits_type': '',
                'body_hits': '',
                'death_count': '',
                'permitted_factions': '',
            }
            response = c.post('/db/species/new', data=post_data)
            assert response.status_code == 200
            assert b'All fields are required.' in response.data

class TestEditSpecies:
    def test_edit_species_get_unauthorized(self, test_client, species):
        response = test_client.get(f'/db/species/{species.id}/edit')
        assert response.status_code == 302  # Redirect to login

    def test_edit_species_get_authorized(self, test_client, rules_team_user, species):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            response = c.get(f'/db/species/{species.id}/edit')
            assert response.status_code == 200
            assert species.name.encode() in response.data

    def test_edit_species_post_valid_data(self, test_client, rules_team_user, species, faction):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            new_name = f"Updated Species {uuid.uuid4().hex[:8]}"
            post_data = {
                'name': new_name,
                'wiki_page': f"updated-wiki-{uuid.uuid4().hex[:8]}",
                'body_hits_type': BodyHitsType.LOCATIONAL.value,
                'body_hits': '7',
                'death_count': '4',
                'permitted_factions': str(faction.id),
                'keywords': 'updated,unit',
                'ability_name[0]': 'Updated Ability',
                'ability_type[0]': AbilityType.GENERIC.value,
                'ability_description[0]': 'An updated ability',
            }
            response = c.post(f'/db/species/{species.id}/edit', data=post_data, follow_redirects=True)
            assert response.status_code == 200
            assert new_name.encode() in response.data

    def test_edit_species_post_missing_fields(self, test_client, rules_team_user, species):
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(rules_team_user.id)
            post_data = {
                'name': '',
                'wiki_page': '',
                'body_hits_type': '',
                'body_hits': '',
                'death_count': '',
                'permitted_factions': '',
            }
            response = c.post(f'/db/species/{species.id}/edit', data=post_data)
            assert response.status_code == 200
            assert b'All fields are required.' in response.data 
