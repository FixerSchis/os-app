"""add_character_background_fields

Revision ID: 9f6883fe1a5d
Revises: e43a060cc670
Create Date: 2025-07-28 15:47:05.696966

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f6883fe1a5d"
down_revision = "e43a060cc670"
branch_labels = None
depends_on = None


def upgrade():
    # Add background fields to character table
    op.add_column("character", sa.Column("background", sa.Text(), nullable=True))
    op.add_column("character", sa.Column("goals", sa.Text(), nullable=True))
    op.add_column("character", sa.Column("concept", sa.Text(), nullable=True))

    # Create character_backgrounds table
    op.create_table(
        "character_backgrounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("background", sa.Text(), nullable=True),
        sa.Column("goals", sa.Text(), nullable=True),
        sa.Column("concept", sa.Text(), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, default=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["character.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    # Drop character_backgrounds table
    op.drop_table("character_backgrounds")

    # Remove background fields from character table
    op.drop_column("character", "concept")
    op.drop_column("character", "goals")
    op.drop_column("character", "background")
