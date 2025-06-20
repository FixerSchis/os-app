import pytest
from models.database.conditions import Condition, ConditionStage

def test_new_condition_with_stages(db):
    """Test creation of a new Condition with multiple stages."""
    # 1. Create a Condition with two stages
    condition_name = "Test Condition"
    condition = Condition(
        name=condition_name,
        stages=[
            ConditionStage(
                stage_number=1,
                rp_effect="You feel a bit dizzy.",
                diagnosis="Minor Nausea",
                cure="Rest",
                duration=2
            ),
            ConditionStage(
                stage_number=2,
                rp_effect="The world is spinning.",
                diagnosis="Vertigo",
                cure="Medicine",
                duration=4
            )
        ]
    )
    
    db.session.add(condition)
    db.session.commit()
    
    # 2. Retrieve and assert the Condition
    retrieved_condition = Condition.query.filter_by(name=condition_name).first()
    
    assert retrieved_condition is not None
    assert retrieved_condition.name == condition_name
    assert retrieved_condition.id is not None
    
    # 3. Assert the stages
    assert len(retrieved_condition.stages) == 2
    
    # Check stage 1
    stage1 = next((s for s in retrieved_condition.stages if s.stage_number == 1), None)
    assert stage1 is not None
    assert stage1.rp_effect == "You feel a bit dizzy."
    assert stage1.duration == 2
    
    # Check stage 2
    stage2 = next((s for s in retrieved_condition.stages if s.stage_number == 2), None)
    assert stage2 is not None
    assert stage2.diagnosis == "Vertigo"
    assert stage2.cure == "Medicine"
    
    # Check relationship back from stage to condition
    assert stage1.condition == retrieved_condition
    assert stage2.condition == retrieved_condition 
