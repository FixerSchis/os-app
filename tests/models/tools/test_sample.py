from models.database.group_type import GroupType
from models.database.sample import Sample, SampleTag
from models.enums import ScienceType
from models.tools.group import Group


def test_new_sample_with_group_and_tags(db):
    """Test creation of a new Sample with Group and SampleTag relationships."""
    # Create a group type first
    group_type = GroupType(
        name="Scientific",
        description="A scientific group type",
        income_items_list=[],
        income_items_discount=0.5,
        income_substances=True,
        income_substance_cost=5,
        income_medicaments=False,
        income_medicament_cost=0,
        income_distribution_dict={"items": 20, "exotics": 40, "chits": 40},
    )
    db.session.add(group_type)
    db.session.commit()

    # Create a group
    group = Group(name="Test Group", group_type_id=group_type.id, bank_account=500)
    db.session.add(group)
    db.session.commit()

    # Create sample tags
    tag1 = SampleTag(name="Rare")
    tag2 = SampleTag(name="Dangerous")
    db.session.add_all([tag1, tag2])
    db.session.commit()

    # Create the sample
    sample_name = "Test Sample"
    sample = Sample(
        name=sample_name,
        type=ScienceType.LIFE,
        is_researched=False,
        description="A test sample for testing purposes",
        group_id=group.id,
        tags=[tag1, tag2],
    )

    db.session.add(sample)
    db.session.commit()

    # Retrieve and assert
    retrieved_sample = Sample.query.filter_by(name=sample_name).first()

    assert retrieved_sample is not None
    assert retrieved_sample.name == sample_name
    assert retrieved_sample.type == ScienceType.LIFE
    assert retrieved_sample.is_researched is False
    assert retrieved_sample.description == "A test sample for testing purposes"
    assert retrieved_sample.group_id == group.id
    assert retrieved_sample.id is not None

    # Check group relationship
    assert retrieved_sample.group == group

    # Check tags relationship
    assert len(retrieved_sample.tags) == 2
    tag_names = [tag.name for tag in retrieved_sample.tags]
    assert "Rare" in tag_names
    assert "Dangerous" in tag_names
