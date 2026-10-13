"""add extra hits per toughness skill

Revision ID: b7c4e91a2f08
Revises: d2e9f51a7b03
Create Date: 2026-10-13 12:55:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "b7c4e91a2f08"
down_revision = "d2e9f51a7b03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "species",
        sa.Column("extra_hits_per_toughness", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_column("species", "extra_hits_per_toughness")
