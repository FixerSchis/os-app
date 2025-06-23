from datetime import datetime, timezone

from sqlalchemy import JSON

from models.database.mods import Mod
from models.enums import CharacterAuditAction, CharacterStatus, ScienceType
from models.extensions import db
from models.tools.pack import Pack

# Association table for many-to-many relationship between Character and CharacterTag
character_tags = db.Table(
    "character_tags",
    db.Column("character_id", db.Integer, db.ForeignKey("character.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("character_tag.id"), primary_key=True),
)


class CharacterTag(db.Model):
    __tablename__ = "character_tag"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Relationship to characters through the association table
    characters = db.relationship(
        "Character",
        secondary=character_tags,
        backref=db.backref("tags", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<CharacterTag {self.name}>"


class CharacterSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    times_purchased = db.Column(db.Integer, nullable=False, default=1)
    purchased_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    purchased_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    character = db.relationship("Character", back_populates="skills")
    skill = db.relationship("Skill")
    purchased_by = db.relationship("User")

    def __repr__(self):
        return f"<CharacterSkill {self.skill.name} (x{self.times_purchased})>"


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    character_id = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    pronouns_subject = db.Column(db.String(20), nullable=True)
    pronouns_object = db.Column(db.String(20), nullable=True)
    faction_id = db.Column(db.Integer, db.ForeignKey("faction.id"), nullable=True)
    species_id = db.Column(db.Integer, db.ForeignKey("species.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=CharacterStatus.ACTIVE)
    base_character_points = db.Column(db.Integer, nullable=False, default=10)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=True)
    bank_account = db.Column(db.Integer, nullable=False, default=0)
    character_pack = db.Column(JSON, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Downtime-related fields
    known_modifications = db.Column(db.JSON, default=list)  # List of mod IDs

    # Relationships
    user = db.relationship("User", back_populates="characters")
    faction = db.relationship("Faction", back_populates="characters")
    species = db.relationship("Species", back_populates="characters")
    skills = db.relationship("CharacterSkill", back_populates="character")
    audit_logs = db.relationship("CharacterAuditLog", back_populates="character")
    reputations = db.relationship("CharacterReputation", back_populates="character")
    active_conditions = db.relationship("CharacterCondition", back_populates="character")
    group = db.relationship("Group", back_populates="characters")
    cybernetics_link = db.relationship("CharacterCybernetic", back_populates="character")
    downtime_packs = db.relationship("DowntimePack", back_populates="character")
    event_tickets = db.relationship("EventTicket", back_populates="character")

    @property
    def pack(self) -> Pack:
        """Get the character's pack as a structured Pack object."""
        return Pack.from_dict(self.character_pack or {})

    @pack.setter
    def pack(self, pack: Pack) -> None:
        """Set the character's pack from a structured Pack object."""
        self.character_pack = pack.to_dict()

    @classmethod
    def get_by_player_reference(cls, player_reference):
        if "." in player_reference:
            player_id, char_id = player_reference.split(".")
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
        return f"<Character {self.name}>"

    def get_total_skill_cost(self):
        """Calculate the total cost of all skills for this character."""
        total_cost = 0
        for character_skill in self.skills:
            skill = character_skill.skill
            if skill.cost_increases:
                # For a skill with increasing cost, the cost of the nth purchase is
                # base_cost + (n-1). We sum the cost for each purchase from 1 to
                # times_purchased
                for i in range(character_skill.times_purchased):
                    purchase_cost = skill.base_cost + i
                    # Apply species discounts
                    for ability in self.species.abilities:
                        if (
                            ability.type == "skill_discounts"
                            and str(skill.id) in ability.skill_discounts_dict
                        ):
                            discount = ability.skill_discounts_dict[str(skill.id)]
                            purchase_cost = max(0, purchase_cost - discount)
                    total_cost += purchase_cost
            else:
                purchase_cost = skill.base_cost
                # Apply species discounts
                for ability in self.species.abilities:
                    if (
                        ability.type == "skill_discounts"
                        and str(skill.id) in ability.skill_discounts_dict
                    ):
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
        """Calculate the cost of a skill, taking into account previous purchases and
        species discounts."""
        # Get the number of times this skill has been purchased
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id, skill_id=skill.id
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
                    base_cost += count - 1  # Cost of the Nth purchase
            else:
                base_cost += count  # Cost of the (N+1)th purchase

        # Apply species discounts if any
        for ability in self.species.abilities:
            if ability.type == "skill_discounts":
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
        if not (user.player_id == self.player_id or user.has_role("user_admin")):
            return False, "You don't have permission to modify this character's skills"

        # Check character status
        if (
            self.status == CharacterStatus.DEAD.value
            or self.status == CharacterStatus.RETIRED.value
        ):
            if not user.has_role("user_admin"):
                return False, "Only admins can modify skills of dead/retired characters"

        # Check if skill can be purchased multiple times
        existing_skill = CharacterSkill.query.filter_by(
            character_id=self.id, skill_id=skill.id
        ).first()
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
            character_id=self.id, skill_id=skill.id
        ).first()

        if character_skill:
            character_skill.times_purchased += 1
            character_skill.purchased_at = datetime.now(timezone.utc)
            character_skill.purchased_by_user_id = user.id
        else:
            character_skill = CharacterSkill(
                character_id=self.id,
                skill_id=skill.id,
                times_purchased=1,
                purchased_by_user_id=user.id,
            )
            db.session.add(character_skill)

        db.session.commit()
        return True

    def refund_skill(self, skill, user):
        """Refund a skill purchase for the character."""
        # Check if user has permission
        if not (user.player_id == self.player_id or user.has_role("user_admin")):
            raise ValueError("You don't have permission to modify this character's skills")

        # Check character status
        if (
            self.status == CharacterStatus.DEAD.value
            or self.status == CharacterStatus.RETIRED.value
        ):
            if not user.has_role("user_admin"):
                raise ValueError("Only admins can modify skills of dead/retired characters")

        # Get the character skill
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id, skill_id=skill.id
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
            character_id=self.id, faction_id=faction_id
        ).first()
        return reputation.value if reputation else 0

    def set_reputation(self, faction_id, value, editor_user_id):
        """Set the character's reputation with a faction."""
        reputation = CharacterReputation.query.filter_by(
            character_id=self.id, faction_id=faction_id
        ).first()

        if reputation:
            old_value = reputation.value
            reputation.value = value
        else:
            old_value = 0
            reputation = CharacterReputation(
                character_id=self.id, faction_id=faction_id, value=value
            )
            db.session.add(reputation)

        # Log the change
        log = CharacterAuditLog(
            character_id=self.id,
            editor_user_id=editor_user_id,
            action=CharacterAuditAction.REPUTATION_CHANGE,
            changes=(
                f"Reputation with faction {faction_id} changed from {old_value} " f"to {value}"
            ),
        )
        db.session.add(log)

        return True

    @property
    def cybernetics(self):
        return [link.cybernetic for link in self.cybernetics_link]

    def get_available_science_slots(self, science_type=None):
        """Get the available science slots for the character."""
        skill_slots = 0
        cybernetic_slots = 0
        st_value = (
            science_type.value
            if science_type and isinstance(science_type, ScienceType)
            else science_type
        )

        # Calculate slots from skills
        for skill_link in self.skills:
            skill = skill_link.skill
            if not (skill.adds_science_downtime > 0 and skill.character_meets_requirements(self)):
                continue

            if st_value:
                skill_st = skill.science_type
                if st_value == ScienceType.GENERIC.value:
                    if skill_st is None:
                        skill_slots += skill.adds_science_downtime * skill_link.times_purchased
                elif skill_st and skill_st.value == st_value:
                    skill_slots += skill.adds_science_downtime * skill_link.times_purchased
            else:
                skill_slots += skill.adds_science_downtime * skill_link.times_purchased

        # Calculate slots from cybernetics
        for cyber_link in self.cybernetics_link:
            cyber = cyber_link.cybernetic
            if not cyber.adds_science_downtime > 0:
                continue

            if st_value:
                cyber_st = cyber.science_type
                if st_value == ScienceType.GENERIC.value:
                    if cyber_st is None:
                        cybernetic_slots += cyber.adds_science_downtime
                elif cyber_st and cyber_st.value == st_value:
                    cybernetic_slots += cyber.adds_science_downtime
            else:
                cybernetic_slots += cyber.adds_science_downtime

        return skill_slots + cybernetic_slots

    def get_available_engineering_slots(self):
        """Get the available engineering slots for the character."""
        skill_slots = sum(
            skill.skill.adds_engineering_downtime * skill.times_purchased
            for skill in self.skills
            if skill.skill.adds_engineering_downtime > 0
            if skill.skill.character_meets_requirements(self)
        )
        cybernetic_slots = sum(
            cyber.cybernetic.adds_engineering_downtime
            for cyber in self.cybernetics_link
            if cyber.cybernetic.adds_engineering_downtime > 0
        )
        return skill_slots + cybernetic_slots

    def get_available_engineering_mod_slots(self):
        """Get the available engineering mod slots for the character."""
        skill_slots = sum(
            skill.skill.adds_engineering_mods * skill.times_purchased
            for skill in self.skills
            if skill.skill.adds_engineering_mods > 0
            if skill.skill.character_meets_requirements(self)
        )
        cybernetic_slots = sum(
            cyber.cybernetic.adds_engineering_mods
            for cyber in self.cybernetics_link
            if cyber.cybernetic.adds_engineering_mods > 0
        )
        return skill_slots + cybernetic_slots

    def get_character_sheet_values(self):
        """Get the character sheet values for the character."""
        values = {}
        for skill in self.skills:
            if skill.skill.character_sheet_values_list:
                for value in skill.skill.character_sheet_values_list:
                    values[value["id"]] = {
                        "name": value["description"],
                        "value": value["value"],
                    }
        return values

    def get_factions_with_reputation(self):
        """Get the factions with a reputation for the character."""
        return [reputation.faction for reputation in self.reputations if reputation.value > 0]

    def get_available_funds(self):
        """Get the available funds for the character."""
        return self.bank_account + (self.group.bank_account if self.group else 0)

    def can_afford(self, amount):
        return self.get_available_funds() >= amount

    def remove_funds(self, amount, editor_user_id, reason):
        """Remove funds from the character's bank account with audit logging."""
        if not self.can_afford(amount):
            raise ValueError("Not enough funds")

        # Calculate how much to take from character balance vs group balance
        character_contribution = min(self.bank_account, amount)
        group_contribution = amount - character_contribution

        # Deduct remaining from group balance
        # Perform first to fail if group doesn't have enough funds
        if group_contribution > 0 and self.group:
            self.group.remove_funds(
                group_contribution, editor_user_id, f"Character {self.name} spent on: {reason}"
            )

        # Deduct from character balance
        if character_contribution > 0:
            self.bank_account -= character_contribution

        # Create an audit log for the expenditure
        changes_parts = []
        if character_contribution > 0:
            changes_parts.append(f"Character: {character_contribution}")
        if group_contribution > 0:
            changes_parts.append(f"Group: {group_contribution}")

        changes_text = f"Removed {amount} for {reason} ({', '.join(changes_parts)})"

        audit_log = CharacterAuditLog(
            character_id=self.id,
            editor_user_id=editor_user_id,
            action=CharacterAuditAction.FUNDS_REMOVED,
            changes=changes_text,
        )
        db.session.add(audit_log)

    def add_funds(self, amount, editor_user_id, reason):
        """Add funds to the character's bank account with audit logging."""
        self.bank_account += amount

        # Create an audit log for the addition
        audit_log = CharacterAuditLog(
            character_id=self.id,
            editor_user_id=editor_user_id,
            action=CharacterAuditAction.FUNDS_ADDED,
            changes=f"Added {amount} for {reason}",
        )
        db.session.add(audit_log)

    def set_funds(self, new_balance, editor_user_id, reason):
        """Set the character's bank account to a specific value with audit logging."""
        old_balance = self.bank_account
        self.bank_account = new_balance
        audit_log = CharacterAuditLog(
            character_id=self.id,
            editor_user_id=editor_user_id,
            action=CharacterAuditAction.FUNDS_SET,
            changes=f"Funds set from {old_balance} to {new_balance} for {reason}",
        )
        db.session.add(audit_log)


def assign_character_id(player_id):
    """Assign a new character ID for a player."""
    # Get the highest character_id for this player
    highest_id = (
        Character.query.filter_by(user_id=player_id).order_by(Character.character_id.desc()).first()
    )

    # If no characters exist for this player, start with ID 1
    if not highest_id or highest_id.character_id is None:
        return 1

    # Otherwise, increment the highest ID
    return highest_id.character_id + 1


class CharacterAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    editor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    action = db.Column(
        db.Enum(
            CharacterAuditAction,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
    )
    changes = db.Column(db.Text, nullable=True)

    character = db.relationship("Character", back_populates="audit_logs")
    editor = db.relationship("User")

    def __repr__(self):
        return f"<CharacterAuditLog {self.action} by {self.editor.email}>"


class CharacterReputation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    faction_id = db.Column(db.Integer, db.ForeignKey("faction.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    character = db.relationship("Character", back_populates="reputations")
    faction = db.relationship("Faction")

    __table_args__ = (
        db.UniqueConstraint("character_id", "faction_id", name="uix_character_faction"),
    )

    def __repr__(self):
        return (
            f"<CharacterReputation {self.character.name} - {self.faction.name}: " f"{self.value}>"
        )


class CharacterCondition(db.Model):
    __tablename__ = "character_conditions"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey("conditions.id"), nullable=False)
    current_stage = db.Column(db.Integer, nullable=True, default=1)
    current_duration = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    character = db.relationship("Character", back_populates="active_conditions")
    condition = db.relationship("Condition")

    __table_args__ = (
        db.UniqueConstraint("character_id", "condition_id", name="uix_character_condition"),
    )

    def __repr__(self):
        return f"<CharacterCondition {self.character.name} - {self.condition.name}>"

    def progress_condition(self) -> dict:
        """
        Progress the condition by one event. Returns a dict with the result.

        Returns:
            dict: Contains 'progressed' (bool), 'message' (str), and 'completed' (bool)
        """
        # Get the current stage
        current_stage_obj = None
        for stage in self.condition.stages:
            if stage.stage_number == self.current_stage:
                current_stage_obj = stage
                break

        if not current_stage_obj:
            return {
                "progressed": False,
                "message": (
                    f"Invalid stage {self.current_stage} for condition {self.condition.name}"
                ),
                "completed": False,
            }

        # Deduct one event from the current duration
        self.current_duration -= 1

        # Check if we've reached 0 events remaining
        if self.current_duration <= 0:
            # Find the next stage
            next_stage = None
            for stage in self.condition.stages:
                if stage.stage_number == self.current_stage + 1:
                    next_stage = stage
                    break

            if next_stage:
                # Progress to next stage
                self.current_stage = next_stage.stage_number
                self.current_duration = next_stage.duration
                return {
                    "progressed": True,
                    "message": (
                        f"Condition {self.condition.name} progressed to stage {self.current_stage}"
                    ),
                    "completed": False,
                }
            else:
                # No more stages - condition has reached its conclusion
                # TODO: Implement condition conclusion system
                self.current_stage = None
                self.current_duration = 0
                return {
                    "progressed": True,
                    "message": (f"Condition {self.condition.name} has reached its conclusion"),
                    "completed": True,
                }
        else:
            # Still in the same stage
            return {
                "progressed": True,
                "message": (
                    f"Condition {self.condition.name} stage {self.current_stage} "
                    f"has {self.current_duration} events remaining"
                ),
                "completed": False,
            }
