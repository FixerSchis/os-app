import os
import secrets

from models.enums import ResearchRequirementType, ResearchType, ScienceType
from models.extensions import db

_bip39_wordlist = None


def get_bip39_wordlist():
    global _bip39_wordlist
    if _bip39_wordlist is None:
        wordlist_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "bip39_verse.txt",
        )
        with open(wordlist_path, "r", encoding="utf-8") as f:
            _bip39_wordlist = [line.strip() for line in f if line.strip()]
    return _bip39_wordlist


def generate_public_id():
    wordlist = get_bip39_wordlist()
    return "-".join(secrets.choice(wordlist) for _ in range(3))


class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), unique=True, nullable=False, default=generate_public_id)
    project_name = db.Column(db.String(200), nullable=False)
    type = db.Column(
        db.Enum(
            ResearchType,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    description = db.Column(db.Text, nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    item = db.relationship("Item", backref=db.backref("artefact_research", lazy="dynamic"))
    stages = db.relationship(
        "ResearchStage",
        backref="research",
        cascade="all, delete-orphan",
        order_by="ResearchStage.stage_number",
    )

    def __init__(self, *args, **kwargs):
        if "public_id" not in kwargs or not kwargs["public_id"]:
            kwargs["public_id"] = generate_public_id()
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Research {self.project_name}>"

    def assign_character(self, character_id):
        """Assign a character to this research project."""
        # Create the CharacterResearch object
        character_research = CharacterResearch(character_id=character_id, research_id=self.id)
        db.session.add(character_research)
        db.session.flush()  # Get the ID for the new CharacterResearch

        # Get the first stage
        first_stage = (
            ResearchStage.query.filter_by(research_id=self.id)
            .order_by(ResearchStage.stage_number)
            .first()
        )

        if first_stage:
            # Create the CharacterResearchStage
            stage_progress = CharacterResearchStage(
                character_research_id=character_research.id, stage_id=first_stage.id
            )
            db.session.add(stage_progress)
            db.session.flush()  # Get the ID for the new CharacterResearchStage

            # Create progress entries for all requirements
            for req in first_stage.unlock_requirements:
                req_progress = CharacterResearchStageRequirement(
                    character_research_stage_id=stage_progress.id, requirement_id=req.id
                )
                db.session.add(req_progress)

            # Set the current stage
            character_research.current_stage_id = first_stage.id

        return character_research

    def stages_to_json(self):
        stages = (
            ResearchStage.query.filter_by(research_id=self.id)
            .order_by(ResearchStage.stage_number)
            .all()
        )
        # Gather all assignees and their current stage numbers
        assignees = self.character_research
        assignee_stage_numbers = []
        for assignee in assignees:
            if assignee.current_stage_id is not None:
                stage = db.session.get(ResearchStage, assignee.current_stage_id)
                if stage:
                    assignee_stage_numbers.append(stage.stage_number)
            else:
                # If current_stage_id is None, the assignee is complete
                # (beyond all stages)
                assignee_stage_numbers.append(float("inf"))
        result = []
        for stage in stages:
            # Not deletable if any assignee is on or beyond this stage
            deletable = all(s > stage.stage_number for s in assignee_stage_numbers)
            result.append(
                {
                    "stage_number": stage.stage_number,
                    "name": stage.name,
                    "description": stage.description,
                    "unlock_requirements": [
                        {
                            "requirement_type": req.requirement_type.value,
                            "science_type": (req.science_type.value if req.science_type else None),
                            "item_type": req.item_type,
                            "exotic_substance_id": req.exotic_substance_id,
                            "amount": req.amount,
                            "sample_tag": (
                                req.sample_tag if req.requirement_type.value == "sample" else None
                            ),
                            "requires_researched": (
                                req.requires_researched
                                if req.requirement_type.value == "sample"
                                else False
                            ),
                        }
                        for req in stage.unlock_requirements
                    ],
                    "deletable": deletable,
                }
            )
        return result


class ResearchStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    research_id = db.Column(db.Integer, db.ForeignKey("research.id"), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("research_id", "stage_number", name="uix_research_stage_number"),
    )

    unlock_requirements = db.relationship(
        "ResearchStageRequirement", backref="stage", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ResearchStage {self.research_id} - {self.stage_number}: {self.name}>"


class ResearchStageRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("research_stage.id"), nullable=False)
    requirement_type = db.Column(
        db.Enum(
            ResearchRequirementType,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    science_type = db.Column(
        db.Enum(
            ScienceType,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    item_type = db.Column(db.String(100), nullable=True)
    exotic_substance_id = db.Column(
        db.Integer, db.ForeignKey("exotic_substances.id"), nullable=True
    )
    sample_tag = db.Column(db.String(100), nullable=True)
    requires_researched = db.Column(db.Boolean, nullable=False, default=False)
    amount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ResearchStageRequirement {self.requirement_type} " f"{self.amount}>"


class CharacterResearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    research_id = db.Column(db.Integer, db.ForeignKey("research.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )
    current_stage_id = db.Column(db.Integer, db.ForeignKey("research_stage.id"), nullable=True)

    character = db.relationship(
        "Character", backref=db.backref("character_research", lazy="dynamic")
    )
    research = db.relationship("Research", backref=db.backref("character_research", lazy="dynamic"))
    progress = db.relationship(
        "CharacterResearchStage",
        backref="character_research",
        cascade="all, delete-orphan",
    )
    current_stage = db.relationship("ResearchStage", foreign_keys=[current_stage_id])

    def __repr__(self):
        return f"<CharacterResearch {self.character_id} - {self.research_id}>"

    def is_complete(self):
        """Check if the research is complete."""
        return self.current_stage_id is None

    def get_current_stage(self):
        """Get the current stage of the research, or None if complete."""
        if not self.current_stage_id:
            return None
        return CharacterResearchStage.query.filter_by(
            character_research_id=self.id, stage_id=self.current_stage_id
        ).first()

    def advance_stage(self):
        """Mark the current stage as complete and create the next stage if it exists."""
        current_stage = self.get_current_stage()
        if not current_stage:
            return None

        # Mark current stage as complete
        current_stage.stage_completed = True

        # Find the next stage
        next_stage = (
            ResearchStage.query.filter(
                ResearchStage.research_id == self.research_id,
                ResearchStage.stage_number > current_stage.stage.stage_number,
            )
            .order_by(ResearchStage.stage_number)
            .first()
        )

        if next_stage:
            # Create new stage progress
            new_stage = CharacterResearchStage(
                character_research_id=self.id, stage_id=next_stage.id
            )
            db.session.add(new_stage)
            db.session.flush()

            # Create progress entries for new stage requirements
            for req in next_stage.unlock_requirements:
                req_progress = CharacterResearchStageRequirement(
                    character_research_stage_id=new_stage.id, requirement_id=req.id
                )
                db.session.add(req_progress)

            # Update current stage
            self.current_stage_id = next_stage.id
            return new_stage
        else:
            # No next stage, mark research as complete
            self.current_stage_id = None
            return None

    def regress_stage(self):
        """Delete the current stage and mark the previous stage as incomplete."""
        current_stage = self.get_current_stage()
        if not current_stage:
            return None

        # Find the previous stage
        prev_stage = (
            ResearchStage.query.filter(
                ResearchStage.research_id == self.research_id,
                ResearchStage.stage_number < current_stage.stage.stage_number,
            )
            .order_by(ResearchStage.stage_number.desc())
            .first()
        )

        if prev_stage:
            # Get the previous stage progress
            prev_stage_progress = CharacterResearchStage.query.filter_by(
                character_research_id=self.id, stage_id=prev_stage.id
            ).first()

            if prev_stage_progress:
                # Mark previous stage as incomplete
                prev_stage_progress.stage_completed = False

                # Reset all requirement progress for the previous stage
                for req_progress in prev_stage_progress.requirement_progress:
                    req_progress.progress = 0

                # Delete current stage and its requirements
                for req_progress in current_stage.requirement_progress:
                    db.session.delete(req_progress)
                db.session.delete(current_stage)

                # Update current stage
                self.current_stage_id = prev_stage.id
                return prev_stage_progress

        return None


class CharacterResearchStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_research_id = db.Column(
        db.Integer, db.ForeignKey("character_research.id"), nullable=False
    )
    stage_id = db.Column(db.Integer, db.ForeignKey("research_stage.id"), nullable=False)
    stage_completed = db.Column(db.Boolean, nullable=False, default=False)

    stage = db.relationship("ResearchStage", backref="character_progress")
    requirement_progress = db.relationship(
        "CharacterResearchStageRequirement",
        backref="stage",
        cascade="all, delete-orphan",
    )

    @property
    def progress_percent(self):
        if not self.requirement_progress:
            return 0
        total = sum(r.requirement.amount for r in self.requirement_progress)
        done = sum(min(r.progress, r.requirement.amount) for r in self.requirement_progress)
        return int((done / total) * 100) if total else 0

    def __repr__(self):
        return f"<CharacterResearchStage {self.character_research_id} - " f"{self.stage_id}>"

    def meets_requirements(self):
        """Check if the stage requirements are met."""
        return all(r.progress >= r.requirement.amount for r in self.requirement_progress)


class CharacterResearchStageRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_research_stage_id = db.Column(
        db.Integer, db.ForeignKey("character_research_stage.id"), nullable=False
    )
    requirement_id = db.Column(
        db.Integer, db.ForeignKey("research_stage_requirement.id"), nullable=False
    )
    progress = db.Column(db.Integer, nullable=False, default=0)

    requirement = db.relationship(
        "ResearchStageRequirement", backref="character_progress", lazy="joined"
    )

    def __repr__(self):
        return (
            f"<CharacterResearchStageRequirement "
            f"{self.character_research_stage_id} - {self.requirement_id}>"
        )
