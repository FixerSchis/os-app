"""Add new character audit actions

Revision ID: add_new_character_audit_actions
Revises: merge_heads
Create Date: 2024-12-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_new_character_audit_actions"
down_revision = "merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    # This migration was created to resolve a missing migration issue
    # The character audit actions already exist in the enum
    pass


def downgrade():
    pass
