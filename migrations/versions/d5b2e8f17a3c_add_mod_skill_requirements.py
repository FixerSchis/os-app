"""add skill requirements and skill grants to mods

Revision ID: d5b2e8f17a3c
Revises: c3f8a62d9e41
Create Date: 2026-10-13 19:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "d5b2e8f17a3c"
down_revision = "c3f8a62d9e41"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("mods") as batch_op:
        batch_op.add_column(sa.Column("required_skills", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("granted_by_skills", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("mods") as batch_op:
        batch_op.drop_column("granted_by_skills")
        batch_op.drop_column("required_skills")
