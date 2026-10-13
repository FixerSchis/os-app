"""add skill bans

Revision ID: e3a9c71b5d14
Revises: c8e1a47b2d90
Create Date: 2026-10-13 13:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "e3a9c71b5d14"
down_revision = "c8e1a47b2d90"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ability", sa.Column("banned_skills", sa.String(), nullable=True))


def downgrade():
    op.drop_column("ability", "banned_skills")
