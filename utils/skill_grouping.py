"""Group catalogue skills into ordered sections and prerequisite trees."""

import re
from collections import defaultdict

SKILL_SECTIONS_START_OPEN = (
    "combat",
    "professional",
    "spaceflight",
    "reputation",
)

SKILL_SECTION_ORDER = SKILL_SECTIONS_START_OPEN + (
    "discipline",
    "psionic",
    "mutation",
    "devotion",
    "standard_program",
    "advanced_program",
)

SKILL_SECTION_LABELS = {
    "combat": "Combat",
    "professional": "Professional",
    "spaceflight": "Spaceflight",
    "reputation": "Reputation",
    "discipline": "Discipline",
    "psionic": "Psionic",
    "mutation": "Mutation",
    "devotion": "Devotion",
    "standard_program": "Standard Programs",
    "advanced_program": "Advanced Programs",
    "UNCATEGORIZED": "Uncategorized",
}

_RANK_SUFFIX = re.compile(r"\s\[(Basic|Advanced|\d+)\]\s*$")
_SHALLOW_TREE_LEVELS = 3


def skill_family_name(name):
    """Drop a rank suffix so a tree can be titled from its root skill."""
    return _RANK_SUFFIX.sub("", name).strip()


def group_skills_for_display(skills):
    """Return skill sections in catalogue order, each with trees and loose skills."""
    by_type = defaultdict(list)
    for skill in skills:
        by_type[skill.skill_type or "UNCATEGORIZED"].append(skill)

    sections = []
    for skill_type in sorted(by_type, key=_section_sort_key):
        standalone, trees = _split_type(by_type[skill_type], skill_type)
        standalone, trees = _inline_shallow_trees(standalone, trees)
        standalone, trees = _promote_lone_tree(standalone, trees)
        sections.append(
            {
                "key": skill_type,
                "label": _section_label(skill_type),
                "open": skill_type in SKILL_SECTIONS_START_OPEN,
                "standalone": standalone,
                "trees": trees,
            }
        )
    return sections


def _inline_shallow_trees(standalone, trees):
    """Keep a short prerequisite chain in the section list, indented by depth."""
    blocks = [(row["skill"].name.lower(), [row]) for row in standalone]
    kept = []
    for tree in trees:
        if _tree_levels(tree) <= _SHALLOW_TREE_LEVELS:
            blocks.append((_tree_sort_name(tree), tree["skills"]))
        else:
            kept.append({**tree, "skills": _flat_rows(tree["skills"])})
    blocks.sort(key=lambda block: block[0])
    rows = [row for _name, block_rows in blocks for row in block_rows]
    return rows, kept


def _flat_rows(rows):
    return [{"skill": row["skill"], "depth": 0} for row in rows]


def _tree_levels(tree):
    return max(row["depth"] for row in tree["skills"]) + 1


def _tree_sort_name(tree):
    return tree["skills"][0]["skill"].name.lower()


def _promote_lone_tree(standalone, trees):
    """Show a section's only tree directly when nothing else sits beside it."""
    if standalone or len(trees) != 1:
        return standalone, trees
    return _flat_rows(trees[0]["skills"]), []


def _section_sort_key(skill_type):
    if skill_type in SKILL_SECTION_ORDER:
        return (0, SKILL_SECTION_ORDER.index(skill_type))
    if skill_type == "UNCATEGORIZED":
        return (2, skill_type)
    return (1, skill_type)


def _section_label(skill_type):
    return SKILL_SECTION_LABELS.get(skill_type, skill_type.replace("_", " ").title())


def _split_type(skills, skill_type):
    named = defaultdict(list)
    ungrouped = []
    for skill in skills:
        group_name = (getattr(skill, "group_name", None) or "").strip()
        if group_name:
            named[group_name].append(skill)
        else:
            ungrouped.append(skill)

    standalone, trees = _prerequisite_trees(ungrouped)
    for title, members in named.items():
        trees.append(
            {
                "id": _group_tree_id(skill_type, title),
                "title": title,
                "skills": _order_members(members),
            }
        )
    trees.sort(key=lambda tree: tree["title"].lower())
    return standalone, trees


def _prerequisite_trees(skills):
    standalone = []
    trees = []
    for root, rows in _rooted_rows(skills):
        if len(rows) == 1:
            standalone.append(rows[0])
        else:
            trees.append(
                {
                    "id": root.id,
                    "title": skill_family_name(root.name),
                    "skills": rows,
                }
            )
    return standalone, trees


def _order_members(skills):
    rows = []
    for _root, rooted in _rooted_rows(skills):
        rows.extend(rooted)
    return rows


def _rooted_rows(skills):
    by_id = {skill.id: skill for skill in skills}
    children = defaultdict(list)
    roots = []
    for skill in skills:
        parent_id = skill.required_skill_id
        if parent_id in by_id:
            children[parent_id].append(skill)
        else:
            roots.append(skill)
    rooted = []
    for root in sorted(roots, key=lambda skill: skill.name.lower()):
        rooted.append((root, _walk(root, children, 0)))
    return rooted


def _group_tree_id(skill_type, title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"group-{skill_type}-{slug}"


def _walk(skill, children, depth):
    rows = [{"skill": skill, "depth": depth}]
    ordered = sorted(children.get(skill.id, []), key=lambda child: _child_sort_key(skill, child))
    for child in ordered:
        rows.extend(_walk(child, children, depth + 1))
    return rows


def _child_sort_key(parent, child):
    same_line = skill_family_name(child.name) != skill_family_name(parent.name)
    return (same_line, _rank_order(child.name), child.name.lower())


def _rank_order(name):
    match = _RANK_SUFFIX.search(name)
    if not match:
        return 0
    token = match.group(1)
    if token == "Basic":  # nosec B105
        return 0
    if token == "Advanced":  # nosec B105
        return 1
    return int(token)
