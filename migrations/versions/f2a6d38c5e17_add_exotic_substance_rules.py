"""add used on, effect, and duration to exotic substances

Revision ID: f2a6d38c5e17
Revises: d5b2e8f17a3c
Create Date: 2026-10-13 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "f2a6d38c5e17"
down_revision = "d5b2e8f17a3c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exotic_substances") as batch_op:
        batch_op.add_column(sa.Column("used_on", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("effect", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("duration", sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table("exotic_substances") as batch_op:
        batch_op.drop_column("duration")
        batch_op.drop_column("effect")
        batch_op.drop_column("used_on")
