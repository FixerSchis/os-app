"""add summary, effect, and modes to medicaments

Revision ID: e8c4f27a9b61
Revises: d5b2e8f17a3c
Create Date: 2026-10-13 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "e8c4f27a9b61"
down_revision = "d5b2e8f17a3c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("medicaments") as batch_op:
        batch_op.add_column(sa.Column("summary", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("effect", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("modes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("medicaments") as batch_op:
        batch_op.drop_column("modes")
        batch_op.drop_column("effect")
        batch_op.drop_column("summary")
