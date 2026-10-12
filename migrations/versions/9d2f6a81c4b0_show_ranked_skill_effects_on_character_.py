"""show ranked skill effects on character sheets

Revision ID: 9d2f6a81c4b0
Revises: b4ddf1331b0f
Create Date: 2026-10-12 15:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d2f6a81c4b0"
down_revision = "b4ddf1331b0f"
branch_labels = None
depends_on = None

_OLD_SKILLS_BLOCK = (
    "       {% for skill in character.skills %}\n"
    "       {{ skill.skill.name }}{% if loop.index != character.skills|length %}, "
    "{% endif %}"
)
_NEW_SKILLS_BLOCK = (
    "       {% for character_skill in character.skills %}\n"
    "       <div><strong>{{ character_skill.skill.name }}"
    "{% if character_skill.skill.can_purchase_multiple %} "
    "{{ character_skill.times_purchased }}{% endif %}</strong>"
    "{% if character_skill.skill.description %}: "
    "{{ character_skill.format_description() }}{% endif %}</div>"
)


def _replace_skills_block(source, target):
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, front_html FROM print_templates WHERE type = :template_type"),
        {"template_type": "character_sheet"},
    ).fetchall()
    for row in rows:
        html = row[1] or ""
        newline = "\r\n" if "\r\n" in html else "\n"
        old_block = source.replace("\n", newline)
        new_block = target.replace("\n", newline)
        if old_block not in html:
            continue
        connection.execute(
            sa.text("UPDATE print_templates SET front_html = :html WHERE id = :template_id"),
            {"html": html.replace(old_block, new_block, 1), "template_id": row[0]},
        )


def upgrade():
    _replace_skills_block(_OLD_SKILLS_BLOCK, _NEW_SKILLS_BLOCK)


def downgrade():
    _replace_skills_block(_NEW_SKILLS_BLOCK, _OLD_SKILLS_BLOCK)
