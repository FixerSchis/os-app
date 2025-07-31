"""add_reputation_fields_to_skills_and_abilities

Revision ID: bdbea454f874
Revises: b4d2e379b967
Create Date: 2025-07-31 22:05:39.593390

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bdbea454f874"
down_revision = "b4d2e379b967"
branch_labels = None
depends_on = None


def upgrade():
    # Add reputation fields to skill table
    op.add_column("skill", sa.Column("adds_reputation_faction_id", sa.Integer(), nullable=True))
    op.add_column("skill", sa.Column("adds_reputation_value", sa.Integer(), nullable=True))

    # Add reputation fields to ability table
    op.add_column(
        "ability", sa.Column("starting_reputation_faction_id", sa.Integer(), nullable=True)
    )
    op.add_column("ability", sa.Column("starting_reputation_value", sa.Integer(), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints after table creation
    # The foreign key relationships are handled at the application level


def downgrade():
    # Remove reputation fields from ability table
    op.drop_column("ability", "starting_reputation_value")
    op.drop_column("ability", "starting_reputation_faction_id")

    # Remove reputation fields from skill table
    op.drop_column("skill", "adds_reputation_value")
    op.drop_column("skill", "adds_reputation_faction_id")
