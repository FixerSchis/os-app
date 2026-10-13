"""add skill and species rank caps

Revision ID: c1d8e40f6a91
Revises: a7e3c91b4d02
Create Date: 2026-10-13 11:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c1d8e40f6a91"
down_revision = "a7e3c91b4d02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("skill", sa.Column("max_ranks", sa.Integer(), nullable=True))
    op.add_column("ability", sa.Column("rank_caps", sa.String(), nullable=True))


def downgrade():
    op.drop_column("ability", "rank_caps")
    op.drop_column("skill", "max_ranks")
