"""add skill group name

Revision ID: c4e8a17d2b90
Revises: a7c3e91b4d58
Create Date: 2026-10-13 09:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c4e8a17d2b90"
down_revision = "a7c3e91b4d58"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("skill", sa.Column("group_name", sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column("skill", "group_name")
