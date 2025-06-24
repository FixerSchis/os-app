"""Fix partial migration - handle existing tables

Revision ID: d09a1b96022b
Revises: dcfca26159fc
Create Date: 2025-06-24 15:29:47.508089

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "d09a1b96022b"
down_revision = "dcfca26159fc"
branch_labels = None
depends_on = None


def upgrade():
    # Check which tables already exist and create only the missing ones
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()

    # Create global_settings table if it doesn't exist
    if "global_settings" not in existing_tables:
        op.create_table(
            "global_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("character_income_ec", sa.Integer(), nullable=False),
            sa.Column("group_income_contribution", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Create group_types table if it doesn't exist
    if "group_types" not in existing_tables:
        op.create_table(
            "group_types",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("income_items", sa.String(), nullable=True),
            sa.Column("income_items_discount", sa.Float(), nullable=False),
            sa.Column("income_substances", sa.Boolean(), nullable=False),
            sa.Column("income_substance_cost", sa.Integer(), nullable=False),
            sa.Column("income_medicaments", sa.Boolean(), nullable=False),
            sa.Column("income_medicament_cost", sa.Integer(), nullable=False),
            sa.Column("income_distribution", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    # Drop role and user_roles tables if they exist
    if "user_roles" in existing_tables:
        op.drop_table("user_roles")
    if "role" in existing_tables:
        op.drop_table("role")

    # Add columns to existing tables if they don't exist
    if "ability" in existing_tables:
        ability_columns = [col["name"] for col in inspector.get_columns("ability")]
        if "additional_group_income" not in ability_columns:
            with op.batch_alter_table("ability", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column("additional_group_income", sa.Integer(), nullable=True)
                )

    if "character" in existing_tables:
        character_columns = [col["name"] for col in inspector.get_columns("character")]
        if "pack_complete" not in character_columns:
            with op.batch_alter_table("character", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "pack_complete", sa.Boolean(), nullable=False, server_default=sa.false()
                    )
                )
        if "character_pack" in character_columns:
            # Check if character_pack is JSON type and convert to String
            character_pack_col = next(
                col for col in inspector.get_columns("character") if col["name"] == "character_pack"
            )
            if "JSON" in str(character_pack_col["type"]):
                with op.batch_alter_table("character", schema=None) as batch_op:
                    batch_op.alter_column(
                        "character_pack",
                        existing_type=sa.JSON(),
                        type_=sa.String(),
                        existing_nullable=True,
                    )

    if "character_audit_log" in existing_tables:
        audit_log_columns = [col["name"] for col in inspector.get_columns("character_audit_log")]
        if "action" in audit_log_columns:
            action_col = next(
                col
                for col in inspector.get_columns("character_audit_log")
                if col["name"] == "action"
            )
            if "VARCHAR" in str(action_col["type"]):
                with op.batch_alter_table("character_audit_log", schema=None) as batch_op:
                    batch_op.alter_column(
                        "action",
                        existing_type=sa.VARCHAR(length=17),
                        type_=sa.Enum(
                            "create",
                            "edit",
                            "status_change",
                            "skill_change",
                            "reputation_change",
                            "funds_added",
                            "funds_removed",
                            "funds_set",
                            "group_joined",
                            "group_left",
                            "condition_change",
                            "cybernetics_change",
                            name="characterauditaction",
                            native_enum=False,
                        ),
                        existing_nullable=False,
                    )

    if "character_conditions" in existing_tables:
        conditions_columns = [col["name"] for col in inspector.get_columns("character_conditions")]
        if "current_stage" in conditions_columns:
            current_stage_col = next(
                col
                for col in inspector.get_columns("character_conditions")
                if col["name"] == "current_stage"
            )
            if not current_stage_col["nullable"]:
                with op.batch_alter_table("character_conditions", schema=None) as batch_op:
                    batch_op.alter_column(
                        "current_stage", existing_type=sa.INTEGER(), nullable=True
                    )

    if "events" in existing_tables:
        events_columns = [col["name"] for col in inspector.get_columns("events")]
        if "booking_deadline" not in events_columns:
            # Add booking_deadline as nullable first
            with op.batch_alter_table("events", schema=None) as batch_op:
                batch_op.add_column(sa.Column("booking_deadline", sa.DateTime(), nullable=True))

            # Update existing events to set booking_deadline to early_booking_deadline + 10 days
            connection = op.get_bind()
            events = connection.execute(
                sa.text(
                    "SELECT id, early_booking_deadline FROM events WHERE booking_deadline IS NULL"
                )
            )
            for event in events:
                from datetime import datetime, timedelta

                early_deadline = datetime.fromisoformat(
                    event.early_booking_deadline.replace("Z", "+00:00")
                )
                booking_deadline = early_deadline + timedelta(days=10)
                connection.execute(
                    sa.text(
                        "UPDATE events SET booking_deadline = :booking_deadline "
                        "WHERE id = :event_id"
                    ),
                    {"booking_deadline": booking_deadline.isoformat(), "event_id": event.id},
                )

            # Now make the column NOT NULL
            with op.batch_alter_table("events", schema=None) as batch_op:
                batch_op.alter_column("booking_deadline", nullable=False)

    if "group" in existing_tables:
        group_columns = [col["name"] for col in inspector.get_columns("group")]
        if "group_type_id" not in group_columns:
            with op.batch_alter_table("group", schema=None) as batch_op:
                batch_op.add_column(sa.Column("group_type_id", sa.Integer(), nullable=False))
        if "group_pack" not in group_columns:
            with op.batch_alter_table("group", schema=None) as batch_op:
                batch_op.add_column(sa.Column("group_pack", sa.String(), nullable=True))
        if "pack_complete" not in group_columns:
            with op.batch_alter_table("group", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "pack_complete", sa.Boolean(), nullable=False, server_default=sa.false()
                    )
                )

        # Add foreign key if it doesn't exist
        if "group_types" in existing_tables:
            foreign_keys = inspector.get_foreign_keys("group")
            fk_exists = any(fk["referred_table"] == "group_types" for fk in foreign_keys)
            if not fk_exists:
                with op.batch_alter_table("group", schema=None) as batch_op:
                    batch_op.create_foreign_key(
                        "fk_group_group_type_id", "group_types", ["group_type_id"], ["id"]
                    )

        # Drop old columns if they exist
        if "pack_data" in group_columns:
            with op.batch_alter_table("group", schema=None) as batch_op:
                batch_op.drop_column("pack_data")
        if "type" in group_columns:
            with op.batch_alter_table("group", schema=None) as batch_op:
                batch_op.drop_column("type")


def downgrade():
    # This is a complex migration that handles partial state
    # Downgrade would be complex and potentially destructive
    # For now, we'll leave it empty to prevent accidental data loss
    pass
