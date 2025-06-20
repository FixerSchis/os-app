import pytest
from models.tools.research import Research, ResearchStage, ResearchStageRequirement
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

def test_new_research_with_stages(db, character):
    """Test creation of a new Research project with stages and requirements."""
    # Create the research project
    research = Research(
        project_name="Test Research Project",
        type=ResearchType.INVENTION,
        description="A test research project"
    )
    
    db.session.add(research)
    db.session.commit()
    
    # Create a research stage
    stage = ResearchStage(
        research_id=research.id,
        stage_number=1,
        name="Initial Analysis",
        description="First stage of research"
    )
    
    db.session.add(stage)
    db.session.commit()
    
    # Create a requirement for the stage
    requirement = ResearchStageRequirement(
        stage_id=stage.id,
        requirement_type=ResearchRequirementType.SCIENCE,
        science_type=ScienceType.LIFE,
        amount=5
    )
    
    db.session.add(requirement)
    db.session.commit()
    
    # Retrieve and assert
    retrieved_research = Research.query.filter_by(project_name="Test Research Project").first()
    
    assert retrieved_research is not None
    assert retrieved_research.project_name == "Test Research Project"
    assert retrieved_research.type == ResearchType.INVENTION
    assert retrieved_research.description == "A test research project"
    assert retrieved_research.public_id is not None
    assert retrieved_research.id is not None
    
    # Check stages relationship
    assert len(retrieved_research.stages) == 1
    retrieved_stage = retrieved_research.stages[0]
    assert retrieved_stage.stage_number == 1
    assert retrieved_stage.name == "Initial Analysis"
    
    # Check requirements relationship
    assert len(retrieved_stage.unlock_requirements) == 1
    retrieved_requirement = retrieved_stage.unlock_requirements[0]
    assert retrieved_requirement.requirement_type == ResearchRequirementType.SCIENCE
    assert retrieved_requirement.science_type == ScienceType.LIFE
    assert retrieved_requirement.amount == 5
    
    # Test character assignment
    character_research = retrieved_research.assign_character(character.id)
    db.session.commit()
    
    assert character_research is not None
    assert character_research.character_id == character.id
    assert character_research.research_id == retrieved_research.id
    assert character_research.current_stage_id == retrieved_stage.id
    
    # Test stages_to_json method
    stages_json = retrieved_research.stages_to_json()
    assert len(stages_json) == 1
    stage_data = stages_json[0]
    assert stage_data['stage_number'] == 1
    assert stage_data['name'] == "Initial Analysis"
    assert len(stage_data['unlock_requirements']) == 1
    assert stage_data['unlock_requirements'][0]['requirement_type'] == ResearchRequirementType.SCIENCE.value 
