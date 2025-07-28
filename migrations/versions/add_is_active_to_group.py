"""add_is_active_to_group

Revision ID: add_is_active_to_group
Revises: merge_heads
Create Date: 2025-01-27

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_is_active_to_group"
down_revision = ("add_notify_message_responded_column", "add_dark_mode_column")
branch_labels = None
depends_on = None


def upgrade():
    # Add is_active column to group table
    op.add_column(
        "group", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
    )


def downgrade():
    # Remove is_active column from group table
    op.drop_column("group", "is_active")
