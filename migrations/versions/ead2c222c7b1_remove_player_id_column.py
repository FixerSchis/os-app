"""remove_player_id_column

Revision ID: ead2c222c7b1
Revises: d09a1b96022b
Create Date: 2025-06-25 19:00:46.768628

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ead2c222c7b1"
down_revision = "d09a1b96022b"
branch_labels = None
depends_on = None


def upgrade():
    # Get connection and inspector
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if the user table exists
    if "user" not in inspector.get_table_names():
        print("User table does not exist, skipping migration")
        return

    # Check if player_id column exists
    columns = [col["name"] for col in inspector.get_columns("user")]
    if "player_id" not in columns:
        print("player_id column does not exist, skipping removal")
        return

    print("Removing player_id column from user table...")

    # Check if player_id unique constraint exists
    constraints = inspector.get_unique_constraints("user")
    player_id_constraint = None
    for constraint in constraints:
        if "player_id" in constraint["column_names"]:
            player_id_constraint = constraint["name"]
            break

    # Remove unique constraint if it exists
    if player_id_constraint:
        try:
            op.drop_constraint(player_id_constraint, "user", type_="unique")
            print(f"Removed unique constraint: {player_id_constraint}")
        except Exception as e:
            print(f"Warning: Could not remove constraint {player_id_constraint}: {e}")

    # Remove the player_id column
    try:
        with op.batch_alter_table("user") as batch_op:
            batch_op.drop_column("player_id")
        print("Removed player_id column from user table")
    except Exception as e:
        print(f"Warning: Could not remove player_id column: {e}")
        print("Column may have already been removed")

    print("Migration completed successfully!")


def downgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "user" not in inspector.get_table_names():
        print("User table does not exist, cannot add player_id column")
        return
    columns = [col["name"] for col in inspector.get_columns("user")]
    if "player_id" in columns:
        print("player_id column already exists, skipping addition")
        return
    # Add the player_id column and unique constraint using
    # batch_alter_table for SQLite compatibility
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("player_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_user_player_id", ["player_id"])
    print("Added player_id column and unique constraint back to user table")
