"""add character sheet values to abilities

Revision ID: a4d8e2c61f37
Revises: f7c2a91e4b18
Create Date: 2026-10-13 14:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "a4d8e2c61f37"
down_revision = "f7c2a91e4b18"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ability", sa.Column("character_sheet_values", sa.String(), nullable=True))


def downgrade():
    op.drop_column("ability", "character_sheet_values")
