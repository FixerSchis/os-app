"""add trigger-only conditions, stage sheet values, and starting conditions

Revision ID: b7e4c19d3a52
Revises: a4d8e2c61f37
Create Date: 2026-10-13 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "b7e4c19d3a52"
down_revision = "a4d8e2c61f37"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "conditions",
        sa.Column(
            "progresses_naturally",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column("conditions", sa.Column("stage_sheet_values", sa.String(), nullable=True))
    op.add_column("ability", sa.Column("starting_condition_id", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("ability", "starting_condition_id")
    op.drop_column("conditions", "stage_sheet_values")
    op.drop_column("conditions", "progresses_naturally")
