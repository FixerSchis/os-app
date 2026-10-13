"""add skills that only earned character points can buy

Revision ID: c3f8a62d9e41
Revises: b7e4c19d3a52
Create Date: 2026-10-13 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c3f8a62d9e41"
down_revision = "b7e4c19d3a52"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "skill",
        sa.Column(
            "earned_points_only",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute("UPDATE skill SET earned_points_only = 1 WHERE skill_type = 'mutation'")


def downgrade():
    op.drop_column("skill", "earned_points_only")
