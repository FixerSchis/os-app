"""remove_old_roles_column

Revision ID: remove_old_roles_column
Revises: a0221b2e8e8e
Create Date: 2025-08-01 22:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "remove_old_roles_column"
down_revision = "a0221b2e8e8e"
branch_labels = None
depends_on = None


def upgrade():
    # Remove the old roles column from user table using batch operations
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("roles")


def downgrade():
    # Add back the old roles column (for rollback purposes)
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("roles", sa.String(length=255), nullable=True))
