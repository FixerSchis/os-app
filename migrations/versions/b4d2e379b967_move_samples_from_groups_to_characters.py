"""move_samples_from_groups_to_characters

Revision ID: b4d2e379b967
Revises: 4f1a135f8b36
Create Date: 2025-07-31 19:13:25.965484

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "b4d2e379b967"
down_revision = "4f1a135f8b36"
branch_labels = None
depends_on = None


def upgrade():
    # Create the character_samples association table
    op.create_table(
        "character_samples",
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["character.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sample_id"],
            ["sample.id"],
        ),
        sa.PrimaryKeyConstraint("character_id", "sample_id"),
    )

    # Migrate existing group samples to character samples
    # For each group, assign its samples to all characters in that group
    connection = op.get_bind()
    # Get all groups that have samples
    groups_with_samples = connection.execute(
        text("SELECT DISTINCT group_id FROM sample WHERE group_id IS NOT NULL")
    ).fetchall()

    for (group_id,) in groups_with_samples:
        # Get all characters in this group
        characters_in_group = connection.execute(
            text("SELECT id FROM character WHERE group_id = :group_id"),
            {"group_id": group_id},
        ).fetchall()

        # Get all samples for this group
        samples_in_group = connection.execute(
            text("SELECT id FROM sample WHERE group_id = :group_id"),
            {"group_id": group_id},
        ).fetchall()

        # Assign each sample to each character in the group
        for (character_id,) in characters_in_group:
            for (sample_id,) in samples_in_group:
                connection.execute(
                    text(
                        "INSERT INTO character_samples (character_id, sample_id) "
                        "VALUES (:character_id, :sample_id)"
                    ),
                    {"character_id": character_id, "sample_id": sample_id},
                )


def downgrade():
    # Remove the character_samples association table
    op.drop_table("character_samples")
