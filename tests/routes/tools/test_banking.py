import pytest
from flask import url_for
from models.tools.character import Character
from models.tools.group import Group
from models.tools.user import User
from models.database.faction import Faction
from models.database.species import Species
from models.enums import Role, CharacterStatus, GroupType
from models.extensions import db
import uuid
import json

def login_user(client, email, password):
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

class TestBankingAccess:
    def test_bank_unauthorized(self, test_client):
        """Test bank page access without login."""
        response = test_client.get('/banking/')
        assert response.status_code == 302  # Redirect to login

    def test_bank_regular_user_no_active_character(self, test_client, regular_user):
        """Test bank page access for regular user without active character."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.get('/banking/', follow_redirects=True)
            assert response.status_code == 200
            assert b'You need an active character to access banking' in response.data

    def test_bank_regular_user_with_active_character(self, test_client, regular_user, character_with_faction):
        """Test bank page access for regular user with active character."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.get('/banking/')
            assert response.status_code == 200
            assert character_with_faction.name.encode() in response.data

    def test_bank_admin_user(self, test_client, user_admin, character_with_faction, group):
        """Test bank page access for admin user."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.get('/banking/')
            assert response.status_code == 200
            assert character_with_faction.name.encode() in response.data
            assert group.name.encode() in response.data

    def test_bank_admin_user_with_selected_accounts(self, test_client, user_admin, character_with_faction, group):
        """Test bank page access for admin user with selected accounts."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.get(f'/banking/?character_id={character_with_faction.id}&group_id={group.id}')
            assert response.status_code == 200
            assert character_with_faction.name.encode() in response.data
            assert group.name.encode() in response.data

class TestUpdateBalance:
    def test_update_balance_unauthorized(self, test_client):
        """Test update balance without login."""
        response = test_client.post('/banking/update-balance', data={
            'account_type': 'character',
            'account_id': '1',
            'balance': '1000'
        })
        assert response.status_code == 302  # Redirect to login

    def test_update_balance_regular_user(self, test_client, regular_user, character_with_faction):
        """Test update balance as regular user (should fail)."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/update-balance', data={
                'account_type': 'character',
                'account_id': str(character_with_faction.id),
                'balance': '1000'
            })
            assert response.status_code == 403  # Forbidden (access denied)

    def test_update_balance_admin_character(self, test_client, user_admin, character_with_faction):
        """Test update balance for character as admin."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.post('/banking/update-balance', data={
                'account_type': 'character',
                'account_id': str(character_with_faction.id),
                'balance': '1500'
            })
            assert response.status_code == 302  # Redirect on success
            # Verify the balance was actually updated
            db.session.refresh(character_with_faction)
            assert character_with_faction.bank_account == 1500

    def test_update_balance_admin_group(self, test_client, user_admin, group):
        """Test update balance for group as admin."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.post('/banking/update-balance', data={
                'account_type': 'group',
                'account_id': str(group.id),
                'balance': '750'
            })
            assert response.status_code == 302  # Redirect on success
            # Verify the balance was actually updated
            db.session.refresh(group)
            assert group.bank_account == 750

    def test_update_balance_invalid_amount(self, test_client, user_admin, character_with_faction):
        """Test update balance with invalid amount."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.post('/banking/update-balance', data={
                'account_type': 'character',
                'account_id': str(character_with_faction.id),
                'balance': 'invalid'
            })
            assert response.status_code == 302  # Redirect on error

    def test_update_balance_nonexistent_character(self, test_client, user_admin):
        """Test update balance for nonexistent character."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.post('/banking/update-balance', data={
                'account_type': 'character',
                'account_id': '99999',
                'balance': '1000'
            })
            assert response.status_code == 404  # get_or_404 returns 404 for nonexistent character

class TestTransfer:
    def test_transfer_unauthorized(self, test_client):
        """Test transfer without login."""
        response = test_client.post('/banking/transfer', data={
            'source_type': 'character',
            'source_id': '1',
            'target_type': 'character',
            'target_id': '2',
            'amount': '100'
        })
        assert response.status_code == 302  # Redirect to login

    def test_transfer_regular_user_own_character(self, test_client, regular_user, character_with_faction, admin_character):
        """Test transfer from regular user's own character to admin character."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': '100'
            })
            assert response.status_code == 302  # Redirect on success
            # Verify the balances were updated
            db.session.refresh(character_with_faction)
            assert character_with_faction.bank_account == 400  # 500 - 100

    def test_transfer_regular_user_own_group(self, test_client, regular_user, character_with_group, admin_character):
        """Test transfer from regular user's own group to admin character."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'group',
                'source_id': str(character_with_group.group_id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': '100'
            })
            assert response.status_code == 302  # Redirect on success
            # Verify the balances were updated
            db.session.refresh(character_with_group)
            group = Group.query.get(character_with_group.group_id)
            assert group.bank_account == 400  # 500 - 100

    def test_transfer_admin_any_account(self, test_client, user_admin, character_with_faction, group, admin_character):
        """Test transfer between any accounts as admin."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(user_admin.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'group',
                'target_id': str(group.id),
                'amount': '100'
            })
            assert response.status_code == 302  # Redirect on success
            # Verify the balances were updated
            db.session.refresh(character_with_faction)
            db.session.refresh(group)
            assert character_with_faction.bank_account == 400  # 500 - 100
            assert group.bank_account == 600  # 500 + 100

    def test_transfer_regular_user_unauthorized_character(self, test_client, regular_user, admin_character):
        """Test transfer from unauthorized character (should fail)."""
        # Create another character that doesn't belong to regular_user
        other_character = Character(
            user_id=admin_character.user_id,
            name='Other Character',
            status=CharacterStatus.ACTIVE.value,
            bank_account=1000
        )
        db.session.add(other_character)
        db.session.commit()
        
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(other_character.id),
                'target_type': 'character',
                'target_id': str(regular_user.id),
                'amount': '100'
            })
            assert response.status_code == 302  # Redirect on error (access denied)

    def test_transfer_regular_user_unauthorized_group(self, test_client, regular_user, group, admin_character):
        """Test transfer from unauthorized group (should fail)."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'group',
                'source_id': str(group.id),
                'target_type': 'character',
                'target_id': str(regular_user.id),
                'amount': '100'
            })
            assert response.status_code == 302  # Redirect on error (access denied)

    def test_transfer_insufficient_funds(self, test_client, regular_user, character_with_faction, admin_character):
        """Test transfer with insufficient funds."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': '1000'  # More than available (500)
            })
            assert response.status_code == 302  # Redirect on error (insufficient funds)

    def test_transfer_invalid_amount(self, test_client, regular_user, character_with_faction, admin_character):
        """Test transfer with invalid amount."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': 'invalid'
            })
            assert response.status_code == 302  # Redirect on error (invalid amount)

    def test_transfer_negative_amount(self, test_client, regular_user, character_with_faction, admin_character):
        """Test transfer with negative amount."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': '-100'
            })
            assert response.status_code == 302  # Redirect on error (negative amount)

    def test_transfer_zero_amount(self, test_client, regular_user, character_with_faction, admin_character):
        """Test transfer with zero amount."""
        with test_client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
            response = c.post('/banking/transfer', data={
                'source_type': 'character',
                'source_id': str(character_with_faction.id),
                'target_type': 'character',
                'target_id': str(admin_character.id),
                'amount': '0'
            })
            assert response.status_code == 302  # Redirect on error (zero amount) 