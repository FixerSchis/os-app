"""add any-of and distinct skill requirements

Revision ID: d2e9f51a7b03
Revises: c1d8e40f6a91
Create Date: 2026-10-13 12:05:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "d2e9f51a7b03"
down_revision = "c1d8e40f6a91"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("skill", sa.Column("required_any_skills", sa.String(), nullable=True))
    op.add_column("skill", sa.Column("distinct_requirements", sa.String(), nullable=True))


def downgrade():
    op.drop_column("skill", "distinct_requirements")
    op.drop_column("skill", "required_any_skills")
