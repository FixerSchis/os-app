import json
from datetime import datetime, timezone

from sqlalchemy import false, func, or_

from models.database.mods import Mod
from models.enums import (
    AbilityType,
    BodyHitsType,
    CharacterAuditAction,
    CharacterStatus,
    ScienceType,
)
from models.extensions import db
from models.tools.pack import Pack

# Association table for many-to-many relationship between Character and CharacterTag
character_tags = db.Table(
    "character_tags",
    db.Column("character_id", db.Integer, db.ForeignKey("character.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("character_tag.id"), primary_key=True),
)


def _species_uses_global_hits(species):
    hit_type = species.body_hits_type
    hit_value = hit_type.value if hasattr(hit_type, "value") else hit_type
    return hit_value == BodyHitsType.GLOBAL.value


def _ability_type_value(ability):
    ability_type = ability.type
    return ability_type.value if hasattr(ability_type, "value") else ability_type


def _pool_key(skill_ids):
    return tuple(sorted(int(item) for item in skill_ids or []))


def _skill_name_list(skill_ids):
    from models.database.skills import Skill

    rows = Skill.query.filter(Skill.id.in_(list(skill_ids))).all()
    by_id = {row.id: row.name for row in rows}
    names = [by_id[skill_id] for skill_id in skill_ids if skill_id in by_id]
    if not names:
        return "another skill"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", or " + names[-1]


def _positive_rank_limit(value):
    if value is None or value == "":
        return None
    limit = int(value)
    if limit < 1:
        return None
    return limit


# Association table for many-to-many relationship between Character and Sample
character_samples = db.Table(
    "character_samples",
    db.Column("character_id", db.Integer, db.ForeignKey("character.id"), primary_key=True),
    db.Column("sample_id", db.Integer, db.ForeignKey("sample.id"), primary_key=True),
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
    free_ranks = db.Column(db.Integer, nullable=False, default=0)
    purchased_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    purchased_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    character = db.relationship("Character", back_populates="skills")
    skill = db.relationship("Skill")
    purchased_by = db.relationship("User")

    def __repr__(self):
        return f"<CharacterSkill {self.skill.name} (x{self.times_purchased})>"

    def format_description(self):
        """Description with this character's purchased rank substituted."""
        if not self.skill:
            return ""
        return self.skill.format_applied(self.times_purchased)

    def paid_purchases(self):
        """Ranks the character paid for. A free creation rank is not one of these."""
        return max(0, self.times_purchased - (self.free_ranks or 0))


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
    character_pack = db.Column(db.JSON, nullable=True)  # JSON data
    pack_complete = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Downtime-related fields
    known_modifications = db.Column(db.JSON, default=list)  # List of mod IDs

    # Character background fields
    background = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    concept = db.Column(db.Text, nullable=True)
    skill_pair_grants = db.Column(db.String, nullable=True)

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
    inventory_items = db.relationship("CharacterItem", back_populates="character")
    samples = db.relationship("Sample", secondary="character_samples", lazy="dynamic")
    abilities = db.relationship(
        "Ability",
        backref="character",
        cascade="all, delete-orphan",
        foreign_keys="Ability.character_id",
    )

    @property
    def pack(self):
        try:
            # character_pack is always JSON data (dict) since we control the data
            pack = Pack(**self.character_pack)
            return pack
        except Exception:
            return Pack()

    @pack.setter
    def pack(self, pack):
        self.character_pack = pack.to_dict()
        self.pack_complete = pack.is_completed

    @classmethod
    def get_by_player_reference(cls, player_reference):
        if "." in player_reference:
            user_id, char_id = player_reference.split(".")
            return cls.get_by_user_id_and_char_id(user_id, char_id)
        else:
            return None

    @classmethod
    def get_by_user_id_and_char_id(cls, user_id, char_id):
        return cls.query.filter_by(user_id=user_id, character_id=char_id).first()

    @classmethod
    def filter_by_search(cls, query_text, characters_query=None):
        """Match characters by name, user name, or user_id.character_id.

        A value like ``12.3`` matches that player reference exactly. Any other
        text matches the character name or the user's first name, surname, or
        full name.
        """
        from models.tools.user import User

        if characters_query is None:
            characters_query = cls.query

        query_text = (query_text or "").strip()
        if len(query_text) < 2:
            return characters_query.filter(false())

        if query_text.count(".") == 1:
            user_id_str, char_id_str = query_text.split(".", 1)
            if user_id_str.isdigit() and char_id_str.isdigit():
                return characters_query.filter(
                    cls.user_id == int(user_id_str),
                    cls.character_id == int(char_id_str),
                )

        full_name = func.trim(func.concat(User.first_name, " ", func.coalesce(User.surname, "")))
        pattern = f"%{query_text}%"
        return characters_query.join(User).filter(
            or_(
                cls.name.ilike(pattern),
                User.first_name.ilike(pattern),
                User.surname.ilike(pattern),
                full_name.ilike(pattern),
            )
        )

    def __repr__(self):
        return f"<Character {self.name}>"

    def get_total_skill_cost(self):
        """Calculate the total cost of all skills for this character."""
        total_cost = 0
        for character_skill in self.skills:
            skill = character_skill.skill
            paid = character_skill.paid_purchases()
            discount = self.skill_discount(skill)
            if skill.cost_increases:
                # The first paid purchase costs base_cost. A free rank is not a paid purchase.
                for i in range(paid):
                    total_cost += max(0, skill.base_cost + i - discount)
            else:
                total_cost += max(0, skill.base_cost - discount) * paid
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
        count = 0 if character_skill is None else character_skill.paid_purchases()
        if is_refund and count <= 0:
            return 0

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

        return max(0, base_cost - self.skill_discount(skill))

    def skill_discount(self, skill):
        """Character points a species skill-discount ability takes off this skill."""
        if self.species is None:
            return 0
        discount = 0
        for ability in self.species.abilities:
            if _ability_type_value(ability) != AbilityType.SKILL_DISCOUNTS.value:
                continue
            amount = ability.skill_discounts_dict.get(str(skill.id))
            if amount:
                discount += int(amount)
        return discount

    def get_available_character_points(self):
        """Get the available character points for the character to spend."""
        from models.tools.user import User

        # Query the user directly to get the current character points
        user = User.query.get(self.user_id)
        user_points = user.character_points if user else 0

        character_cp_balance = self.base_character_points - self.get_total_skill_cost()
        total_available = user_points + max(0, character_cp_balance)

        return total_available

    @property
    def skill_pair_grants_list(self):
        if not self.skill_pair_grants:
            return []
        return json.loads(self.skill_pair_grants)

    @skill_pair_grants_list.setter
    def skill_pair_grants_list(self, grants):
        self.skill_pair_grants = json.dumps(grants) if grants else None

    def skill_requirement_error(self, skill):
        """Return why this skill cannot be bought, or None when its skill rules are met."""
        owned = self._owned_skill_ids()
        any_of = skill.required_any_skills_list
        if any_of and not set(any_of) & owned:
            return f"Requires one of {_skill_name_list(any_of)}"
        pool = skill.distinct_requirements_list
        if pool and not self._has_distinct_requirement(skill, owned):
            return f"Requires a different one of {_skill_name_list(pool)}"
        return None

    def skill_refund_error(self, skill):
        """Return why this skill cannot be refunded, or None when other skills stay valid."""
        owned = self._owned_skill_ids()
        if skill.id not in owned:
            return None
        for peer in self._requirement_skills():
            if peer.id not in owned:
                continue
            options = peer.required_any_skills_list
            if skill.id in options and not any(
                option in owned and option != skill.id for option in options
            ):
                return f"Cannot refund {skill.name} as it is required for {peer.name}."
            pool = peer.distinct_requirements_list
            if skill.id not in pool:
                continue
            key = _pool_key(pool)
            consumers = sum(
                1
                for other in self._requirement_skills()
                if other.id in owned and _pool_key(other.distinct_requirements_list) == key
            )
            remaining = len(set(pool) & owned) - 1
            if remaining < consumers:
                return f"Cannot refund {skill.name} as it is required for {peer.name}."
        return None

    def _has_distinct_requirement(self, skill, owned):
        key = _pool_key(skill.distinct_requirements_list)
        consumers = 0
        for peer in self._requirement_skills():
            if _pool_key(peer.distinct_requirements_list) != key:
                continue
            if peer.id in owned or peer.id == skill.id:
                consumers += 1
        return len(set(skill.distinct_requirements_list) & owned) >= consumers

    def _requirement_skills(self):
        cached = getattr(self, "_requirement_skill_cache", None)
        if cached is None:
            from models.database.skills import Skill

            cached = Skill.query.filter(
                or_(
                    Skill.required_any_skills.isnot(None),
                    Skill.distinct_requirements.isnot(None),
                )
            ).all()
            self._requirement_skill_cache = cached
        return cached

    def _owned_skill_ids(self):
        return {row.skill_id for row in self.skills}

    def maximum_rank(self, skill):
        """Lowest rank cap from the skill and this species. None means no cap."""
        limit = _positive_rank_limit(skill.max_ranks)
        if self.species is None:
            return limit
        for ability in self.species.abilities:
            ability_type = ability.type.value if hasattr(ability.type, "value") else ability.type
            if ability_type != AbilityType.SKILL_RANK_CAPS.value:
                continue
            for cap in ability.rank_caps_list:
                if int(cap.get("skill_id") or 0) != skill.id:
                    continue
                species_limit = _positive_rank_limit(cap.get("max_ranks"))
                if species_limit is None:
                    continue
                limit = species_limit if limit is None else min(limit, species_limit)
        return limit

    def can_purchase_skill(self, skill, user):
        """Check if the character can purchase a skill."""
        # Check if user has permission
        if not (user.id == self.user_id or user.has_permission("character.edit_all")):
            return False, "You don't have permission to modify this character's skills"

        # Check character status
        if (
            self.status == CharacterStatus.DEAD.value
            or self.status == CharacterStatus.RETIRED.value
        ):
            if not user.has_permission("character.edit_all"):
                return False, "Only admins can modify skills of dead/retired characters"

        # Check if skill can be purchased multiple times
        existing_skill = CharacterSkill.query.filter_by(
            character_id=self.id, skill_id=skill.id
        ).first()
        if existing_skill and not skill.can_purchase_multiple:
            return False, "This skill cannot be purchased multiple times"

        owned_ranks = existing_skill.times_purchased if existing_skill else 0
        rank_limit = self.maximum_rank(skill)
        if rank_limit is not None and owned_ranks >= rank_limit:
            return False, f"Maximum {rank_limit} ranks"

        requirement_error = self.skill_requirement_error(skill)
        if requirement_error:
            return False, requirement_error

        if skill.required_skill_id:
            has_prerequisite = CharacterSkill.query.filter_by(
                character_id=self.id, skill_id=skill.required_skill_id
            ).first()
            if not has_prerequisite:
                if skill.required_skill:
                    required_name = skill.required_skill.name
                else:
                    required_name = "another skill"
                return False, f"Requires {required_name}"

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
            # Ensure the user is tracked in the session
            db.session.merge(user)

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

        db.session.flush()
        from utils.skill_pairs import note_skill_purchase

        note_skill_purchase(self, skill, user)

        # Handle reputation from skill if character is active
        if (
            self.status == CharacterStatus.ACTIVE.value
            and skill.adds_reputation_faction_id
            and skill.adds_reputation_value
        ):
            current_reputation = self.get_reputation(skill.adds_reputation_faction_id)
            new_reputation = current_reputation + skill.adds_reputation_value
            self.set_reputation(skill.adds_reputation_faction_id, new_reputation, user.id)

        db.session.commit()
        return True

    def activate(self, user):
        """Activate the character and handle reputation from skills and species abilities."""
        if self.status != CharacterStatus.DEVELOPING.value:
            raise ValueError("Only developing characters can be activated")

        self.status = CharacterStatus.ACTIVE.value

        # Handle reputation from skills
        for character_skill in self.skills:
            skill = character_skill.skill
            if skill.adds_reputation_faction_id and skill.adds_reputation_value:
                current_reputation = self.get_reputation(skill.adds_reputation_faction_id)
                new_reputation = current_reputation + skill.adds_reputation_value
                self.set_reputation(skill.adds_reputation_faction_id, new_reputation, user.id)

        # Handle reputation from species abilities
        if self.species:
            for ability in self.species.abilities:
                if (
                    (
                        ability.type == AbilityType.STARTING_REPUTATION.value
                        or ability.type == AbilityType.STARTING_REPUTATION
                    )
                    and ability.starting_reputation_faction_id
                    and ability.starting_reputation_value
                ):
                    current_reputation = self.get_reputation(ability.starting_reputation_faction_id)
                    new_reputation = current_reputation + ability.starting_reputation_value
                    self.set_reputation(
                        ability.starting_reputation_faction_id, new_reputation, user.id
                    )

        db.session.commit()
        return True

    def refund_skill(self, skill, user):
        """Refund a skill purchase for the character."""
        # Check if user has permission
        if not (user.id == self.user_id or user.has_permission("character.edit_all")):
            raise ValueError("You don't have permission to modify this character's skills")

        # Check character status
        if (
            self.status == CharacterStatus.DEAD.value
            or self.status == CharacterStatus.RETIRED.value
        ):
            if not user.has_permission("character.edit_all"):
                raise ValueError("Only admins can modify skills of dead/retired characters")

        # Get the character skill
        character_skill = CharacterSkill.query.filter_by(
            character_id=self.id, skill_id=skill.id
        ).first()

        if not character_skill:
            raise ValueError("Character does not have this skill")

        refund_error = self.skill_refund_error(skill)
        if refund_error:
            raise ValueError(refund_error)

        from utils.skill_pairs import note_skill_refund

        note_skill_refund(self, skill)

        # Calculate how much CP was spent from the user's pool before the refund
        total_skills_cost_before = self.get_total_skill_cost()
        user_spent_before = max(0, total_skills_cost_before - self.base_character_points)

        # Calculate refund amount for this specific skill purchase
        refund_amount = self.get_skill_cost(skill, is_refund=True)

        # Handle reputation removal if character is active
        if (
            self.status == CharacterStatus.ACTIVE.value
            and skill.adds_reputation_faction_id
            and skill.adds_reputation_value
        ):
            current_reputation = self.get_reputation(skill.adds_reputation_faction_id)
            new_reputation = current_reputation - skill.adds_reputation_value
            self.set_reputation(skill.adds_reputation_faction_id, new_reputation, user.id)

        if character_skill.paid_purchases() == 0:
            character_skill.free_ranks = max(0, (character_skill.free_ranks or 0) - 1)

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
            # Query the user directly to ensure we have the latest state
            from models.tools.user import User

            user_to_refund = User.query.get(self.user_id)
            if user_to_refund:
                user_to_refund.add_character_points(refund_to_user)
                # Ensure the user is tracked in the session
                db.session.merge(user_to_refund)

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

        # Only log the change if the value actually changed
        if old_value != value:
            log = CharacterAuditLog(
                character_id=self.id,
                editor_user_id=editor_user_id,
                action=CharacterAuditAction.REPUTATION_CHANGE.value,
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

    def toughness_ranks(self):
        """Purchased ranks of Toughness, including a free rank."""
        for row in self.skills:
            if row.skill is not None and row.skill.name == "Toughness":
                return row.times_purchased or 0
        return 0

    def toughness_hit_bonus(self):
        """Global hits added by Toughness. Locational species keep those hits per location."""
        if self.species is None or not _species_uses_global_hits(self.species):
            return 0
        per_rank = self.species.extra_hits_per_toughness
        if per_rank is None:
            per_rank = 1
        return self.toughness_ranks() * per_rank

    def printed_abilities(self):
        """Species abilities, then abilities written for this character alone."""
        shared = list(self.species.abilities) if self.species is not None else []
        return shared + list(self.abilities)

    def get_character_sheet_values(self):
        """Get the character sheet values for the character."""
        values = {}
        for skill in self.skills:
            if skill.skill.character_sheet_values_list:
                for value in skill.skill.character_sheet_values_list:
                    value_id = value["id"]
                    if value_id in values:
                        # Add to existing value
                        values[value_id]["value"] += value["value"]
                    else:
                        # Create new entry
                        values[value_id] = {
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

    def can_edit(self, user):
        """Check if a user can edit this character."""
        if not user or not user.is_authenticated:
            return False
        if user.id == self.user_id or user.has_permission("character.edit_all"):
            return True
        return False

    def can_delete(self, user):
        """Check if a user can delete this character."""
        if not user or not user.is_authenticated:
            return False
        if user.has_permission("character.edit_all"):
            return True
        return False

    def can_view_details(self, user):
        """Check if a user can view detailed information about this character."""
        if not user or not user.is_authenticated:
            return False
        if user.id == self.user_id or user.has_permission("character.view_all"):
            return True
        return False

    def can_manage_inventory(self, user):
        """Check if a user can manage this character's inventory."""
        if not user or not user.is_authenticated:
            return False
        if user.has_permission("character.edit_all"):
            return True
        return False


def assign_character_id(user_id):
    """Assign a new character ID for a user."""
    # Get the highest character_id for this user
    highest_id = (
        Character.query.filter_by(user_id=user_id).order_by(Character.character_id.desc()).first()
    )

    # If no characters exist for this user, start with ID 1
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
        return (
            f"<CharacterCondition {self.character.name} - "
            f"{self.condition.name} (Stage {self.current_stage})>"
        )

    @property
    def events_remaining(self):
        """Return the number of events remaining for this condition."""
        return self.current_duration

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


class CharacterBackground(db.Model):
    __tablename__ = "character_backgrounds"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    background = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    concept = db.Column(db.Text, nullable=True)
    needs_review = db.Column(db.Boolean, nullable=False, default=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    character = db.relationship("Character", backref=db.backref("backgrounds", lazy="dynamic"))
    reviewed_by = db.relationship("User")

    def __repr__(self):
        return f"<CharacterBackground {self.character.name} - Review: {self.needs_review}>"

    @classmethod
    def get_or_create_for_character(cls, character_id):
        """Get existing background or create a new one for the character."""
        background = cls.query.filter_by(character_id=character_id).first()
        if not background:
            background = cls(character_id=character_id)
        return background

    def mark_for_review(self):
        """Mark this background as needing review."""
        self.needs_review = True
        self.reviewed_at = None
        self.reviewed_by_user_id = None

    def mark_as_reviewed(self, reviewer_user_id):
        """Mark this background as reviewed."""
        self.needs_review = False
        self.reviewed_at = db.func.now()
        self.reviewed_by_user_id = reviewer_user_id
