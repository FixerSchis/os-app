import pytest
from sqlalchemy.orm import joinedload

from models.database.conditions import Condition, ConditionStage
from models.database.rule_tag import RuleTag
from models.database.skills import Skill
from models.database.species import Ability
from models.enums import AbilityType
from models.tools.character import CharacterCondition, CharacterSkill


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

    def _tag(self, db, name):
        tag = RuleTag(name=name)
        db.session.add(tag)
        db.session.flush()
        return tag

    def _condition(self, db, name, duration, tags, next_duration=None):
        condition = Condition(name=name)
        condition.tags = tags
        db.session.add(condition)
        db.session.flush()
        db.session.add(
            ConditionStage(
                condition_id=condition.id,
                stage_number=1,
                rp_effect="Effect",
                diagnosis="Diagnosis",
                cure="Cure",
                duration=duration,
            )
        )
        if next_duration is not None:
            db.session.add(
                ConditionStage(
                    condition_id=condition.id,
                    stage_number=2,
                    rp_effect="Later",
                    diagnosis="Later",
                    cure="Later",
                    duration=next_duration,
                )
            )
        db.session.commit()
        return db.session.query(Condition).options(joinedload(Condition.stages)).get(condition.id)

    def _timing_ability(self, db, character, rate, tags):
        ability = Ability(
            species_id=character.species_id,
            name="Timing",
            description="Timing",
            type=AbilityType.CONDITION_TIMING,
            condition_progress_rate=rate,
        )
        ability.tags = tags
        db.session.add(ability)
        db.session.commit()
        return ability

    def _progress(self, db, character, condition, duration):
        char_condition = CharacterCondition(
            character_id=character.id,
            condition_id=condition.id,
            current_stage=1,
            current_duration=duration,
        )
        db.session.add(char_condition)
        db.session.commit()
        char_condition.condition = condition
        result = char_condition.progress_condition()
        db.session.flush()
        return char_condition, result

    def test_half_time_consumes_two_events(self, db, character):
        toxic = self._tag(db, "toxic")
        self._timing_ability(db, character, 2, [toxic])
        condition = self._condition(db, "Toxic Burn", 4, [toxic])

        char_condition, result = self._progress(db, character, condition, 4)

        assert result["completed"] is False
        assert "has 2 events remaining" in result["message"]
        assert char_condition.current_duration == 2
        assert char_condition.current_stage == 1

    def test_untagged_condition_keeps_the_usual_rate(self, db, character):
        toxic = self._tag(db, "toxic")
        self._timing_ability(db, character, 2, [toxic])
        condition = self._condition(db, "Plain Fever", 4, [])

        char_condition, result = self._progress(db, character, condition, 4)

        assert "has 3 events remaining" in result["message"]
        assert char_condition.current_duration == 3

    def test_quarter_time_finishes_a_matching_stage(self, db, character):
        toxic = self._tag(db, "toxic")
        self._timing_ability(db, character, 4, [toxic])
        condition = self._condition(db, "Hive Toxin", 4, [toxic])

        char_condition, result = self._progress(db, character, condition, 4)

        assert result["completed"] is True
        assert char_condition.current_duration == 0

    def test_next_stage_reloads_the_catalogue_duration(self, db, character):
        toxic = self._tag(db, "toxic")
        self._timing_ability(db, character, 2, [toxic])
        condition = self._condition(db, "Staged Toxin", 2, [toxic], next_duration=6)

        char_condition, result = self._progress(db, character, condition, 2)

        assert "progressed to stage 2" in result["message"]
        assert char_condition.current_stage == 2
        assert char_condition.current_duration == 6

    def test_owned_skill_rate_multiplies_with_the_species(self, db, character):
        toxic = self._tag(db, "toxic")
        self._timing_ability(db, character, 2, [toxic])
        skill = Skill(
            name="Steel Viscera",
            description="Slows a matching condition.",
            base_cost=2,
            can_purchase_multiple=False,
            cost_increases=False,
            condition_progress_rate=0.5,
        )
        skill.condition_tags = [toxic]
        db.session.add(skill)
        db.session.flush()
        db.session.add(
            CharacterSkill(
                character_id=character.id,
                skill_id=skill.id,
                times_purchased=1,
                purchased_by_user_id=character.user_id,
            )
        )
        db.session.commit()
        condition = self._condition(db, "Slowed Toxin", 4, [toxic])

        char_condition, result = self._progress(db, character, condition, 4)

        assert "has 3 events remaining" in result["message"]
        assert char_condition.current_duration == 3

    def _steel_viscera(self, db, character, ranks, tags):
        skill = Skill(
            name="Steel Viscera",
            description="Slows toxins and diseases.",
            base_cost=2,
            can_purchase_multiple=True,
            cost_increases=True,
            condition_progress_rate=0.5,
        )
        skill.condition_tags = tags
        db.session.add(skill)
        db.session.flush()
        db.session.add(
            CharacterSkill(
                character_id=character.id,
                skill_id=skill.id,
                times_purchased=ranks,
                purchased_by_user_id=character.user_id,
            )
        )
        db.session.commit()

    def test_fractional_rate_keeps_a_partial_event(self, db, character):
        disease = self._tag(db, "disease")
        self._steel_viscera(db, character, 1, [disease])
        condition = self._condition(db, "Slow Disease", 2, [disease])

        char_condition, result = self._progress(db, character, condition, 2)

        assert "has 1.5 events remaining" in result["message"]
        assert char_condition.current_duration == pytest.approx(1.5)

    def test_each_steel_viscera_rank_adds_the_stated_time_again(self, db, character):
        disease = self._tag(db, "disease")
        self._steel_viscera(db, character, 2, [disease])
        condition = self._condition(db, "Slower Disease", 1, [disease])

        char_condition, result = self._progress(db, character, condition, 1)

        assert char_condition.current_duration == pytest.approx(2 / 3)
        assert result["completed"] is False

    def test_new_rule_tag_is_found_by_later_lookups(self, db):
        created = RuleTag.resolve_list(["plasma"])
        assert created[0].name == "plasma"
        again = RuleTag.resolve_list(["Plasma"])
        assert again[0].id == created[0].id
        found = RuleTag.query.filter(RuleTag.name.ilike("%plas%")).all()
        assert [tag.name for tag in found] == ["plasma"]
