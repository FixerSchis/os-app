"""widen wiki section restriction value

Revision ID: f3b7c91a2e64
Revises: 9d2f6a81c4b0
Create Date: 2026-10-12 17:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3b7c91a2e64"
down_revision = "9d2f6a81c4b0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("wiki_section", schema=None) as batch_op:
        batch_op.alter_column(
            "restriction_value",
            existing_type=sa.String(length=100),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("wiki_section", schema=None) as batch_op:
        batch_op.alter_column(
            "restriction_value",
            existing_type=sa.Text(),
            type_=sa.String(length=100),
            existing_nullable=True,
        )
