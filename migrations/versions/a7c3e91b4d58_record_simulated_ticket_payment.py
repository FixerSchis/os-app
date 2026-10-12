"""record simulated ticket payment

Revision ID: a7c3e91b4d58
Revises: f3b7c91a2e64
Create Date: 2026-10-12 17:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c3e91b4d58"
down_revision = "f3b7c91a2e64"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("event_tickets", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "payment_simulated",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("event_tickets", schema=None) as batch_op:
        batch_op.drop_column("payment_simulated")
