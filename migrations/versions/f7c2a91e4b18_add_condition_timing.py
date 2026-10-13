"""add condition timing and shared rule tags

Revision ID: f7c2a91e4b18
Revises: e3a9c71b5d14
Create Date: 2026-10-13 14:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "f7c2a91e4b18"
down_revision = "e3a9c71b5d14"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rule_tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "condition_rule_tags",
        sa.Column("condition_id", sa.Integer(), nullable=False),
        sa.Column("rule_tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["condition_id"], ["conditions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_tag_id"], ["rule_tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("condition_id", "rule_tag_id"),
    )
    op.create_table(
        "ability_rule_tags",
        sa.Column("ability_id", sa.Integer(), nullable=False),
        sa.Column("rule_tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ability_id"], ["ability.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_tag_id"], ["rule_tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ability_id", "rule_tag_id"),
    )
    op.create_table(
        "skill_rule_tags",
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("rule_tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skill.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_tag_id"], ["rule_tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("skill_id", "rule_tag_id"),
    )
    op.add_column("ability", sa.Column("condition_progress_rate", sa.Float(), nullable=True))
    op.add_column("skill", sa.Column("condition_progress_rate", sa.Float(), nullable=True))
    with op.batch_alter_table("character_conditions") as batch:
        batch.alter_column(
            "current_duration",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("character_conditions") as batch:
        batch.alter_column(
            "current_duration",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
    op.drop_column("skill", "condition_progress_rate")
    op.drop_column("ability", "condition_progress_rate")
    op.drop_table("skill_rule_tags")
    op.drop_table("ability_rule_tags")
    op.drop_table("condition_rule_tags")
    op.drop_table("rule_tag")
