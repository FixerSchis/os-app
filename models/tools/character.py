from sqlalchemy import JSON, event

from models.database.faction import Faction
from models.database.mods import Mod
from models.tools.user import User
from models.extensions import db
from models.enums import CharacterStatus, CharacterAuditAction, ScienceType
from models.database.species import Species
from datetime import datetime
from models.database.cybernetic import CharacterCybernetic, Cybernetic

# Association table for many-to-many relationship between Character and CharacterTag
character_tags = db.Table('character_tags',
    db.Column('character_id', db.Integer, db.ForeignKey('character.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('character_tag.id'), primary_key=True)
)

class CharacterTag(db.Model):
    __tablename__ = 'character_tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationship to characters through the association table
    characters = db.relationship('Character', secondary=character_tags, backref=db.backref('tags', lazy='dynamic'))

    def __repr__(self):
        return f'<CharacterTag {self.name}>'

class CharacterSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    times_purchased = db.Column(db.Integer, nullable=False, default=1)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    purchased_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    character = db.relationship('Character', back_populates='skills')
    skill = db.relationship('Skill')
    purchased_by = db.relationship('User')

    def __repr__(self):
        return f'<CharacterSkill {self.skill.name} (x{self.times_purchased})>'

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    character_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    pronouns_subject = db.Column(db.String(20), nullable=True)
    pronouns_object = db.Column(db.String(20), nullable=True)
    faction_id = db.Column(db.Integer, db.ForeignKey('faction.id'), nullable=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=CharacterStatus.ACTIVE)
    base_character_points = db.Column(db.Integer, nullable=False, default=10)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    bank_account = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    character_pack = db.Column(JSON, default=dict)
    
    # Downtime-related fields
    known_modifications = db.Column(db.JSON, default=list)  # List of mod IDs

    # Relationships will be set up after all models are defined
    user = None
    faction = None
    species = None
    skills = None
    audit_logs = None
    reputations = None
    active_conditions = None
    group = None
    cybernetics_link = None
    downtime_packs = None
    event_tickets = None


    @classmethod
    def get_by_player_reference(cls, player_reference):
        if '.' in player_reference:
            player_id, char_id = player_reference.split('.')
            return cls.get_by_player_id_and_char_id(player_id, char_id)
        else:
            return None

    @classmethod
    def get_by_player_id_and_char_id(cls, player_id, char_id):
        return cls.query.filter_by(user_id=player_id, character_id=char_id).first()

    @property
    def player_id(self):
        return self.user.player_id if self.user else None

    def __repr__(self):
        return f'<Character {self.name}>'

    def get_total_skill_cost(self):
        """Calculate the total cost of all skills for this character."""
        total_cost = 0
        for character_skill in self.skills:
            skill = character_skill.skill
            if skill.cost_increases:
                # For a skill with increasing cost, the cost of the nth purchase is base_cost + (n-1)
                # We sum the cost for each purchase from 1 to times_purchased
                for i in range(character_skill.times_purchased):
                    purchase_cost = skill.base_cost + i
                    # Apply species discounts
                    for ability in self.species.abilities:
                        if ability.type == 'skill_discounts' and str(skill.id) in ability.skill_discounts_dict:
                            discount = ability.skill_discounts_dict[str(skill.id)]
                            purchase_cost = max(0, purchase_cost - discount)
                    total_cost += purchase_cost
            else:
                purchase_cost = skill.base_cost
                # Apply species discounts
                for ability in self.species.abilities:
                    if ability.type == 'skill_discounts' and str(skill.id) in ability.skill_discounts_dict:
                        discount = ability.skill_discounts_dict[str(skill.id)]
                        purchase_cost = max(0, purchase_cost - discount)
                total_cost += purchase_cost * character_skill.times_purchased
        return total_cost

    def get_faction_name(self):
        return self.faction.name if self.faction else None

    def get_faction_slug(self):
        return self.faction.wiki_slug if self.faction else None

    @property
    def status_enum(self):
        return CharacterStatus(self.status)

    @status_enum.setter
    def status_enum(self, status):
        if isinstance(status, CharacterStatus):
            self.status = status.value
        else:
            self.status = status

    def get_skill_cost(self, skill, is_refund=False):
        """Calculate the cost of a skill, taking into account previous purchases and species discounts."""
        # Get the number of times this skill has been purchased
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id,
            skill_id=skill.id
        ).first()
        
        # If the skill hasn't been purchased yet, start at 0
        count = 0 if character_skill is None else character_skill.times_purchased
        
        # Calculate the base cost based on the skill's properties
        base_cost = skill.base_cost
        if skill.cost_increases:
            # For refunds, we calculate the cost of the rank being refunded,
            # which is the cost of the Nth purchase where N is the current count.
            # For a new purchase, we calculate the cost of the (N+1)th purchase.
            if is_refund:
                if count > 0:
                    base_cost += (count - 1) # Cost of the Nth purchase
            else:
                base_cost += count # Cost of the (N+1)th purchase
        
        # Apply species discounts if any
        for ability in self.species.abilities:
            if ability.type == 'skill_discounts':
                if str(skill.id) in ability.skill_discounts_dict:
                    discount = ability.skill_discounts_dict[str(skill.id)]
                    base_cost = max(0, base_cost - discount)
        
        return base_cost
    
    def get_available_character_points(self):
        """Get the available character points for the character to spend."""
        character_cp_balance = self.base_character_points - self.get_total_skill_cost()
        return self.user.character_points + max(0, character_cp_balance)

    def can_purchase_skill(self, skill, user):
        """Check if the character can purchase a skill."""
        # Check if user has permission
        if not (user.player_id == self.player_id or user.has_role('user_admin')):
            return False, "You don't have permission to modify this character's skills"
        
        # Check character status
        if self.status == CharacterStatus.DEAD.value or self.status == CharacterStatus.RETIRED.value:
            if not user.has_role('user_admin'):
                return False, "Only admins can modify skills of dead/retired characters"
        
        # Check if skill can be purchased multiple times
        existing_skill = CharacterSkill.query.filter_by(character_id=self.id, skill_id=skill.id).first()
        if existing_skill and not skill.can_purchase_multiple:
            return False, "This skill cannot be purchased multiple times"
        
        cost = self.get_skill_cost(skill)
        
        # Calculate total CP spent on all current skills
        total_skills_cost = self.get_total_skill_cost()
        
        # Calculate how much CP we need from the user
        remaining_base_cp = self.base_character_points - total_skills_cost
        cp_from_user = max(0, cost - remaining_base_cp)
        
        # Spend CP if character is active
        if self.status == CharacterStatus.ACTIVE.value and cp_from_user > 0:
            if not user.can_spend_character_points(cp_from_user):
                return False, "Not enough character points"
        
        return True, None

    def purchase_skill(self, skill, user):
        """Purchase a skill for the character."""
        can_purchase, error = self.can_purchase_skill(skill, user)
        if not can_purchase:
            raise ValueError(error)
        
        cost = self.get_skill_cost(skill)
        
        # Calculate total CP spent on all current skills
        total_skills_cost = self.get_total_skill_cost()
        
        # Calculate how much CP we need from the user
        user_spent_before = max(0, total_skills_cost - self.base_character_points)
        user_spent_after = max(0, total_skills_cost + cost - self.base_character_points)
        cp_from_user = user_spent_after - user_spent_before
        
        # Spend CP if character is active
        if self.status == CharacterStatus.ACTIVE.value and cp_from_user > 0:
            user.spend_character_points(cp_from_user)
        
        # Create or update the character skill
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id,
            skill_id=skill.id
        ).first()
        
        if character_skill:
            character_skill.times_purchased += 1
            character_skill.purchased_at = datetime.utcnow()
            character_skill.purchased_by_user_id = user.id
        else:
            character_skill = CharacterSkill(
                character_id=self.id,
                skill_id=skill.id,
                times_purchased=1,
                purchased_by_user_id=user.id
            )
            db.session.add(character_skill)
        
        db.session.commit()
        return True

    def refund_skill(self, skill, user):
        """Refund a skill purchase for the character."""
        # Check if user has permission
        if not (user.player_id == self.player_id or user.has_role('user_admin')):
            raise ValueError("You don't have permission to modify this character's skills")
        
        # Check character status
        if self.status == CharacterStatus.DEAD.value or self.status == CharacterStatus.RETIRED.value:
            if not user.has_role('user_admin'):
                raise ValueError("Only admins can modify skills of dead/retired characters")
        
        # Get the character skill
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id,
            skill_id=skill.id
        ).first()
        
        if not character_skill:
            raise ValueError("Character does not have this skill")
        
        # Calculate how much CP was spent from the user's pool before the refund
        total_skills_cost_before = self.get_total_skill_cost()
        user_spent_before = max(0, total_skills_cost_before - self.base_character_points)

        # Calculate refund amount for this specific skill purchase
        refund_amount = self.get_skill_cost(skill, is_refund=True)

        if character_skill.times_purchased <= 1:
            # Remove the skill entirely
            db.session.delete(character_skill)
        else:
            # Decrease the times purchased
            character_skill.times_purchased -= 1
        
        # Calculate how much CP would be spent from the user's pool after the refund
        total_skills_cost_after = total_skills_cost_before - refund_amount
        user_spent_after = max(0, total_skills_cost_after - self.base_character_points)
        
        # The actual refund is the difference
        refund_to_user = user_spent_before - user_spent_after
        
        # Refund CP if character is active
        if self.status == CharacterStatus.ACTIVE.value and refund_to_user > 0:
            self.user.add_character_points(refund_to_user)
        
        db.session.commit()
        return True

    def get_known_modifications(self):
        """Get the known modifications for the character."""
        return Mod.query.filter(Mod.id.in_(self.known_modifications)).all()

    def get_total_reputation(self):
        """Get the total reputation for the character."""
        return sum(reputation.value for reputation in self.reputations)

    def get_reputation(self, faction_id):
        """Get the character's reputation with a faction."""
        reputation = CharacterReputation.query.filter_by(
            character_id=self.id,
            faction_id=faction_id
        ).first()
        return reputation.value if reputation else 0

    def set_reputation(self, faction_id, value, editor_user_id):
        """Set the character's reputation with a faction."""
        reputation = CharacterReputation.query.filter_by(
            character_id=self.id,
            faction_id=faction_id
        ).first()
        
        if reputation:
            old_value = reputation.value
            reputation.value = value
        else:
            old_value = 0
            reputation = CharacterReputation(
                character_id=self.id,
                faction_id=faction_id,
                value=value
            )
            db.session.add(reputation)
        
        # Log the change
        log = CharacterAuditLog(
            character_id=self.id,
            editor_user_id=editor_user_id,
            action=CharacterAuditAction.REPUTATION_CHANGE,
            changes=f"Reputation with faction {faction_id} changed from {old_value} to {value}"
        )
        db.session.add(log)
        
        db.session.commit()
        return True

    @property
    def cybernetics(self):
        return [link.cybernetic for link in self.cybernetics_link]

    def get_available_science_slots(self, science_type=None):
        """Get the number of available science slots for a given type."""
        if science_type is None:
            skill_slots = sum(skill.skill.adds_science_downtime * skill.times_purchased for skill in self.skills if skill.skill.adds_science_downtime > 0 if skill.character_meets_requirements(self))
            cybernetic_slots = sum(cybernetic.cybernetic.adds_science_downtime for cybernetic in self.cybernetics_link if cybernetic.cybernetic.adds_science_downtime > 0)
            return skill_slots + cybernetic_slots
        else:
            skill_slots = sum(skill.skill.adds_science_downtime * skill.times_purchased for skill in self.skills if skill.skill.adds_science_downtime > 0 and skill.skill.science_type == science_type and skill.character_meets_requirements(self))
            cybernetic_slots = sum(cybernetic.cybernetic.adds_science_downtime for cybernetic in self.cybernetics_link if cybernetic.cybernetic.adds_science_downtime > 0 and cybernetic.cybernetic.science_type == science_type)
            return skill_slots + cybernetic_slots
        return 0

    def get_available_engineering_slots(self):
        """Get the number of available engineering maintenance slots."""
        skill_slots = sum(skill.skill.adds_engineering_downtime * skill.times_purchased for skill in self.skills if skill.skill.adds_engineering_downtime > 0)
        cybernetic_slots = sum(cybernetic.cybernetic.adds_engineering_downtime for cybernetic in self.cybernetics_link if cybernetic.cybernetic.adds_engineering_downtime > 0)
        return skill_slots + cybernetic_slots
    
    def get_available_engineering_mod_slots(self):
        """Get the number of available engineering mod slots."""
        skill_slots = sum(skill.skill.adds_engineering_mods * skill.times_purchased for skill in self.skills if skill.skill.adds_engineering_mods > 0)
        cybernetic_slots = sum(cybernetic.cybernetic.adds_engineering_mods for cybernetic in self.cybernetics_link if cybernetic.cybernetic.adds_engineering_mods > 0)
        return skill_slots + cybernetic_slots

    def get_character_sheet_values(self):
        """Get the character sheet values for the character."""
        values = {}
        for skill in self.skills:
            if skill.skill.character_sheet_values_list:
                for value in skill.skill.character_sheet_values_list:
                    values[value["id"]] = {"name": value["description"], "value": value["value"]}
        return values

    def get_factions_with_reputation(self):
        """Get the factions with a reputation for the character."""
        return [reputation.faction for reputation in self.reputations if reputation.value > 0]
    
    def get_available_funds(self):
        """Get the available funds for the character."""
        return self.bank_account + (self.group.bank_account if self.group else 0)
    
    def can_afford(self, amount):
        """Check if the character can afford an amount."""
        return self.get_available_funds() >= amount
    
    def spend_funds(self, amount):
        """Spend funds for the character."""
        if not self.can_afford(amount):
            return
        # Remove funds from the character account first
        if self.bank_account >= amount:
            self.bank_account -= amount
            amount = 0
        else:
            amount -= self.bank_account
            self.bank_account = 0
        
        # If there's still more to pay, remove from the group account
        if amount > 0 and self.group:
            if self.group.bank_account >= amount:
                self.group.bank_account -= amount
            else:
                self.group.bank_account = 0

def assign_character_id(player_id):
    """Assign a new character ID for a player."""
    # Get the highest character_id for this player
    highest_id = Character.query.filter_by(user_id=player_id).order_by(Character.character_id.desc()).first()
    
    # If no characters exist for this player, start with ID 1
    if not highest_id or highest_id.character_id is None:
        return 1
        
    # Otherwise, increment the highest ID
    return highest_id.character_id + 1

class CharacterAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    editor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action = db.Column(db.Enum(CharacterAuditAction, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=False)
    changes = db.Column(db.Text, nullable=True)

    character = db.relationship('Character', back_populates='audit_logs')
    editor = db.relationship('User')

    def __repr__(self):
        return f'<CharacterAuditLog {self.action} by {self.editor.username}>'

class CharacterReputation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    faction_id = db.Column(db.Integer, db.ForeignKey('faction.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    character = db.relationship('Character', back_populates='reputations')
    faction = db.relationship('Faction')

    __table_args__ = (
        db.UniqueConstraint('character_id', 'faction_id', name='uix_character_faction'),
    )

    def __repr__(self):
        return f'<CharacterReputation {self.character.name} - {self.faction.name}: {self.value}>'

class CharacterCondition(db.Model):
    __tablename__ = 'character_conditions'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey('conditions.id'), nullable=False)
    current_stage = db.Column(db.Integer, nullable=False, default=1)
    current_duration = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    character = db.relationship('Character', back_populates='active_conditions')
    condition = db.relationship('Condition')

    __table_args__ = (
        db.UniqueConstraint('character_id', 'condition_id', name='uix_character_condition'),
    )

    def __repr__(self):
        return f'<CharacterCondition {self.character.name} - {self.condition.name}>'

def setup_relationships():
    Character.user = db.relationship('User', back_populates='characters')
    Character.faction = db.relationship('Faction', back_populates='characters')
    Character.species = db.relationship('Species', back_populates='characters')
    Character.skills = db.relationship('CharacterSkill', back_populates='character')
    Character.audit_logs = db.relationship('CharacterAuditLog', back_populates='character')
    Character.reputations = db.relationship('CharacterReputation', back_populates='character')
    Character.active_conditions = db.relationship('CharacterCondition', back_populates='character')
    Character.group = db.relationship('Group', back_populates='characters')
    Character.cybernetics_link = db.relationship('CharacterCybernetic', back_populates='character')
    Character.downtime_packs = db.relationship('DowntimePack', back_populates='character')
    Character.event_tickets = db.relationship('EventTicket', back_populates='character')