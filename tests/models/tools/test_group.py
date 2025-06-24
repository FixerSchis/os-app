from models.database.group_type import GroupType
from models.tools.group import Group, GroupInvite


def test_new_group_with_invite(db, character):
    """Test creation of a new Group with an invite."""
    # Create a group type first
    group_type = GroupType(
        name="Military",
        description="A military group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=False,
        income_substance_cost=0,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={"items": 50, "chits": 50},
    )
    db.session.add(group_type)
    db.session.commit()

    group_name = "Test Group"
    group = Group(name=group_name, group_type_id=group_type.id, bank_account=1000)

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
    assert retrieved_group.group_type_id == group_type.id
    assert retrieved_group.group_type.name == "Military"
    assert retrieved_group.bank_account == 1000
    assert retrieved_group.id is not None

    # Check invites relationship
    assert len(retrieved_group.invites) == 1
    retrieved_invite = retrieved_group.invites[0]
    assert retrieved_invite.character_id == character.id
    assert retrieved_invite.group_id == group.id
