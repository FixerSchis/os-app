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
    with op.batch_alter_table("character_conditions", schema=None) as batch_op:
        batch_op.alter_column("current_stage", existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table("character_conditions", schema=None) as batch_op:
        batch_op.alter_column("current_stage", existing_type=sa.Integer(), nullable=False)
