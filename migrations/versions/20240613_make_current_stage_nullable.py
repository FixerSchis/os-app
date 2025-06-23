"""Make current_stage nullable in character_conditions

Revision ID: 20240613_make_current_stage_nullable
Revises: add_pack_data_to_group
Create Date: 2024-06-13

"""

import sqlalchemy as sa
from alembic import op

revision = "20240613_make_current_stage_nullable"
down_revision = "add_pack_data_to_group"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "character_conditions", "current_stage", existing_type=sa.Integer(), nullable=True
    )


def downgrade():
    op.alter_column(
        "character_conditions", "current_stage", existing_type=sa.Integer(), nullable=False
    )
