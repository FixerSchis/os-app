"""Merge reputation briefings heads

Revision ID: merge_reputation_briefings_heads
Revises: add_description_to_mods, add_reputation_briefings_tables
Create Date: 2025-01-27 10:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_reputation_briefings_heads"
down_revision = ("add_description_to_mods", "add_reputation_briefings_tables")
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no changes needed
    pass


def downgrade():
    # This is a merge migration - no changes needed
    pass
