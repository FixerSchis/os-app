"""merge_migration_conflicts

Revision ID: b4a1290dd816
Revises: 20240613_make_current_stage_nullable, df727425156a, add_new_character_audit_actions
Create Date: 2025-06-23 22:55:39.311025

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4a1290dd816"
down_revision = (
    "20240613_make_current_stage_nullable",
    "df727425156a",
    "add_new_character_audit_actions",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
