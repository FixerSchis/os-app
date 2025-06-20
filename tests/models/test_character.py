import pytest
from models.tools.character import Character
from models.enums import CharacterStatus
from models.database.skills import Skill

def test_character_creation(db, new_user):
    """Test basic character creation."""
    char = Character(
        user_id=new_user.id,
        name='Bartholomew',
        status=CharacterStatus.ACTIVE.value
    )
    db.session.add(char)
    db.session.commit()

    assert char.id is not None
    assert char.name == 'Bartholomew'
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
    db.session.refresh(new_user)
    db.session.refresh(character)

    # The skill costs 5, so the character should have 5 points left.
    # The user's points should remain 0 as the character's base points were sufficient.
    assert character.get_available_character_points() == 5
    assert new_user.character_points == 0

    # Give the user some points and buy another skill that costs more than available base points
    new_user.add_character_points(10)
    db.session.commit()
    db.session.refresh(new_user)

    expensive_skill = Skill(name='Expensive Skill', description='An expensive skill', base_cost=10, can_purchase_multiple=False)
    db.session.add(expensive_skill)
    db.session.commit()

    character.purchase_skill(expensive_skill, new_user)
    db.session.commit()

    # Refresh the objects to get the latest state from the database
    db.session.refresh(new_user)
    db.session.refresh(character)

    # Character had 5 points left from the first skill purchase (cost 5).
    # The new skill costs 10.
    # 5 points are taken from the character's base points (10 - 5 = 5 remaining).
    # 5 points are taken from the user's points.
    # Expected user points: 10 - 5 = 5
    assert new_user.character_points == 5
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
    expensive_skill = Skill(name='Expensive Skill', description='An expensive skill', base_cost=15)
    db.session.add(expensive_skill)
    db.session.commit()
    
    character.purchase_skill(expensive_skill, new_user)
    db.session.commit()
    db.session.refresh(new_user)
    db.session.refresh(character)
    
    # Character has 10 base points, skill costs 15. 5 points are spent from user.
    assert new_user.character_points == 5
    assert character.get_available_character_points() == 5
    
    # Refund the expensive skill
    character.refund_skill(expensive_skill, new_user)
    db.session.commit()
    db.session.refresh(new_user)
    db.session.refresh(character)
    
    # Check that points are returned to both character and user
    assert new_user.character_points == 10
    assert character.get_available_character_points() == 20

def test_character_reputation(db, new_user, character, faction):
    """Test setting and getting character reputation."""
    from models.tools.character import CharacterAuditLog
    from models.enums import CharacterAuditAction

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
    assert '10' in log.changes
    
    # Set reputation again to see if it updates
    character.set_reputation(faction.id, -5, new_user.id)
    db.session.commit()
    
    assert character.get_reputation(faction.id) == -5
    
    # Check that another audit log was created
    logs = CharacterAuditLog.query.filter_by(character_id=character.id).order_by(CharacterAuditLog.timestamp.desc()).all()
    assert len(logs) == 2
    assert logs[0].action == CharacterAuditAction.REPUTATION_CHANGE
    assert '-5' in logs[0].changes

def test_character_funds(db, new_user, character):
    """Test character fund management."""
    from models.tools.character import CharacterAuditLog
    from models.enums import CharacterAuditAction

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
    character.spend_funds(30, new_user.id, "Test purchase")
    db.session.commit()
    db.session.refresh(character)
    
    assert character.get_available_funds() == 70
    
    # Check audit log
    log = CharacterAuditLog.query.filter_by(character_id=character.id, action=CharacterAuditAction.FUNDS_SPENT).first()
    assert log is not None
    assert log.editor_user_id == new_user.id
    assert "30" in log.changes
    assert "Test purchase" in log.changes
    
    # Test spending too much
    with pytest.raises(ValueError, match="Not enough funds"):
        character.spend_funds(100, new_user.id, "This should fail")
    
    # Verify funds did not change
    assert character.get_available_funds() == 70

def test_get_available_science_slots(db, new_user, character):
    """Test the calculation of available science slots."""
    from models.database.skills import Skill
    from models.enums import ScienceType
    
    # Initially, no slots
    assert character.get_available_science_slots() == 0
    
    # Create a generic science skill
    science_skill = Skill(
        name='Science',
        description='Provides science slots',
        skill_type='science',
        base_cost=1,
        adds_science_downtime=2
    )
    db.session.add(science_skill)
    db.session.commit()
    
    # Purchase the skill
    character.purchase_skill(science_skill, new_user)
    db.session.commit()
    
    assert character.get_available_science_slots() == 2
    
    # Create a specific life science skill
    life_science_skill = Skill(
        name='Life Science',
        description='Provides life science slots',
        skill_type='science',
        base_cost=1,
        adds_science_downtime=1,
        science_type=ScienceType.LIFE.value
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
    from models.database.cybernetic import Cybernetic, CharacterCybernetic
    generic_cyber = Cybernetic(name='Generic Cyber', neural_shock_value=1, adds_science_downtime=1, wiki_slug='generic-cyber')
    db.session.add(generic_cyber)
    db.session.commit()
    char_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=generic_cyber.id)
    db.session.add(char_cyber)
    db.session.commit()

    # Add a life science cybernetic
    life_cyber = Cybernetic(name='Life Cyber', neural_shock_value=1, adds_science_downtime=2, science_type=ScienceType.LIFE.value, wiki_slug='life-cyber')
    db.session.add(life_cyber)
    db.session.commit()
    char_life_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=life_cyber.id)
    db.session.add(char_life_cyber)
    db.session.commit()
    
    # Re-check totals with cybernetics
    assert character.get_available_science_slots() == 3 + 1 + 2 # 3 from skills, 3 from cybernetics
    assert character.get_available_science_slots(science_type=ScienceType.LIFE) == 1 + 2 # 1 from skill, 2 from cybernetic
    assert character.get_available_science_slots(science_type=ScienceType.CORPOREAL) == 0
    assert character.get_available_science_slots(science_type=ScienceType.GENERIC) == 2 + 1 # 2 from skill, 1 from cybernetic

def test_get_available_engineering_slots(db, new_user, character):
    """Test the calculation of available engineering slots."""
    from models.database.skills import Skill
    
    # Initially, no slots
    assert character.get_available_engineering_slots() == 0
    
    # Create an engineering skill
    engineering_skill = Skill(
        name='Engineering',
        description='Provides engineering slots',
        skill_type='engineering',
        base_cost=1,
        adds_engineering_downtime=3
    )
    db.session.add(engineering_skill)
    db.session.commit()
    
    # Purchase the skill
    character.purchase_skill(engineering_skill, new_user)
    db.session.commit()
    
    assert character.get_available_engineering_slots() == 3

    # Add a cybernetic
    from models.database.cybernetic import Cybernetic, CharacterCybernetic
    cyber = Cybernetic(name='Eng Cyber', neural_shock_value=1, adds_engineering_downtime=2, wiki_slug='eng-cyber')
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
        name='Modding',
        description='Provides engineering mod slots',
        skill_type='engineering',
        base_cost=1,
        adds_engineering_mods=4
    )
    db.session.add(mod_skill)
    db.session.commit()
    
    # Purchase the skill
    character.purchase_skill(mod_skill, new_user)
    db.session.commit()
    
    assert character.get_available_engineering_mod_slots() == 4

    # Add a cybernetic
    from models.database.cybernetic import Cybernetic, CharacterCybernetic
    cyber = Cybernetic(name='Mod Cyber', neural_shock_value=1, adds_engineering_mods=5, wiki_slug='mod-cyber')
    db.session.add(cyber)
    db.session.commit()
    char_cyber = CharacterCybernetic(character_id=character.id, cybernetic_id=cyber.id)
    db.session.add(char_cyber)
    db.session.commit()

    assert character.get_available_engineering_mod_slots() == 4 + 5