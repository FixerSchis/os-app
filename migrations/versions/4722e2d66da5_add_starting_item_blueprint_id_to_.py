"""add_starting_item_blueprint_id_to_ability

Revision ID: 4722e2d66da5
Revises: 9f6883fe1a5d
Create Date: 2025-07-28 20:53:20.852868

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4722e2d66da5"
down_revision = "9f6883fe1a5d"
branch_labels = None
depends_on = None


def upgrade():
    # Add starting_item_blueprint_id column to ability table
    op.add_column("ability", sa.Column("starting_item_blueprint_id", sa.Integer(), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints after table creation
    # The foreign key relationship is handled at the application level


def downgrade():
    # Remove starting_item_blueprint_id column from ability table
    op.drop_column("ability", "starting_item_blueprint_id")
