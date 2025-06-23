from enum import Enum


class Role(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER_ADMIN = "user_admin"
    RULES_TEAM = "rules_team"
    PLOT_TEAM = "plot_team"
    DOWNTIME_TEAM = "downtime_team"
    NPC = "npc"

    @classmethod
    def values(cls):
        return [role.value for role in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.OWNER.value: "Owner",
            cls.ADMIN.value: "Admin",
            cls.USER_ADMIN.value: "User Admin",
            cls.RULES_TEAM.value: "Rules Team",
            cls.PLOT_TEAM.value: "Plot Team",
            cls.DOWNTIME_TEAM.value: "Downtime Team",
            cls.NPC.value: "NPC",
        }


class CharacterStatus(Enum):
    DEVELOPING = "developing"
    ACTIVE = "active"
    DEAD = "dead"
    RETIRED = "retired"

    @classmethod
    def values(cls):
        return [status.value for status in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.DEVELOPING.value: "In Development",
            cls.ACTIVE.value: "Active",
            cls.DEAD.value: "Dead",
            cls.RETIRED.value: "Retired",
        }


class BodyHitsType(Enum):
    LOCATIONAL = "locational"
    GLOBAL = "global"

    @classmethod
    def values(cls):
        return [hit_type.value for hit_type in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.LOCATIONAL.value: "Locational Hits",
            cls.GLOBAL.value: "Global Hits",
        }


class SectionRestrictionType(Enum):
    ROLE = "role"
    FACTION = "faction"
    SPECIES = "species"
    REPUTATION = "reputation"
    SKILL = "skill"
    CYBERNETIC = "cybernetic"
    TAG = "tag"

    @classmethod
    def values(cls):
        return [restriction.value for restriction in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.ROLE.value: "Role",
            cls.FACTION.value: "Faction",
            cls.SPECIES.value: "Species",
            cls.REPUTATION.value: "Reputation",
            cls.SKILL.value: "Skill",
            cls.CYBERNETIC.value: "Character has Cybernetic",
            cls.TAG.value: "Character Tag",
        }


class WikiPageVersionStatus(Enum):
    PUBLISHED = "published"
    PENDING = "pending"

    @classmethod
    def values(cls):
        return [status.value for status in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.PUBLISHED.value: "Published",
            cls.PENDING.value: "Pending Review",
        }


class AbilityType(Enum):
    GENERIC = "generic"
    STARTING_SKILLS = "starting_skills"
    SKILL_DISCOUNTS = "skill_discounts"

    @classmethod
    def values(cls):
        return [t.value for t in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.GENERIC.value: "Generic Ability",
            cls.STARTING_SKILLS.value: "Starting Skills",
            cls.SKILL_DISCOUNTS.value: "Skill Discounts",
        }


class CharacterAuditAction(Enum):
    CREATE = "create"
    EDIT = "edit"
    STATUS_CHANGE = "status_change"
    SKILL_CHANGE = "skill_change"
    REPUTATION_CHANGE = "reputation_change"
    FUNDS_ADDED = "funds_added"
    FUNDS_REMOVED = "funds_removed"
    FUNDS_SET = "funds_set"
    GROUP_JOINED = "group_joined"
    GROUP_LEFT = "group_left"
    CONDITION_CHANGE = "condition_change"
    CYBERNETICS_CHANGE = "cybernetics_change"

    @classmethod
    def descriptions(cls):
        return {
            cls.CREATE.value: "Created",
            cls.EDIT.value: "Edited",
            cls.STATUS_CHANGE.value: "Status Changed",
            cls.SKILL_CHANGE.value: "Skills Modified",
            cls.REPUTATION_CHANGE.value: "Reputation Changed",
            cls.FUNDS_ADDED.value: "Funds Added",
            cls.FUNDS_REMOVED.value: "Funds Removed",
            cls.FUNDS_SET.value: "Funds Set",
            cls.GROUP_JOINED.value: "Joined Group",
            cls.GROUP_LEFT.value: "Left Group",
            cls.CONDITION_CHANGE.value: "Condition Changed",
            cls.CYBERNETICS_CHANGE.value: "Cybernetic Changed",
        }


class GroupAuditAction(Enum):
    CREATE = "create"
    EDIT = "edit"
    INVITE_SENT = "invite_sent"
    INVITE_DECLINED = "invite_declined"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    MEMBER_LEFT = "member_left"
    FUNDS_ADDED = "funds_added"
    FUNDS_WITHDRAWN = "funds_withdrawn"
    FUNDS_SET = "funds_set"
    DISBANDED = "disbanded"

    @classmethod
    def descriptions(cls):
        return {
            cls.CREATE.value: "Created",
            cls.EDIT.value: "Edited",
            cls.INVITE_SENT.value: "Invite Sent",
            cls.INVITE_DECLINED.value: "Invite Declined",
            cls.MEMBER_ADDED.value: "Member Added",
            cls.MEMBER_REMOVED.value: "Member Removed",
            cls.MEMBER_LEFT.value: "Member Left",
            cls.FUNDS_ADDED.value: "Funds Added",
            cls.FUNDS_WITHDRAWN.value: "Funds Withdrawn",
            cls.FUNDS_SET.value: "Funds Set",
            cls.DISBANDED.value: "Disbanded",
        }


class GroupType(Enum):
    MILITARY = "military"
    SCIENTIFIC = "scientific"
    CORPORATE = "corporate"

    @classmethod
    def values(cls):
        return [type.value for type in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.MILITARY.value: "Military",
            cls.SCIENTIFIC.value: "Scientific",
            cls.CORPORATE.value: "Corporate",
        }


class ScienceType(Enum):
    GENERIC = "generic"
    LIFE = "life"
    CORPOREAL = "corporeal"
    ETHERIC = "etheric"

    @classmethod
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.GENERIC.value: "Generic",
            cls.LIFE.value: "Life",
            cls.CORPOREAL.value: "Corporeal",
            cls.ETHERIC.value: "Etheric",
        }


class ResearchType(Enum):
    INVENTION = "invention"
    ARTEFACT = "artefact"

    @classmethod
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.INVENTION.value: "Invention",
            cls.ARTEFACT.value: "Artefact",
        }


class ResearchRequirementType(Enum):
    SCIENCE = "science"
    ITEM = "item"
    EXOTIC = "exotic"
    SAMPLE = "sample"

    @classmethod
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.SCIENCE.value: "Required Science",
            cls.ITEM.value: "Required Item",
            cls.EXOTIC.value: "Required Exotic",
            cls.SAMPLE.value: "Required Sample",
        }


class DowntimeStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"

    @classmethod
    def values(cls):
        return [status.value for status in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.PENDING.value: "Pending",
            cls.COMPLETED.value: "Completed",
        }


class DowntimeTaskStatus(Enum):
    ENTER_PACK = "enter_pack"
    ENTER_DOWNTIME = "enter_downtime"
    MANUAL_REVIEW = "manual_review"
    COMPLETED = "completed"

    @classmethod
    def values(cls):
        return [status.value for status in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.ENTER_PACK.value: "Enter Pack",
            cls.ENTER_DOWNTIME.value: "Enter Downtime",
            cls.MANUAL_REVIEW.value: "Manual Review",
            cls.COMPLETED.value: "Completed",
        }


class EventType(Enum):
    MAINLINE = "mainline"
    SANCTIONED = "sanctioned"
    ONLINE = "online"

    @classmethod
    def values(cls):
        return [type.value for type in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.MAINLINE.value: "Mainline Event",
            cls.SANCTIONED.value: "Sanctioned Event",
            cls.ONLINE.value: "Online Event",
        }


class TicketType(Enum):
    ADULT = "adult"
    CHILD_12_15 = "child_12_15"
    CHILD_7_11 = "child_7_11"
    CHILD_UNDER_7 = "child_under_7"
    CREW = "crew"

    @classmethod
    def values(cls):
        return [type.value for type in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.ADULT.value: "Adult",
            cls.CHILD_12_15.value: "Child (12-15)",
            cls.CHILD_7_11.value: "Child (7-11)",
            cls.CHILD_UNDER_7.value: "Child (under 7)",
            cls.CREW.value: "Crew",
        }


class PrintTemplateType(Enum):
    CHARACTER_SHEET = "character_sheet"
    CHARACTER_ID = "character_id"
    ITEM_CARD = "item_card"
    MEDICAMENT_CARD = "medicament_card"
    CONDITION_CARD = "condition_card"
    EXOTIC_SUBSTANCE_LABEL = "exotic_substance_label"

    @classmethod
    def values(cls):
        return [type.value for type in cls]

    @classmethod
    def descriptions(cls):
        return {
            cls.CHARACTER_SHEET.value: "Character Sheet",
            cls.CHARACTER_ID.value: "Character ID",
            cls.ITEM_CARD.value: "Item Card",
            cls.MEDICAMENT_CARD.value: "Medicament Card",
            cls.CONDITION_CARD.value: "Condition Card",
            cls.EXOTIC_SUBSTANCE_LABEL.value: "Exotic Substance Label",
        }
