"""Add dark_mode_preference to user if missing

Revision ID: add_dark_mode_column
Revises: d45ec0f449e7
Create Date: 2024-07-01

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_dark_mode_column"
down_revision = "d45ec0f449e7"
branch_labels = None
depends_on = None


def column_exists(table_name, column_name, connection):
    insp = sa.inspect(connection)
    return column_name in [col["name"] for col in insp.get_columns(table_name)]


def upgrade():
    conn = op.get_bind()
    if not column_exists("user", "dark_mode_preference", conn):
        op.add_column("user", sa.Column("dark_mode_preference", sa.Boolean(), nullable=True))
        # Optionally set default for existing users
        op.execute("UPDATE user SET dark_mode_preference = 1 " "WHERE dark_mode_preference IS NULL")


def downgrade():
    conn = op.get_bind()
    if column_exists("user", "dark_mode_preference", conn):
        op.drop_column("user", "dark_mode_preference")
