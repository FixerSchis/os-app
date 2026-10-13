"""add first-skill pair grants

Revision ID: a7e3c91b4d02
Revises: d8b1e64c0a27
Create Date: 2026-10-13 11:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "a7e3c91b4d02"
down_revision = "d8b1e64c0a27"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ability", sa.Column("skill_pairs", sa.String(), nullable=True))
    op.add_column("character", sa.Column("skill_pair_grants", sa.String(), nullable=True))


def downgrade():
    op.drop_column("character", "skill_pair_grants")
    op.drop_column("ability", "skill_pairs")
