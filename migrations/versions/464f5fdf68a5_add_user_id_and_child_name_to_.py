"""Add user_id and child_name to EventTicket, make character_id nullable

Revision ID: 464f5fdf68a5
Revises: merge_heads
Create Date: 2025-06-21 23:16:16.953359

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "464f5fdf68a5"
down_revision = "merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Check if columns already exist to avoid duplicate column errors
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("event_tickets")]

    # Add user_id column if it doesn't exist
    if "user_id" not in columns:
        with op.batch_alter_table("event_tickets", schema=None) as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))

    # Add child_name column if it doesn't exist
    if "child_name" not in columns:
        with op.batch_alter_table("event_tickets", schema=None) as batch_op:
            batch_op.add_column(sa.Column("child_name", sa.String(length=255), nullable=True))

    # Make character_id nullable if it isn't already
    if "character_id" in columns:
        with op.batch_alter_table("event_tickets", schema=None) as batch_op:
            batch_op.alter_column("character_id", existing_type=sa.INTEGER(), nullable=True)

    # Update ticket_type enum if needed
    with op.batch_alter_table("event_tickets", schema=None) as batch_op:
        batch_op.alter_column(
            "ticket_type",
            existing_type=sa.VARCHAR(length=16),
            type_=sa.Enum(
                "adult",
                "child_12_15",
                "child_7_11",
                "child_under_7",
                "crew",
                name="tickettype",
                native_enum=False,
            ),
            existing_nullable=False,
        )

    # Create foreign key if it doesn't exist
    try:
        with op.batch_alter_table("event_tickets", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_event_tickets_user_id_user", "user", ["user_id"], ["id"]
            )
    except Exception:  # nosec
        # Foreign key might already exist
        pass

    # Backfill user_id for existing tickets based on character_id
    op.execute(
        """
        UPDATE event_tickets
        SET user_id = (
            SELECT user.id FROM user
            JOIN character ON character.id = event_tickets.character_id
            WHERE character.user_id = user.id
        )
        WHERE character_id IS NOT NULL AND user_id IS NULL
    """
    )

    # Handle any tickets that couldn't be backfilled (orphaned tickets)
    # Delete tickets that have no user_id after backfill
    op.execute(
        """
        DELETE FROM event_tickets
        WHERE user_id IS NULL
    """
    )

    # Now set user_id to non-nullable if it isn't already
    with op.batch_alter_table("event_tickets", schema=None) as batch_op:
        batch_op.alter_column("user_id", nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("event_tickets", schema=None) as batch_op:
        batch_op.drop_constraint("fk_event_tickets_user_id_user", type_="foreignkey")
        batch_op.alter_column(
            "ticket_type",
            existing_type=sa.Enum(
                "adult",
                "child_12_15",
                "child_7_11",
                "child_under_7",
                "crew",
                name="tickettype",
                native_enum=False,
            ),
            type_=sa.VARCHAR(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column("character_id", existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column("child_name")
        batch_op.drop_column("user_id")

    # ### end Alembic commands ###
