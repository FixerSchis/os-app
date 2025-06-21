from models.enums import GroupType
from models.tools.group import Group, GroupInvite


def test_new_group_with_invite(db, character):
    """Test creation of a new Group with an invite."""
    group_name = "Test Group"

    group = Group(name=group_name, type=GroupType.MILITARY, bank_account=1000)

    db.session.add(group)
    db.session.commit()

    # Create an invite
    invite = GroupInvite(group_id=group.id, character_id=character.id)

    db.session.add(invite)
    db.session.commit()

    # Retrieve and assert
    retrieved_group = Group.query.filter_by(name=group_name).first()

    assert retrieved_group is not None
    assert retrieved_group.name == group_name
    assert retrieved_group.type_enum == GroupType.MILITARY
    assert retrieved_group.bank_account == 1000
    assert retrieved_group.id is not None

    # Check invites relationship
    assert len(retrieved_group.invites) == 1
    retrieved_invite = retrieved_group.invites[0]
    assert retrieved_invite.character_id == character.id
    assert retrieved_invite.group_id == group.id
