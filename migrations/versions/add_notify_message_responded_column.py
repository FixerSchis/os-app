"""Add notify_message_responded column to user table

Revision ID: add_notify_message_responded_column
Revises: d45ec0f449e7
Create Date: 2024-07-01

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_notify_message_responded_column"
down_revision = "d45ec0f449e7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("notify_message_responded", sa.Boolean(), nullable=True))
    op.execute("UPDATE user SET notify_message_responded = 1")
    # SQLite doesn't support ALTER COLUMN, so we'll leave it nullable for now
    # The application can handle the default value


def downgrade():
    op.drop_column("user", "notify_message_responded")
