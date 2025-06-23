"""Add pack_data column to group table

Revision ID: add_pack_data_to_group
Revises: merge_heads
Create Date: 2024-12-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_pack_data_to_group"
down_revision = "merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    # Add pack_data column to group table
    op.add_column("group", sa.Column("pack_data", sa.JSON(), nullable=True))


def downgrade():
    # Remove pack_data column from group table
    op.drop_column("group", "pack_data")
