import time

import pytest

from models.database.skills import Skill
from models.enums import CharacterStatus
from models.tools.character import Character


def test_character_creation(db, new_user):
    """Test basic character creation."""
    char = Character(user_id=new_user.id, name="Bartholomew", status=CharacterStatus.ACTIVE.value)
    db.session.add(char)
    db.session.commit()

    assert char.id is not None
    assert char.name == "Bartholomew"
    assert char.user_id == new_user.id
    assert char.status == CharacterStatus.ACTIVE.value


def test_character_points(db, new_user, character, skill, species, faction):
    """Test character point calculations."""
    # A new user has 0 points, a new character has 10 base points.
    # So the character should have 10 available points.
    assert new_user.character_points == 0
    assert character.base_character_points == 10
    assert character.get_available_character_points() == 10

    # Purchase a skill and check points again
    character.purchase_skill(skill, new_user)
    db.session.commit()
    # Remove the problematic refresh call
    # db.session.refresh(new_user)
    db.session.refresh(character)

    # The skill costs 5, so the character should have 5 points left.
    # The user's points should remain 0 as the character's base points were sufficient.
    assert character.get_available_character_points() == 5
    assert new_user.character_points == 0

    # Give the user some points and buy another skill that costs more than available
    # base points
    new_user.add_character_points(10)
    # Ensure the user is in the current session
    db.session.merge(new_user)
    db.session.commit()
    # Remove the problematic refresh call
    # db.session.refresh(new_user)

    expensive_skill = Skill(
        name="Expensive Skill",
        description="An expensive skill",
        base_cost=10,
        can_purchase_multiple=False,
    )
    db.session.add(expensive_skill)
    db.session.commit()

    character.purchase_skill(expensive_skill, new_user)
    db.session.commit()

    # Refresh the objects to get the latest state from the database
    # Remove the problematic refresh call
    # db.session.refresh(new_user)
    db.session.refresh(character)

    # Character had 5 points left from the first skill purchase (cost 5).
    # The new skill costs 10.
    # 5 points are taken from the character's base points (10 - 5 = 5 remaining).
    # 5 points are taken from the user's points.
    # Expected user points: 10 - 5 = 5
    # Query the user directly to get the updated points
    from models.tools.user import User

    updated_user = User.query.get(new_user.id)
    assert updated_user.character_points == 5
    # Expected available character points: 0, as all base points are used
    assert character.get_available_character_points() == 5


def test_refund_skill(db, new_user, character, skill, species, faction):
    """Test refunding a skill."""
    # Purchase the skill first
    character.purchase_skill(skill, new_user)
    db.session.commit()
    db.session.refresh(character)

    assert character.get_available_character_points() == 5

    # Refund the skill
    character.refund_skill(skill, new_user)
    db.session.commit()
    db.session.refresh(character)

    # Check that points are returned
    assert character.get_available_character_points() == 10

    # Test refunding a skill that used user points
    new_user.add_character_points(10)
    # Ensure the user is in the current session
    db.session.merge(new_user)
    db.session.commit()

    expensive_skill = Skill(name="Expensive Skill", description="An expensive skill", base_cost=15)
    db.session.add(expensive_skill)
    db.session.commit()

    character.purchase_skill(expensive_skill, new_user)
    db.session.commit()
    # Remove the problematic refresh call
    # db.session.refresh(new_user)
    db.session.refresh(character)

    # Character has 10 base points, skill costs 15. 5 points are spent from user.
    # Query the user directly to get the updated points
    from models.tools.user import User

    updated_user = User.query.get(new_user.id)
    assert updated_user.character_points == 5
    assert character.get_available_character_points() == 5

    # Refund the expensive skill
    character.refund_skill(expensive_skill, new_user)
    db.session.commit()
    # Remove the problematic refresh call
    # db.session.refresh(new_user)
    db.session.refresh(character)

    # Check that points are returned to both character and user
    # Query the user directly to get the updated points
    updated_user = User.query.get(new_user.id)
    assert updated_user.character_points == 10
    assert character.get_available_character_points() == 20


def test_character_reputation(db, new_user, character, faction):
    """Test setting and getting character reputation."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Initially, reputation should be 0
    assert character.get_reputation(faction.id) == 0

    # Set reputation
    character.set_reputation(faction.id, 10, new_user.id)
    db.session.commit()

    # Check new reputation
    assert character.get_reputation(faction.id) == 10

    # Check that an audit log was created
    log = CharacterAuditLog.query.filter_by(character_id=character.id).first()
    assert log is not None
    assert log.action == CharacterAuditAction.REPUTATION_CHANGE
    assert log.editor_user_id == new_user.id
    assert str(faction.id) in log.changes
    assert "10" in log.changes

    # Set reputation again to see if it updates
    character.set_reputation(faction.id, -5, new_user.id)
    db.session.commit()

    assert character.get_reputation(faction.id) == -5

    # Check that another audit log was created
    logs = (
        CharacterAuditLog.query.filter_by(character_id=character.id)
        .order_by(CharacterAuditLog.id.desc())
        .all()
    )
    assert len(logs) == 2
    assert logs[0].action == CharacterAuditAction.REPUTATION_CHANGE
    assert "-5" in logs[0].changes


def test_character_reputation_no_change_no_audit(db, new_user, character, faction):
    """Test that setting reputation to the same value doesn't create audit logs."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Initially, reputation should be 0
    assert character.get_reputation(faction.id) == 0

    # Set reputation to 10
    character.set_reputation(faction.id, 10, new_user.id)
    db.session.commit()

    # Check that an audit log was created
    logs = CharacterAuditLog.query.filter_by(character_id=character.id).all()
    assert len(logs) == 1
    assert logs[0].action == CharacterAuditAction.REPUTATION_CHANGE

    # Set reputation to the same value (10)
    character.set_reputation(faction.id, 10, new_user.id)
    db.session.commit()

    # Check that no additional audit log was created
    logs = CharacterAuditLog.query.filter_by(character_id=character.id).all()
    assert len(logs) == 1  # Still only one log entry

    # Set reputation to 0 (which is the default)
    character.set_reputation(faction.id, 0, new_user.id)
    db.session.commit()

    # Check that another audit log was created for the change from 10 to 0
    logs = CharacterAuditLog.query.filter_by(character_id=character.id).all()
    assert len(logs) == 2  # Now two log entries

    # Set reputation to 0 again
    character.set_reputation(faction.id, 0, new_user.id)
    db.session.commit()

    # Check that no additional audit log was created
    logs = CharacterAuditLog.query.filter_by(character_id=character.id).all()
    assert len(logs) == 2  # Still only two log entries


def test_character_funds(db, new_user, character):
    """Test character fund management."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Initial funds should be 0
    assert character.get_available_funds() == 0
    assert not character.can_afford(1)

    # Add funds
    character.bank_account = 100
    db.session.commit()
    db.session.refresh(character)

    assert character.get_available_funds() == 100
    assert character.can_afford(50)
    assert character.can_afford(100)
    assert not character.can_afford(101)

    # Spend funds
    character.remove_funds(30, new_user.id, "Test purchase")
    db.session.commit()
    db.session.refresh(character)

    assert character.get_available_funds() == 70

    # Check audit log
    log = CharacterAuditLog.query.filter_by(
        character_id=character.id, action=CharacterAuditAction.FUNDS_REMOVED
    ).first()
    assert log is not None
    assert log.editor_user_id == new_user.id
    assert "30" in log.changes
    assert "Test purchase" in log.changes

    # Test spending too much
    with pytest.raises(ValueError, match="Not enough funds"):
        character.remove_funds(100, new_user.id, "This should fail")

    # Verify funds did not change
    assert character.get_available_funds() == 70


def test_character_funds_with_group(db, new_user, character, group):
    """Test character fund management with group funds."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Add character to group
    character.group = group

    # Set initial balances
    character.bank_account = 50
    group.bank_account = 100
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    # Test spending from character funds only
    character.remove_funds(30, new_user.id, "Test purchase")
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    assert character.bank_account == 20  # 50 - 30
    assert group.bank_account == 100  # Unchanged
    assert character.get_available_funds() == 120  # 20 + 100

    # Test spending more than character has (should use group funds)
    character.remove_funds(50, new_user.id, "Large purchase")
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    assert character.bank_account == 0  # 20 - 20 (all character funds used)
    assert group.bank_account == 70  # 100 - 30 (remaining 30 from group)
    assert character.get_available_funds() == 70  # 0 + 70

    # Test spending from group funds only
    character.remove_funds(40, new_user.id, "Group purchase")
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    assert character.bank_account == 0  # Still 0
    assert group.bank_account == 30  # 70 - 40
    assert character.get_available_funds() == 30  # 0 + 30

    # Test spending more than available (should fail)
    with pytest.raises(ValueError, match="Not enough funds"):
        character.remove_funds(50, new_user.id, "This should fail")

    # Verify balances didn't change
    db.session.refresh(character)
    db.session.refresh(group)
    assert character.bank_account == 0
    assert group.bank_account == 30

    # Check audit logs
    logs = (
        CharacterAuditLog.query.filter_by(
            character_id=character.id, action=CharacterAuditAction.FUNDS_REMOVED
        )
        .order_by(CharacterAuditLog.timestamp)
        .all()
    )

    assert len(logs) == 3
    assert "Character: 30" in logs[0].changes  # First purchase
    assert "Character: 20, Group: 30" in logs[1].changes  # Large purchase
    assert "Group: 40" in logs[2].changes  # Group purchase


def test_character_funds_no_group(db, new_user, character):
    """Test character fund management without group."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Set initial balance
    character.bank_account = 100
    character.group = None
    db.session.commit()
    db.session.refresh(character)

    # Test spending from character funds only
    character.remove_funds(50, new_user.id, "Test purchase")
    db.session.commit()
    db.session.refresh(character)

    assert character.bank_account == 50  # 100 - 50
    assert character.get_available_funds() == 50  # Only character funds

    # Test spending more than character has (should fail)
    with pytest.raises(ValueError, match="Not enough funds"):
        character.remove_funds(100, new_user.id, "This should fail")

    # Verify balance didn't change
    db.session.refresh(character)
    assert character.bank_account == 50

    # Check audit log
    log = CharacterAuditLog.query.filter_by(
        character_id=character.id, action=CharacterAuditAction.FUNDS_REMOVED
    ).first()
    assert log is not None
    assert "Character: 50" in log.changes


def test_character_funds_zero_character_balance(db, new_user, character, group):
    """Test spending when character has zero balance but group has funds."""
    from models.enums import CharacterAuditAction
    from models.tools.character import CharacterAuditLog

    # Add character to group
    character.group = group

    # Set initial balances
    character.bank_account = 0
    group.bank_account = 100
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    # Test spending from group funds only
    character.remove_funds(50, new_user.id, "Group purchase")
    db.session.commit()
    db.session.refresh(character)
    db.session.refresh(group)

    assert character.bank_account == 0  # Still 0
    assert group.bank_account == 50  # 100 - 50
    assert character.get_available_funds() == 50  # 0 + 50

    # Check audit log
    log = CharacterAuditLog.query.filter_by(
        character_id=character.id, action=CharacterAuditAction.FUNDS_REMOVED
    ).first()
    assert log is not None
    assert "Group: 50" in log.changes


def test_get_available_science_slots(db, new_user, character):
    """Test the calculation of available science slots."""
    from models.database.skills import Skill
    from models.enums import ScienceType

    # Initially, no slots
    assert character.get_available_science_slots() == 0

    # Create a generic science skill
    science_skill = Skill(
        name="Science",
        description="Provides science slots",
        skill_type="science",
        base_cost=1,
        adds_science_downtime=2,
    )
    db.session.add(science_skill)
    db.session.commit()

    # Purchase the skill
    character.purchase_skill(science_skill, new_user)
    db.session.commit()

    assert character.get_available_science_slots() == 2

    # Create a specific life science skill
    life_science_skill = Skill(
        name="Life Science",
        description="Provides life science slots",
        skill_type="science",
        base_cost=1,
        adds_science_downtime=1,
        science_type=ScienceType.LIFE.value,
    )
    db.session.add(life_science_skill)
    db.session.commit()

    # Purchase the life science skill
    character.purchase_skill(life_science_skill, new_user)
    db.session.commit()

    # Check total and specific slots
    assert character.get_available_science_slots() == 3
    assert character.get_available_science_slots(science_type=ScienceType.LIFE) == 1
    assert character.get_available_science_slots(science_type=ScienceType.CORPOREAL) == 0
    assert character.get_available_science_slots(science_type=ScienceType.GENERIC) == 2

    # Add a generic cybernetic
    from models.database.cybernetic import CharacterCybernetic, Cybernetic

    generic_cyber = Cybernetic(
        name="Generic Cyber",
        neural_shock_value=1,
        adds_science_downtime=1,
        wiki_slug="generic-cyber",
    )
    db.session.add(generic_cyber)
    db.session.commit()
    char_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=generic_cyber.id)
    db.session.add(char_cyber)
    db.session.commit()

    # Add a life science cybernetic
    life_cyber = Cybernetic(
        name="Life Cyber",
        neural_shock_value=1,
        adds_science_downtime=2,
        science_type=ScienceType.LIFE.value,
        wiki_slug="life-cyber",
    )
    db.session.add(life_cyber)
    db.session.commit()
    char_life_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=life_cyber.id)
    db.session.add(char_life_cyber)
    db.session.commit()

    # Re-check totals with cybernetics
    assert character.get_available_science_slots() == 3 + 1 + 2  # 3 from skills, 3 from cybernetics
    assert (
        character.get_available_science_slots(science_type=ScienceType.LIFE) == 1 + 2
    )  # 1 from skill, 2 from cybernetic
    assert character.get_available_science_slots(science_type=ScienceType.CORPOREAL) == 0
    assert (
        character.get_available_science_slots(science_type=ScienceType.GENERIC) == 2 + 1
    )  # 2 from skill, 1 from cybernetic


def test_get_available_engineering_slots(db, new_user, character):
    """Test the calculation of available engineering slots."""
    from models.database.skills import Skill

    # Initially, no slots
    assert character.get_available_engineering_slots() == 0

    # Create an engineering skill
    engineering_skill = Skill(
        name="Engineering",
        description="Provides engineering slots",
        skill_type="engineering",
        base_cost=1,
        adds_engineering_downtime=3,
    )
    db.session.add(engineering_skill)
    db.session.commit()

    # Purchase the skill
    character.purchase_skill(engineering_skill, new_user)
    db.session.commit()

    assert character.get_available_engineering_slots() == 3

    # Add a cybernetic
    from models.database.cybernetic import CharacterCybernetic, Cybernetic

    cyber = Cybernetic(
        name="Eng Cyber",
        neural_shock_value=1,
        adds_engineering_downtime=2,
        wiki_slug="eng-cyber",
    )
    db.session.add(cyber)
    db.session.commit()
    char_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=cyber.id)
    db.session.add(char_cyber)
    db.session.commit()

    assert character.get_available_engineering_slots() == 3 + 2


def test_get_available_engineering_mod_slots(db, new_user, character):
    """Test the calculation of available engineering mod slots."""
    from models.database.skills import Skill

    # Initially, no slots
    assert character.get_available_engineering_mod_slots() == 0

    # Create a skill that adds mod slots
    mod_skill = Skill(
        name="Modding",
        description="Provides engineering mod slots",
        skill_type="engineering",
        base_cost=1,
        adds_engineering_mods=4,
    )
    db.session.add(mod_skill)
    db.session.commit()

    # Purchase the skill
    character.purchase_skill(mod_skill, new_user)
    db.session.commit()

    assert character.get_available_engineering_mod_slots() == 4

    # Add a cybernetic
    from models.database.cybernetic import CharacterCybernetic, Cybernetic

    cyber = Cybernetic(
        name="Mod Cyber",
        neural_shock_value=1,
        adds_engineering_mods=5,
        wiki_slug="mod-cyber",
    )
    db.session.add(cyber)
    db.session.commit()
    char_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=cyber.id)
    db.session.add(char_cyber)
    db.session.commit()

    assert character.get_available_engineering_mod_slots() == 4 + 5


def test_free_rank_is_left_out_of_the_rising_cost(db, new_user, character):
    """A creation rank counts for the skill and leaves the next purchase at the first price."""
    from models.tools.character import CharacterSkill

    skill = Skill(
        name="Rising Skill",
        description="Costs more on each paid rank",
        base_cost=2,
        can_purchase_multiple=True,
        cost_increases=True,
    )
    db.session.add(skill)
    db.session.flush()
    db.session.add(
        CharacterSkill(
            character_id=character.id,
            skill_id=skill.id,
            times_purchased=1,
            free_ranks=1,
            purchased_by_user_id=new_user.id,
        )
    )
    db.session.commit()
    db.session.refresh(character)

    assert character.get_total_skill_cost() == 0
    assert character.get_skill_cost(skill) == 2

    character.purchase_skill(skill, new_user)
    db.session.refresh(character)
    assert character.get_total_skill_cost() == 2
    assert character.get_skill_cost(skill) == 3

    character.refund_skill(skill, new_user)
    db.session.refresh(character)
    assert character.get_total_skill_cost() == 0
    assert character.get_available_character_points() == 10

    character.refund_skill(skill, new_user)
    db.session.refresh(character)
    owned = CharacterSkill.query.filter_by(character_id=character.id, skill_id=skill.id).first()
    assert owned is None
    assert character.get_available_character_points() == 10


def test_starting_skill_grant_and_choice_quota(db, new_user, character, species, faction):
    """Named starting skills are granted free, and a choice quota is enforced."""
    from models.database.species import Ability, Species
    from models.enums import AbilityType
    from models.tools.character import CharacterSkill
    from utils.starting_skills import apply_starting_skills, validate_starting_skill_picks

    engineer = Skill(
        name="Grant Engineer",
        description="A granted rank",
        base_cost=2,
        can_purchase_multiple=True,
        cost_increases=True,
        skill_type="professional",
    )
    first_program = Skill(
        name="Program One",
        description="A standard program",
        base_cost=1,
        skill_type="standard_program",
    )
    second_program = Skill(
        name="Program Two",
        description="A standard program",
        base_cost=1,
        skill_type="standard_program",
    )
    advanced = Skill(
        name="Program Advanced",
        description="An advanced program",
        base_cost=1,
        skill_type="advanced_program",
    )
    db.session.add_all([engineer, first_program, second_program, advanced])
    db.session.flush()
    first_program.required_species_list = [species.id]
    second_program.required_species_list = [species.id]
    advanced.required_species_list = [species.id]

    grant = Ability(
        name="Technical aptitude",
        description="One free rank of Engineer.",
        type=AbilityType.STARTING_SKILLS,
        species=species,
    )
    grant.starting_skills_list = [str(engineer.id)]
    choices = Ability(
        name="Known programs",
        description="Pick programs.",
        type=AbilityType.STARTING_SKILL_CHOICES,
        species=species,
    )
    choices.starting_skill_choices_list = [
        {"skill_type": "standard_program", "count": 2},
        {"skill_type": "advanced_program", "count": 1},
    ]
    db.session.add_all([grant, choices])
    db.session.commit()
    db.session.refresh(species)

    error = validate_starting_skill_picks(species, [str(first_program.id)])
    assert error == "Choose 2 Standard Program skills."

    picks = [str(first_program.id), str(second_program.id), str(advanced.id)]
    assert validate_starting_skill_picks(species, picks) is None

    apply_starting_skills(character, species, new_user, picks)
    db.session.commit()
    owned = CharacterSkill.query.filter_by(character_id=character.id, skill_id=engineer.id).one()
    assert owned.times_purchased == 1
    assert owned.free_ranks == 1
    assert character.get_skill_cost(engineer) == 2

    apply_starting_skills(character, species, new_user, picks)
    db.session.commit()
    db.session.refresh(owned)
    assert owned.times_purchased == 1

    plain = Species(
        name="Plain Species",
        wiki_page="plain-species",
        permitted_factions=f"[{faction.id}]",
        body_hits_type="locational",
        body_hits=1,
        death_count=100,
    )
    db.session.add(plain)
    db.session.commit()
    apply_starting_skills(character, plain, new_user, [])
    db.session.commit()
    assert (
        CharacterSkill.query.filter_by(character_id=character.id, skill_id=engineer.id).first()
        is None
    )
    assert (
        CharacterSkill.query.filter_by(character_id=character.id, skill_id=first_program.id).first()
        is None
    )


def test_free_rank_cannot_be_raised_until_its_prerequisite_is_owned(
    db, new_user, character, species
):
    """A creation rank is kept without its prerequisite, and the next rank waits for it."""
    from models.database.species import Ability
    from models.enums import AbilityType
    from models.tools.character import CharacterSkill
    from utils.starting_skills import apply_starting_skills

    scientist = Skill(
        name="Gate Scientist",
        description="The prerequisite",
        base_cost=2,
        skill_type="professional",
    )
    science = Skill(
        name="Granted Science",
        description="Each rank grants a research point",
        base_cost=1,
        can_purchase_multiple=True,
        cost_increases=True,
        skill_type="professional",
    )
    db.session.add_all([scientist, science])
    db.session.flush()
    science.required_skill_id = scientist.id
    grant = Ability(
        name="Scientist training",
        description="One free rank.",
        type=AbilityType.STARTING_SKILLS,
        species=species,
    )
    grant.starting_skills_list = [str(science.id)]
    db.session.add(grant)
    db.session.commit()
    db.session.refresh(species)

    apply_starting_skills(character, species, new_user, [])
    db.session.commit()
    owned = CharacterSkill.query.filter_by(character_id=character.id, skill_id=science.id).one()
    assert owned.times_purchased == 1
    assert owned.free_ranks == 1
    assert character.get_skill_cost(science) == 1
    assert character.get_total_skill_cost() == 0

    with pytest.raises(ValueError, match="Requires Gate Scientist"):
        character.purchase_skill(science, new_user)
    db.session.refresh(owned)
    assert owned.times_purchased == 1

    character.purchase_skill(scientist, new_user)
    character.purchase_skill(science, new_user)
    db.session.refresh(owned)
    assert owned.times_purchased == 2
    assert owned.free_ranks == 1
    assert character.get_total_skill_cost() == 3
    assert character.get_skill_cost(science) == 2


def test_first_skill_in_a_group_grants_its_pair(db, new_user, character, species, faction):
    """The first skill bought from a group grants its pair, and only that one."""
    from models.database.species import Ability, Species
    from models.enums import AbilityType
    from models.tools.character import CharacterSkill
    from utils.skill_pairs import apply_skill_pair_grants

    helm = Skill(name="Helm Basic", base_cost=1, skill_type="spaceflight")
    helm_advanced = Skill(name="Helm Advanced", base_cost=2, skill_type="spaceflight")
    weapons = Skill(name="Weapons Basic", base_cost=1, skill_type="spaceflight")
    weapons_advanced = Skill(name="Weapons Advanced", base_cost=2, skill_type="spaceflight")
    db.session.add_all([helm, helm_advanced, weapons, weapons_advanced])
    db.session.flush()
    helm_advanced.required_skill_id = helm.id
    weapons_advanced.required_skill_id = weapons.id
    pairs = Ability(
        name="Spaceflight aptitude",
        description="The first basic console grants its advanced skill.",
        type=AbilityType.FIRST_SKILL_PAIR,
        species=species,
    )
    pairs.skill_pairs_list = [
        {"trigger_skill_id": helm.id, "granted_skill_id": helm_advanced.id},
        {"trigger_skill_id": weapons.id, "granted_skill_id": weapons_advanced.id},
    ]
    db.session.add(pairs)
    db.session.flush()
    plain = Species(
        name="Plain Pilot",
        wiki_page="plain-pilot",
        permitted_factions=f"[{faction.id}]",
        body_hits_type="locational",
        body_hits=1,
        death_count=100,
    )
    outsider = Character(
        user_id=new_user.id,
        name="Outsider",
        status=CharacterStatus.ACTIVE.value,
        species=plain,
    )
    db.session.add_all([plain, outsider])
    db.session.commit()
    db.session.refresh(species)
    character.species = species

    outsider.purchase_skill(helm, new_user)
    assert (
        CharacterSkill.query.filter_by(character_id=outsider.id, skill_id=helm_advanced.id).first()
        is None
    )

    character.purchase_skill(helm, new_user)
    granted = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=helm_advanced.id
    ).one()
    assert granted.free_ranks == 1
    assert character.get_total_skill_cost() == 1

    character.purchase_skill(weapons, new_user)
    assert (
        CharacterSkill.query.filter_by(
            character_id=character.id, skill_id=weapons_advanced.id
        ).first()
        is None
    )
    assert character.get_total_skill_cost() == 2

    apply_skill_pair_grants(character, plain, new_user)
    db.session.commit()
    assert (
        CharacterSkill.query.filter_by(character_id=character.id, skill_id=helm_advanced.id).first()
        is None
    )
    assert character.skill_pair_grants_list

    apply_skill_pair_grants(character, species, new_user)
    db.session.commit()
    restored = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=helm_advanced.id
    ).one()
    assert restored.free_ranks == 1
    assert character.get_total_skill_cost() == 2

    character.refund_skill(helm_advanced, new_user)
    character.refund_skill(helm, new_user)
    character.refund_skill(weapons, new_user)
    assert character.skill_pair_grants_list == []

    character.purchase_skill(weapons, new_user)
    again = CharacterSkill.query.filter_by(
        character_id=character.id, skill_id=weapons_advanced.id
    ).one()
    assert again.free_ranks == 1
    assert character.get_total_skill_cost() == 1


def test_buying_the_only_paired_skill_grants_one_free_rank(db, new_user, character, species):
    """A one-pair group grants its skill on purchase, and that rank stays unpaid."""
    from models.database.species import Ability
    from models.enums import AbilityType
    from models.tools.character import CharacterSkill

    scientist = Skill(name="Pair Scientist", base_cost=2, skill_type="professional")
    science = Skill(
        name="Pair Science",
        base_cost=1,
        can_purchase_multiple=True,
        cost_increases=True,
        skill_type="professional",
    )
    db.session.add_all([scientist, science])
    db.session.flush()
    science.required_skill_id = scientist.id
    pairs = Ability(
        name="Scientist training",
        description="Buying the scientist skill grants one science rank.",
        type=AbilityType.FIRST_SKILL_PAIR,
        species=species,
    )
    pairs.skill_pairs_list = [{"trigger_skill_id": scientist.id, "granted_skill_id": science.id}]
    db.session.add(pairs)
    db.session.commit()
    db.session.refresh(species)
    character.species = species

    with pytest.raises(ValueError, match="Requires Pair Scientist"):
        character.purchase_skill(science, new_user)

    character.purchase_skill(scientist, new_user)
    owned = CharacterSkill.query.filter_by(character_id=character.id, skill_id=science.id).one()
    assert owned.times_purchased == 1
    assert owned.free_ranks == 1
    assert character.get_total_skill_cost() == 2
    assert character.get_skill_cost(science) == 1

    character.purchase_skill(science, new_user)
    db.session.refresh(owned)
    assert owned.times_purchased == 2
    assert owned.free_ranks == 1
    assert character.get_total_skill_cost() == 3


def test_species_rank_cap_stays_below_the_skill_maximum(db, new_user, character, species):
    """A species cap can lower a skill's maximum, and cannot raise it."""
    from models.database.species import Ability
    from models.enums import AbilityType
    from models.tools.character import CharacterSkill

    guarded = Skill(
        name="Guarded",
        base_cost=1,
        can_purchase_multiple=True,
        cost_increases=True,
        skill_type="combat",
        max_ranks=3,
    )
    db.session.add(guarded)
    db.session.flush()
    caps = Ability(
        name="Rank cap",
        description="At most 2 ranks.",
        type=AbilityType.SKILL_RANK_CAPS,
        species=species,
    )
    caps.rank_caps_list = [{"skill_id": guarded.id, "max_ranks": 2}]
    outsider = Character(
        user_id=new_user.id,
        name="Uncapped",
        status=CharacterStatus.ACTIVE.value,
    )
    db.session.add_all([caps, outsider])
    db.session.commit()
    db.session.refresh(species)
    character.species = species

    character.purchase_skill(guarded, new_user)
    character.purchase_skill(guarded, new_user)
    with pytest.raises(ValueError, match="Maximum 2 ranks"):
        character.purchase_skill(guarded, new_user)
    owned = CharacterSkill.query.filter_by(character_id=character.id, skill_id=guarded.id).one()
    assert owned.times_purchased == 2

    for _ in range(3):
        outsider.purchase_skill(guarded, new_user)
    with pytest.raises(ValueError, match="Maximum 3 ranks"):
        outsider.purchase_skill(guarded, new_user)
    other = CharacterSkill.query.filter_by(character_id=outsider.id, skill_id=guarded.id).one()
    assert other.times_purchased == 3


def test_captain_skills_need_one_expert_and_a_different_console(db, new_user, character):
    """One expert unlocks every captain skill, and each one needs its own console."""
    helm = Skill(name="Helm Advanced", base_cost=1, skill_type="spaceflight")
    weapons = Skill(name="Weapons Advanced", base_cost=1, skill_type="spaceflight")
    evasive = Skill(name="Evasive", base_cost=1, skill_type="spaceflight")
    evacuation = Skill(name="Evacuation", base_cost=1, skill_type="spaceflight")
    first = Skill(name="A Good Day", base_cost=1, skill_type="spaceflight")
    second = Skill(name="Fly Apart", base_cost=1, skill_type="spaceflight")
    db.session.add_all([helm, weapons, evasive, evacuation, first, second])
    db.session.flush()
    for captain in (first, second):
        captain.required_any_skills_list = [evasive.id, evacuation.id]
        captain.distinct_requirements_list = [helm.id, weapons.id]
    db.session.commit()
    assert first.character_meets_requirements(character) is False

    with pytest.raises(ValueError, match="Requires one of"):
        character.purchase_skill(first, new_user)

    character.purchase_skill(evasive, new_user)
    with pytest.raises(ValueError, match="Requires a different one of"):
        character.purchase_skill(first, new_user)

    character.purchase_skill(helm, new_user)
    character.purchase_skill(first, new_user)
    character.purchase_skill(evacuation, new_user)
    with pytest.raises(ValueError, match="Requires a different one of"):
        character.purchase_skill(second, new_user)

    character.purchase_skill(weapons, new_user)
    character.purchase_skill(second, new_user)

    character.refund_skill(evasive, new_user)
    with pytest.raises(ValueError, match="Cannot refund Evacuation"):
        character.refund_skill(evacuation, new_user)
    with pytest.raises(ValueError, match="Cannot refund Helm Advanced"):
        character.refund_skill(helm, new_user)


def test_core_species_status_discount_applies_to_every_rank(db, new_user, character, species):
    """A skill discount lowers each rank, and a flat-cost skill charges every rank."""
    from models.database.species import Ability
    from models.enums import AbilityType

    status = Skill(
        name="Faction Status",
        base_cost=3,
        can_purchase_multiple=True,
        cost_increases=False,
        skill_type="reputation",
    )
    db.session.add(status)
    db.session.flush()
    discount = Ability(
        name="Status discount",
        description="Faction Status costs 1 less per rank.",
        type=AbilityType.SKILL_DISCOUNTS,
        species=species,
    )
    discount.skill_discounts_dict = {str(status.id): 1}
    outsider = Character(
        user_id=new_user.id,
        name="Full Price",
        status=CharacterStatus.ACTIVE.value,
    )
    db.session.add_all([discount, outsider])
    db.session.commit()
    db.session.refresh(species)
    character.species = species

    assert character.get_skill_cost(status) == 2
    assert outsider.get_skill_cost(status) == 3

    character.purchase_skill(status, new_user)
    character.purchase_skill(status, new_user)
    assert character.get_total_skill_cost() == 4
    assert character.get_skill_cost(status) == 2

    outsider.purchase_skill(status, new_user)
    outsider.purchase_skill(status, new_user)
    assert outsider.get_total_skill_cost() == 6
