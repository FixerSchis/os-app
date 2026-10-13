"""add character abilities

Revision ID: c8e1a47b2d90
Revises: b7c4e91a2f08
Create Date: 2026-10-13 13:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c8e1a47b2d90"
down_revision = "b7c4e91a2f08"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ability") as batch_op:
        batch_op.alter_column("species_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("character_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_ability_character_id",
            "character",
            ["character_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_check_constraint(
            "ck_ability_one_owner",
            "(species_id IS NOT NULL AND character_id IS NULL) OR "
            "(species_id IS NULL AND character_id IS NOT NULL)",
        )


def downgrade():
    with op.batch_alter_table("ability") as batch_op:
        batch_op.drop_constraint("ck_ability_one_owner", type_="check")
        batch_op.drop_constraint("fk_ability_character_id", type_="foreignkey")
        batch_op.drop_column("character_id")
        batch_op.alter_column("species_id", existing_type=sa.Integer(), nullable=False)
