import pytest
from sqlalchemy.orm import joinedload

from models.database.conditions import Condition, ConditionStage
from models.tools.character import CharacterCondition


class TestConditionProgression:
    """Test condition progression functionality."""

    def test_condition_progression_same_stage(self, db, character):
        """Test condition progression within the same stage."""
        # Create a condition with stages
        condition = Condition(name="Test Condition")
        db.session.add(condition)
        db.session.flush()

        stage1 = ConditionStage(
            condition_id=condition.id,
            stage_number=1,
            rp_effect="You feel dizzy",
            diagnosis="Minor vertigo",
            cure="Rest",
            duration=3,
        )
        db.session.add(stage1)
        db.session.commit()

        # Refresh condition to populate stages
        condition = (
            db.session.query(Condition).options(joinedload(Condition.stages)).get(condition.id)
        )

        # Create character condition
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=1,
            current_duration=3,
        )
        db.session.add(char_condition)
        db.session.commit()

        # Progress the condition
        char_condition.condition = condition  # Attach populated condition
        result = char_condition.progress_condition()
        db.session.flush()

        assert result["progressed"] is True
        assert result["completed"] is False
        assert "has 2 events remaining" in result["message"]

        # Check that duration was reduced
        db.session.refresh(char_condition)
        assert char_condition.current_duration == 2
        assert char_condition.current_stage == 1

    def test_condition_progression_to_next_stage(self, db, character):
        """Test condition progression to the next stage."""
        # Create a condition with multiple stages
        condition = Condition(name="Test Condition")
        db.session.add(condition)
        db.session.flush()

        stage1 = ConditionStage(
            condition_id=condition.id,
            stage_number=1,
            rp_effect="You feel dizzy",
            diagnosis="Minor vertigo",
            cure="Rest",
            duration=1,
        )
        stage2 = ConditionStage(
            condition_id=condition.id,
            stage_number=2,
            rp_effect="Severe dizziness",
            diagnosis="Advanced vertigo",
            cure="Medicine",
            duration=2,
        )
        db.session.add_all([stage1, stage2])
        db.session.commit()

        # Refresh condition to populate stages
        condition = (
            db.session.query(Condition).options(joinedload(Condition.stages)).get(condition.id)
        )

        # Create character condition
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=1,
            current_duration=1,
        )
        db.session.add(char_condition)
        db.session.commit()

        # Progress the condition
        char_condition.condition = condition  # Attach populated condition
        result = char_condition.progress_condition()
        db.session.flush()

        assert result["progressed"] is True
        assert result["completed"] is False
        assert "progressed to stage 2" in result["message"]

        # Check that stage was advanced
        db.session.refresh(char_condition)
        assert char_condition.current_stage == 2
        assert char_condition.current_duration == 2

    def test_condition_progression_to_conclusion(self, db, character):
        """Test condition progression to conclusion."""
        # Create a condition with one stage
        condition = Condition(name="Test Condition")
        db.session.add(condition)
        db.session.flush()

        stage1 = ConditionStage(
            condition_id=condition.id,
            stage_number=1,
            rp_effect="You feel dizzy",
            diagnosis="Minor vertigo",
            cure="Rest",
            duration=1,
        )
        db.session.add(stage1)
        db.session.commit()

        # Refresh condition to populate stages
        condition = (
            db.session.query(Condition).options(joinedload(Condition.stages)).get(condition.id)
        )

        # Create character condition
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=1,
            current_duration=1,
        )
        db.session.add(char_condition)
        db.session.commit()

        # Progress the condition
        char_condition.condition = condition  # Attach populated condition
        result = char_condition.progress_condition()
        db.session.flush()

        assert result["progressed"] is True
        assert result["completed"] is True
        assert "has reached its conclusion" in result["message"]

        # Check that condition is marked as concluded
        db.session.refresh(char_condition)
        assert char_condition.current_stage is None
        assert char_condition.current_duration == 0

    def test_condition_progression_invalid_stage(self, db, character):
        """Test condition progression with invalid stage."""
        # Create a condition
        condition = Condition(name="Test Condition")
        db.session.add(condition)
        db.session.commit()

        # Create character condition with invalid stage
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=999,  # Invalid stage
            current_duration=1,
        )
        db.session.add(char_condition)
        db.session.commit()

        # Progress the condition
        result = char_condition.progress_condition()

        assert result["progressed"] is False
        assert result["completed"] is False
        assert "Invalid stage" in result["message"]

    def test_condition_progression_multiple_stages(self, db, character):
        """Test condition progression through multiple stages."""
        # Create a condition with three stages
        condition = Condition(name="Test Condition")
        db.session.add(condition)
        db.session.flush()

        stage1 = ConditionStage(
            condition_id=condition.id,
            stage_number=1,
            rp_effect="Stage 1 effect",
            diagnosis="Stage 1 diagnosis",
            cure="Stage 1 cure",
            duration=1,
        )
        stage2 = ConditionStage(
            condition_id=condition.id,
            stage_number=2,
            rp_effect="Stage 2 effect",
            diagnosis="Stage 2 diagnosis",
            cure="Stage 2 cure",
            duration=1,
        )
        stage3 = ConditionStage(
            condition_id=condition.id,
            stage_number=3,
            rp_effect="Stage 3 effect",
            diagnosis="Stage 3 diagnosis",
            cure="Stage 3 cure",
            duration=1,
        )
        db.session.add_all([stage1, stage2, stage3])
        db.session.commit()

        # Refresh condition to populate stages
        condition = (
            db.session.query(Condition).options(joinedload(Condition.stages)).get(condition.id)
        )

        # Create character condition
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=1,
            current_duration=1,
        )
        db.session.add(char_condition)
        db.session.commit()

        # Progress through all stages
        char_condition.condition = condition  # Attach populated condition
        # Stage 1 -> Stage 2
        result1 = char_condition.progress_condition()
        db.session.flush()
        assert result1["progressed"] is True
        assert result1["completed"] is False
        assert char_condition.current_stage == 2

        # Stage 2 -> Stage 3
        result2 = char_condition.progress_condition()
        db.session.flush()
        assert result2["progressed"] is True
        assert result2["completed"] is False
        assert char_condition.current_stage == 3

        # Stage 3 -> Conclusion
        result3 = char_condition.progress_condition()
        db.session.flush()
        assert result3["progressed"] is True
        assert result3["completed"] is True
        assert char_condition.current_stage is None
        assert char_condition.current_duration == 0
