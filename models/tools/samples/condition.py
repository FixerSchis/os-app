from datetime import datetime

from models.database.conditions import Condition, ConditionStage


def get_sample_condition():
    condition = Condition(
        id=1,
        name="Radiation Poisoning",
        created_at=datetime(2024, 1, 10, 9, 0, 0),
        updated_at=datetime(2024, 1, 10, 9, 0, 0),
    )
    stage1 = ConditionStage(
        id=1,
        condition=condition,
        stage_number=1,
        rp_effect="Character feels slightly ill and fatigued",
        diagnosis="Minor radiation exposure detected",
        cure="Rest and hydration",
        duration=1,
    )
    stage2 = ConditionStage(
        id=2,
        condition=condition,
        stage_number=2,
        rp_effect="Character experiences nausea and weakness",
        diagnosis="Moderate radiation poisoning",
        cure="Anti-radiation medication required",
        duration=2,
    )
    stage3 = ConditionStage(
        id=3,
        condition=condition,
        stage_number=3,
        rp_effect="Severe illness, risk of death",
        diagnosis="Critical radiation exposure",
        cure="Immediate medical intervention needed",
        duration=3,
    )
    condition.stages = [stage1, stage2, stage3]
    return condition
