"""consolidate_granular_permissions_system

Revision ID: a0221b2e8e8e
Revises: bdbea454f874
Create Date: 2025-08-01 16:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a0221b2e8e8e"
down_revision = "bdbea454f874"
branch_labels = None
depends_on = None


def upgrade():
    # Create permissions table
    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create roles table
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_system_role", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create role_permissions association table
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # Add role_id column to user table with foreign key constraint using batch operations
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("role_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_user_role_id", "role", ["role_id"], ["id"])


def downgrade():
    # Remove foreign key and column from user table using batch operations
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_constraint("fk_user_role_id", type_="foreignkey")
        batch_op.drop_column("role_id")

    # Drop association table
    op.drop_table("role_permissions")

    # Drop roles table
    op.drop_table("role")

    # Drop permissions table
    op.drop_table("permission")
