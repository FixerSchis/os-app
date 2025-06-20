import pytest
from models.tools.group import Group, GroupInvite
from models.tools.character import Character
from models.enums import CharacterStatus, Role, GroupType

class TestGroupsRoutes:
    def test_group_list_admin(self, test_client, admin_user, db):
        """Admin sees all groups"""
        group = Group(name='Test Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        resp = test_client.get('/groups/')
        assert resp.status_code == 200
        assert b'Test Group' in resp.data

    def test_group_list_regular_user_with_active_character(self, test_client, new_user, db):
        """Regular user with active character sees their group list"""
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.get('/groups/')
        assert resp.status_code == 200
        assert b'Char' in resp.data

    def test_group_list_regular_user_no_active_character(self, test_client, new_user, db):
        """Regular user with no active character is redirected"""
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.get('/groups/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'You need an active character to access groups' in resp.data

    def test_create_group_post(self, test_client, new_user, db):
        """User with active character can create a group"""
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        data = {'name': 'New Group', 'type': 'military'}
        resp = test_client.post('/groups/create', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Group created successfully' in resp.data
        group = Group.query.filter_by(name='New Group').first()
        assert group is not None
        updated_char = Character.query.get(character.id)
        assert updated_char.group_id == group.id

    def test_create_group_post_missing_fields(self, test_client, new_user, db):
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        data = {'name': '', 'type': ''}
        resp = test_client.post('/groups/create', data=data, follow_redirects=True)
        assert b'Name and type are required' in resp.data

    def test_edit_group_post_admin(self, test_client, admin_user, db):
        group = Group(name='Edit Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        data = {'name': 'Edited Group', 'type': 'scientific', 'bank_account': '100'}
        resp = test_client.post(f'/groups/{group.id}/edit', data=data, follow_redirects=True)
        assert b'Group updated successfully' in resp.data
        updated = Group.query.get(group.id)
        assert updated.name == 'Edited Group'
        assert updated.type.value == 'scientific'
        assert updated.bank_account == 100

    def test_edit_group_post_member(self, test_client, new_user, db):
        group = Group(name='Edit Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value, group_id=group.id)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        data = {'name': 'Edited Group'}
        resp = test_client.post(f'/groups/{group.id}/edit', data=data, follow_redirects=True)
        assert b'Group updated successfully' in resp.data
        updated = Group.query.get(group.id)
        assert updated.name == 'Edited Group'

    def test_invite_character(self, test_client, new_user, db):
        group = Group(name='Invite Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value, group_id=group.id)
        db.session.add(character)
        invitee = Character(name='Invitee', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(invitee)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        data = {'character_id': invitee.id}
        resp = test_client.post(f'/groups/{group.id}/invite', data=data, follow_redirects=True)
        assert b'Invite sent successfully' in resp.data
        invite = GroupInvite.query.filter_by(group_id=group.id, character_id=invitee.id).first()
        assert invite is not None

    def test_accept_invite(self, test_client, new_user, db):
        group = Group(name='Accept Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        invite = GroupInvite(group_id=group.id, character_id=character.id)
        db.session.add(invite)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.post(f'/groups/invite/{invite.id}/accept', follow_redirects=True)
        assert b'Joined group successfully' in resp.data
        updated_char = Character.query.get(character.id)
        assert updated_char.group_id == group.id

    def test_decline_invite(self, test_client, new_user, db):
        group = Group(name='Decline Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        invite = GroupInvite(group_id=group.id, character_id=character.id)
        db.session.add(invite)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.post(f'/groups/invite/{invite.id}/decline', follow_redirects=True)
        assert b'Invite declined' in resp.data
        invite = GroupInvite.query.get(invite.id)
        assert invite is None

    def test_leave_group(self, test_client, new_user, db):
        group = Group(name='Leave Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value, group_id=group.id)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.post(f'/groups/{group.id}/leave', follow_redirects=True)
        assert b'You have left the group' in resp.data
        updated_char = Character.query.get(character.id)
        assert updated_char.group_id is None

    def test_disband_group(self, test_client, new_user, db):
        group = Group(name='Disband Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=new_user.id, status=CharacterStatus.ACTIVE.value, group_id=group.id)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = new_user.id
            sess['_fresh'] = True
        resp = test_client.post(f'/groups/{group.id}/disband', follow_redirects=True)
        assert b'Group has been disbanded' in resp.data
        group = Group.query.get(group.id)
        assert group is None

    def test_remove_character_admin(self, test_client, admin_user, db):
        group = Group(name='Remove Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=admin_user.id, status=CharacterStatus.ACTIVE.value, group_id=group.id)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        resp = test_client.post(f'/groups/{group.id}/remove/{character.id}', follow_redirects=True)
        assert b'Character removed from group' in resp.data
        updated_char = Character.query.get(character.id)
        assert updated_char.group_id is None

    def test_create_group_admin(self, test_client, admin_user, db):
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        data = {'name': 'Admin Group', 'type': 'military', 'bank_account': '500'}
        resp = test_client.post('/groups/create/admin', data=data, follow_redirects=True)
        assert b'Group created successfully' in resp.data
        group = Group.query.filter_by(name='Admin Group').first()
        assert group is not None
        assert group.bank_account == 500

    def test_edit_group_admin(self, test_client, admin_user, db):
        group = Group(name='Edit Admin Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        data = {'name': 'Edited Admin Group', 'type': 'scientific', 'bank_account': '200'}
        resp = test_client.post(f'/groups/{group.id}/edit/admin', data=data, follow_redirects=True)
        assert b'Group updated successfully' in resp.data
        updated = Group.query.get(group.id)
        assert updated.name == 'Edited Admin Group'
        assert updated.type.value == 'scientific'
        assert updated.bank_account == 200

    def test_add_character_admin(self, test_client, admin_user, db):
        group = Group(name='AddChar Group', type='military', bank_account=0)
        db.session.add(group)
        db.session.commit()
        character = Character(name='Char', user_id=admin_user.id, status=CharacterStatus.ACTIVE.value)
        db.session.add(character)
        db.session.commit()
        with test_client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        data = {'character_id': character.id}
        resp = test_client.post(f'/groups/{group.id}/add_character/admin', data=data, follow_redirects=True)
        assert b'Character added to group' in resp.data
        updated_char = Character.query.get(character.id)
        assert updated_char.group_id == group.id 
