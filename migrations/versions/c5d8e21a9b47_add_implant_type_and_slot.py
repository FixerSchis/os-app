"""add type and slot to implants

Revision ID: c5d8e21a9b47
Revises: f2a6d38c5e17
Create Date: 2026-10-14 12:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c5d8e21a9b47"
down_revision = "f2a6d38c5e17"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cybernetics") as batch_op:
        batch_op.add_column(sa.Column("implant_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("slot", sa.String(length=100), nullable=True))
    op.execute(
        "UPDATE permission SET description = 'Manage implants' WHERE name = 'rules.cybernetics'"
    )


def downgrade():
    op.execute(
        "UPDATE permission SET description = 'Manage cybernetics' "
        "WHERE name = 'rules.cybernetics'"
    )
    with op.batch_alter_table("cybernetics") as batch_op:
        batch_op.drop_column("slot")
        batch_op.drop_column("implant_type")
