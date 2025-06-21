"""Merge heads

Revision ID: merge_heads
Revises: add_notify_message_responded_column, add_dark_mode_column
Create Date: 2024-12-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_heads"
down_revision = ("add_notify_message_responded_column", "add_dark_mode_column")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass 