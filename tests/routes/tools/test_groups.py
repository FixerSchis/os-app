import pytest
from bs4 import BeautifulSoup
from flask import url_for

from models.enums import CharacterStatus, GroupType
from models.tools.character import Character
from models.tools.group import Group, GroupInvite


def test_group_list_admin(test_client, admin_user, db_session):
    """Admin sees all groups"""
    group = Group(name="Test Group", type="military", bank_account=0)
    db_session.add(group)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True
    resp = test_client.get("/groups/")
    assert resp.status_code == 200
    assert b"Test Group" in resp.data


def test_group_list_regular_user_with_active_character(test_client, new_user, db_session):
    """Regular user with active character sees their group list"""
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add(character)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    resp = test_client.get("/groups/")
    assert resp.status_code == 200
    assert b"Char" in resp.data


def test_group_list_no_active_character(test_client, new_user):
    """User with no active character is redirected"""
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    resp = test_client.get("/groups/", follow_redirects=True)
    assert b"You need an active character to access groups" in resp.data


def test_create_group_get(test_client, new_user, db_session):
    """User with active character can access create group page"""
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add(character)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    resp = test_client.get("/groups/new")
    assert resp.status_code == 302


def test_create_group_post(test_client, new_user, db_session):
    """User with active character can create a group"""
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add(character)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"name": "New Group", "type": "military", "character_id": character.id}
    resp = test_client.post("/groups/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    new_group = Group.query.filter_by(name="New Group").first()
    assert new_group is not None
    db_session.refresh(character)
    assert character.group_id == new_group.id


def test_create_group_post_missing_fields(test_client, new_user, db_session):
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add(character)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"name": "", "type": "", "character_id": character.id}
    resp = test_client.post("/groups/new", data=data, follow_redirects=True)
    assert b"Name and type are required" in resp.data


def test_edit_group_post(test_client, new_user, db_session):
    group = Group(name="Original Name", type="military", bank_account=0)
    character = Character(
        name="Char",
        user_id=new_user.id,
        status=CharacterStatus.ACTIVE.value,
    )
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"name": "Updated Name", "type": "scientific", "character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200
    updated_group = db_session.get(Group, group.id)
    assert updated_group.name == "Updated Name"
    # Type is not editable by non-admins, so it should not change
    assert updated_group.type == GroupType.MILITARY


def test_invite_character(test_client, new_user, db_session):
    group = Group(name="Invite Group", type="military", bank_account=0)
    character = Character(
        name="Char",
        user_id=new_user.id,
        status=CharacterStatus.ACTIVE.value,
    )
    invitee = Character(name="Invitee", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character, invitee])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"character_id": invitee.id, "redirect_character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/invite", data=data, follow_redirects=True)
    assert resp.status_code == 200
    invite = GroupInvite.query.filter_by(group_id=group.id, character_id=invitee.id).first()
    assert invite is not None


def test_accept_invite(test_client, new_user, db_session):
    group = Group(name="Accept Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    invite = GroupInvite(group_id=group.id, character_id=character.id)
    db_session.add(invite)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"action": "accept", "character_id": character.id}
    resp = test_client.post(
        f"/groups/invites/{invite.id}/respond", data=data, follow_redirects=True
    )
    assert resp.status_code == 200
    db_session.refresh(character)
    assert character.group_id == group.id


def test_decline_invite(test_client, new_user, db_session):
    group = Group(name="Decline Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    invite = GroupInvite(group_id=group.id, character_id=character.id)
    db_session.add(invite)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"action": "decline", "character_id": character.id}
    resp = test_client.post(
        f"/groups/invites/{invite.id}/respond", data=data, follow_redirects=True
    )
    assert resp.status_code == 200
    declined_invite = db_session.get(GroupInvite, invite.id)
    assert declined_invite is None


def test_leave_group(test_client, new_user, db_session):
    group = Group(name="Leave Group", type="military", bank_account=0)
    character = Character(
        name="Char",
        user_id=new_user.id,
        status=CharacterStatus.ACTIVE.value,
    )
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/leave", data=data, follow_redirects=True)
    assert resp.status_code == 200
    db_session.refresh(character)
    assert character.group_id is None


def test_disband_group(test_client, new_user, db_session):
    group = Group(name="Disband Group", type="military", bank_account=0)
    character = Character(
        name="Char",
        user_id=new_user.id,
        status=CharacterStatus.ACTIVE.value,
    )
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True
    data = {"character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/disband", data=data, follow_redirects=True)
    assert resp.status_code == 200
    disbanded_group = db_session.get(Group, group.id)
    assert disbanded_group is None


def test_remove_character_admin(test_client, admin_user, db_session):
    group = Group(name="Remove Group", type="military", bank_account=0)
    character = Character(
        name="Char",
        user_id=admin_user.id,
        status=CharacterStatus.ACTIVE.value,
    )
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True
    resp = test_client.post(f"/groups/{group.id}/remove/{character.id}", follow_redirects=True)
    assert resp.status_code == 200
    db_session.refresh(character)
    assert character.group_id is None


def test_create_group_admin(test_client, admin_user, db_session):
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True
    data = {"name": "Admin Group", "type": "military", "bank_account": "500"}
    resp = test_client.post("/groups/create/admin", data=data, follow_redirects=True)
    assert b"Group created successfully" in resp.data
    group = Group.query.filter_by(name="Admin Group").first()
    assert group is not None
    assert group.bank_account == 500


def test_edit_group_admin(test_client, admin_user, db_session):
    group = Group(name="Edit Admin Group", type="military", bank_account=0)
    db_session.add(group)
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True
    data = {
        "name": "Edited Admin Group",
        "type": "scientific",
        "bank_account": "200",
    }
    resp = test_client.post(f"/groups/{group.id}/edit/admin", data=data, follow_redirects=True)
    assert b"Group updated successfully" in resp.data
    updated = db_session.get(Group, group.id)
    assert updated.name == "Edited Admin Group"
    assert updated.type.value == "scientific"
    assert updated.bank_account == 200


def test_add_character_admin(test_client, admin_user, db_session):
    group = Group(name="Add Char Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=admin_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True
    data = {"character_id": character.id}
    resp = test_client.post(
        f"/groups/{group.id}/add_character/admin", data=data, follow_redirects=True
    )
    assert resp.status_code == 200
    db_session.refresh(character)
    assert character.group_id == group.id


def test_group_list_for_multi_char_user(test_client, npc_user_with_chars):
    """
    GIVEN a logged-in NPC user with multiple active characters
    WHEN they visit the group page
    THEN they should see a character selection dropdown
    """
    user, char1, char2 = npc_user_with_chars
    with test_client.session_transaction() as sess:
        sess["_user_id"] = user.id
        sess["_fresh"] = True

    response = test_client.get("/groups/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    # Check for the character selection dropdown
    assert soup.find("select", {"id": "character-selector"}) is not None
    assert b"NPC Char 1" in response.data
    assert b"NPC Char 2" in response.data


def test_group_creation_for_multi_char_user(test_client, db_session, npc_user_with_chars):
    """
    GIVEN a logged-in NPC user with multiple active characters
    WHEN they create a new group
    THEN the group should be associated with the selected character
    """
    user, char1, char2 = npc_user_with_chars
    with test_client.session_transaction() as sess:
        sess["_user_id"] = user.id
        sess["_fresh"] = True

    # Create a group with the first character selected
    response = test_client.post(
        "/groups/new",
        data={"name": "Multi-Char Group", "type": "military", "character_id": char1.id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("input", {"value": "Multi-Char Group"}) is not None

    new_group = Group.query.filter_by(name="Multi-Char Group").first()
    assert new_group is not None
    db_session.refresh(char1)
    db_session.refresh(char2)
    assert char1.group_id == new_group.id
    assert char2.group_id is None


def test_admin_group_view_switching(test_client, db_session, admin_user, npc_user_with_chars):
    """Admin can switch between admin and user views"""
    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True

    # Admin view (default)
    resp = test_client.get("/groups/")
    assert resp.status_code == 200
    assert b"Groups - Admin View" in resp.data

    # User view - admin without active characters gets redirected
    resp = test_client.get("/groups/?admin_view=false", follow_redirects=False)
    assert resp.status_code == 302  # Redirect to character list
    assert "characters" in resp.location.lower()


def test_group_audit_log_creation(test_client, new_user, db_session):
    """Test that group creation creates an audit log entry"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add(character)
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"name": "Audit Test Group", "type": "military", "character_id": character.id}
    resp = test_client.post("/groups/new", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Check that group was created
    group = Group.query.filter_by(name="Audit Test Group").first()
    assert group is not None

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.CREATE
    assert audit_log.editor_user_id == new_user.id
    assert "Group created by Char" in audit_log.changes


def test_group_audit_log_edit(test_client, new_user, db_session):
    """Test that group editing creates audit log entries"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Original Name", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"name": "Updated Name", "character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.EDIT
    assert audit_log.editor_user_id == new_user.id
    assert "Name changed from 'Original Name' to 'Updated Name'" in audit_log.changes


def test_group_audit_log_member_join(test_client, new_user, db_session):
    """Test that member joining creates audit log entries"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Join Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()

    invite = GroupInvite(group_id=group.id, character_id=character.id)
    db_session.add(invite)
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"action": "accept", "character_id": character.id}
    resp = test_client.post(
        f"/groups/invites/{invite.id}/respond", data=data, follow_redirects=True
    )
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.MEMBER_ADDED
    assert audit_log.editor_user_id == new_user.id
    assert "Member joined: Char" in audit_log.changes


def test_group_audit_log_member_leave(test_client, new_user, db_session):
    """Test that member leaving creates audit log entries"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Leave Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/leave", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.MEMBER_LEFT
    assert audit_log.editor_user_id == new_user.id
    assert "Member left: Char" in audit_log.changes


def test_group_audit_log_admin_remove(test_client, admin_user, db_session):
    """Test that admin removing member creates audit log entries"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Remove Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=admin_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True

    resp = test_client.post(f"/groups/{group.id}/remove/{character.id}", follow_redirects=True)
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.MEMBER_REMOVED
    assert audit_log.editor_user_id == admin_user.id
    assert "Member removed by admin: Char" in audit_log.changes


def test_group_audit_log_view_access(test_client, new_user, db_session):
    """Test that group audit log is accessible to group members"""
    group = Group(name="Audit Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    resp = test_client.get(f"/groups/{group.id}/audit-log")
    assert resp.status_code == 200
    assert b"Audit Log for Audit Group" in resp.data


def test_group_audit_log_view_access_denied(test_client, new_user, db_session):
    """Test that group audit log is not accessible to non-members"""
    group = Group(name="Audit Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()
    # Note: character is NOT added to the group

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    resp = test_client.get(f"/groups/{group.id}/audit-log")
    assert resp.status_code == 403


def test_group_audit_log_admin_access(test_client, admin_user, db_session):
    """Test that admins can access any group's audit log"""
    group = Group(name="Admin Audit Group", type="military", bank_account=0)
    db_session.add(group)
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = admin_user.id
        sess["_fresh"] = True

    resp = test_client.get(f"/groups/{group.id}/audit-log")
    assert resp.status_code == 200
    assert b"Audit Log for Admin Audit Group" in resp.data


def test_group_audit_log_invite_sent(test_client, new_user, db_session):
    """Test that sending an invite creates an audit log entry"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Invite Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    invitee = Character(name="Invitee", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character, invitee])
    db_session.commit()
    character.group_id = group.id
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"character_id": invitee.id, "redirect_character_id": character.id}
    resp = test_client.post(f"/groups/{group.id}/invite", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.INVITE_SENT
    assert audit_log.editor_user_id == new_user.id
    assert "Invite sent to Invitee" in audit_log.changes


def test_group_audit_log_invite_declined(test_client, new_user, db_session):
    """Test that declining an invite creates an audit log entry"""
    from models.enums import GroupAuditAction
    from models.tools.group import GroupAuditLog

    group = Group(name="Decline Group", type="military", bank_account=0)
    character = Character(name="Char", user_id=new_user.id, status=CharacterStatus.ACTIVE.value)
    db_session.add_all([group, character])
    db_session.commit()

    invite = GroupInvite(group_id=group.id, character_id=character.id)
    db_session.add(invite)
    db_session.commit()

    with test_client.session_transaction() as sess:
        sess["_user_id"] = new_user.id
        sess["_fresh"] = True

    data = {"action": "decline", "character_id": character.id}
    resp = test_client.post(
        f"/groups/invites/{invite.id}/respond", data=data, follow_redirects=True
    )
    assert resp.status_code == 200

    # Check that audit log was created
    audit_log = GroupAuditLog.query.filter_by(group_id=group.id).first()
    assert audit_log is not None
    assert audit_log.action == GroupAuditAction.INVITE_DECLINED
    assert audit_log.editor_user_id == new_user.id
    assert "Invite declined by Char" in audit_log.changes
