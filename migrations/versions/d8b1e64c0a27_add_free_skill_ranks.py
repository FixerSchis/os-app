"""add free skill ranks and starting skill choices

Revision ID: d8b1e64c0a27
Revises: c4e8a17d2b90
Create Date: 2026-10-13 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "d8b1e64c0a27"
down_revision = "c4e8a17d2b90"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "character_skill",
        sa.Column("free_ranks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("ability", sa.Column("starting_skill_choices", sa.String(), nullable=True))


def downgrade():
    op.drop_column("ability", "starting_skill_choices")
    op.drop_column("character_skill", "free_ranks")
