from models.extensions import db


class GlobalSettings(db.Model):
    __tablename__ = "global_settings"

    id = db.Column(db.Integer, primary_key=True)
    character_income_ec = db.Column(db.Integer, nullable=False, default=30)
    group_income_contribution = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now()
    )

    def __repr__(self):
        return (
            f"<GlobalSettings character_income_ec={self.character_income_ec} "
            f"group_contribution={self.group_income_contribution}>"
        )

    @classmethod
    def create_default_settings(cls):
        """Create default global settings."""
        return cls(character_income_ec=30, group_income_contribution=30)
