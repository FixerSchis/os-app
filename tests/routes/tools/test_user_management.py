import uuid
import pytest
from flask import url_for
from models.tools.user import User
from models.tools.character import Character, CharacterStatus, CharacterTag
from models.enums import Role
from models.database.faction import Faction


class TestUserManagementRoutes:
    """Test user management routes"""

    def test_user_management_list(self, test_client, admin_user, db):
        """Test user management list page"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = test_client.get('/users/user-management')
        assert response.status_code == 200
        assert b'User Management' in response.data

    def test_user_management_list_requires_admin(self, test_client, regular_user, db):
        """Test user management list requires admin role"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = regular_user.id
            sess['_fresh'] = True
        
        response = test_client.get('/users/user-management')
        assert response.status_code == 403

    def test_user_management_edit_user(self, test_client, admin_user, regular_user, db):
        """Test user management edit user page"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = test_client.get(f'/users/user-management/user/{regular_user.id}')
        assert response.status_code == 200
        assert regular_user.email.encode() in response.data

    def test_user_management_edit_user_requires_admin(self, test_client, regular_user, db):
        """Test user management edit user requires admin role"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = regular_user.id
            sess['_fresh'] = True
        
        response = test_client.get('/users/user-management/user/1')
        assert response.status_code == 403

    def test_user_management_edit_user_not_found(self, test_client, admin_user, db):
        """Test user management edit user with non-existent user"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = test_client.get('/users/user-management/user/999')
        assert response.status_code == 404

    def test_update_user_basic_info(self, test_client, admin_user, regular_user, db):
        """Test updating user basic information"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': 'newemail@example.com',
            'first_name': 'New',
            'surname': 'Name',
            'pronouns_subject': 'they',
            'pronouns_object': 'them',
            'player_id': '123',
            'character_points': '50.0'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Check that user was updated
        updated_user = User.query.get(regular_user.id)
        assert updated_user.email == 'newemail@example.com'
        assert updated_user.first_name == 'New'
        assert updated_user.surname == 'Name'
        assert updated_user.pronouns_subject == 'they'
        assert updated_user.pronouns_object == 'them'
        assert updated_user.player_id == 123
        assert updated_user.character_points == 50.0

    def test_update_user_clear_player_id(self, test_client, admin_user, regular_user, db):
        """Test clearing user player ID"""
        regular_user.player_id = 123
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': regular_user.email,
            'first_name': regular_user.first_name,
            'surname': regular_user.surname,
            'player_id': '',
            'character_points': '0.0'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        updated_user = User.query.get(regular_user.id)
        assert updated_user.player_id is None

    def test_update_user_invalid_player_id(self, test_client, admin_user, regular_user, db):
        """Test updating user with invalid player ID"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': regular_user.email,
            'first_name': regular_user.first_name,
            'surname': regular_user.surname,
            'player_id': 'invalid',
            'character_points': '0.0'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Player ID must be an integer' in response.data

    def test_update_user_duplicate_player_id(self, test_client, admin_user, regular_user, db):
        """Test updating user with duplicate player ID"""
        # Create another user with player_id 123
        other_user = User(
            email='other@example.com',
            password_hash='hash',
            first_name='Other',
            surname='User'
        )
        other_user.player_id = 123
        db.session.add(other_user)
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': regular_user.email,
            'first_name': regular_user.first_name,
            'surname': regular_user.surname,
            'player_id': '123',
            'character_points': '0.0'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Player ID already in use' in response.data

    def test_update_user_negative_character_points(self, test_client, admin_user, regular_user, db):
        """Test updating user with negative character points"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': regular_user.email,
            'first_name': regular_user.first_name,
            'surname': regular_user.surname,
            'player_id': '',
            'character_points': '-10.0'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Character points cannot be negative' in response.data

    def test_update_user_invalid_character_points(self, test_client, admin_user, regular_user, db):
        """Test updating user with invalid character points"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_user': '1',
            'email': regular_user.email,
            'first_name': regular_user.first_name,
            'surname': regular_user.surname,
            'player_id': '',
            'character_points': 'invalid'
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Character points must be a number' in response.data

    def test_add_role(self, test_client, admin_user, regular_user, db):
        """Test adding role to user"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True

        data = {
            'add_role': '1',
            'role': Role.RULES_TEAM.value
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Check that role was added
        updated_user = User.query.get(regular_user.id)
        assert updated_user.has_role(Role.RULES_TEAM.value)

    def test_add_owner_role_requires_owner(self, test_client, admin_user, regular_user, db):
        """Test adding owner role requires owner permission"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'add_role': '1',
            'role': Role.OWNER.value
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'You do not have permission to add the owner role' in response.data

    def test_add_admin_role_requires_owner(self, test_client, admin_user, regular_user, db):
        """Test adding admin role requires owner permission"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'add_role': '1',
            'role': Role.ADMIN.value
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'You do not have permission to add the admin role' in response.data

    def test_remove_role(self, test_client, admin_user, regular_user, db):
        """Test removing role from user"""
        regular_user.add_role(Role.RULES_TEAM.value)
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'remove_role': '1',
            'role': Role.RULES_TEAM.value
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Role removed successfully' in response.data
        
        updated_user = User.query.get(regular_user.id)
        assert not updated_user.has_role(Role.RULES_TEAM.value)

    def test_add_tag(self, test_client, admin_user, regular_user, db):
        """Test adding tag to user"""
        tag = CharacterTag(name='Test Tag')
        db.session.add(tag)
        db.session.commit()
        
        # Create an active character for the user
        character = Character(user_id=regular_user.id, name='Active Character', status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'add_tag': '1',
            'tag_id': str(tag.id)
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Tag added successfully' in response.data
        
        updated_character = Character.query.get(character.id)
        assert tag in updated_character.tags

    def test_remove_tag(self, test_client, admin_user, regular_user, db):
        """Test removing tag from user"""
        tag = CharacterTag(name='Test Tag')
        db.session.add(tag)
        db.session.commit()
        
        # Create an active character for the user and add the tag
        character = Character(user_id=regular_user.id, name='Active Character', status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        character.tags.append(tag)
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'remove_tag': '1',
            'tag_id': str(tag.id)
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Tag removed successfully' in response.data
        
        updated_character = Character.query.get(character.id)
        assert tag not in updated_character.tags

    def test_update_character_status(self, test_client, admin_user, regular_user, db):
        """Test updating character status"""
        character = Character(
            name='Test Character',
            user_id=regular_user.id,
            status=CharacterStatus.ACTIVE.value
        )
        db.session.add(character)
        db.session.commit()
        
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'update_character_status': '1',
            'character_id': str(character.id),
            'status': CharacterStatus.RETIRED.value
        }
        
        response = test_client.post(f'/users/user-management/user/{regular_user.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Character status updated successfully' in response.data
        
        updated_character = Character.query.get(character.id)
        assert updated_character.status == CharacterStatus.RETIRED.value 
