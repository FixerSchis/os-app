import pytest
from models.tools.sample import Sample, SampleTag
from models.tools.group import Group
from models.enums import ScienceType, GroupType

def test_new_sample_with_group_and_tags(db):
    """Test creation of a new Sample with Group and SampleTag relationships."""
    # Create a group first
    group = Group(
        name="Test Group",
        type=GroupType.SCIENTIFIC,
        bank_account=500
    )
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
        tags=[tag1, tag2]
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