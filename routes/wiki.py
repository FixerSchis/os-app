import uuid
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
)
from flask_login import AnonymousUserMixin, login_required, current_user
from models.wiki import (
    db,
    WikiPage,
    WikiImage,
    WikiSection,
    WikiPageVersion,
    SectionRestrictionType,
    WikiPageVersionStatus,
    WikiChangeLog,
    WikiTag,
)
from models.enums import Role
from models import Faction, Species, Skill, CharacterTag, Cybernetic
import io
import difflib
import json

from utils.email import send_wiki_published_notification_to_all

wiki_bp = Blueprint("wiki", __name__)


def get_latest_published_version(page):
    return (
        page.versions.filter_by(status=WikiPageVersionStatus.PUBLISHED)
        .order_by(None)
        .order_by(WikiPageVersion.version_number.desc())
        .first()
    )


def get_latest_version(page):
    return (
        page.versions.order_by(None)
        .order_by(WikiPageVersion.version_number.desc())
        .first()
    )


def get_pending_version(page, current_user):
    latest_version = get_latest_version(page)
    if latest_version and latest_version.status == WikiPageVersionStatus.PUBLISHED:
        # Create a new PENDING version
        new_version = WikiPageVersion(
            page_slug=page.slug,
            version_number=latest_version.version_number + 1,
            status=WikiPageVersionStatus.PENDING,
            created_by=current_user.id,
        )
        db.session.add(new_version)
        db.session.flush()
        # Copy sections from the latest published version
        for section in latest_version.sections:
            new_section = WikiSection(
                id=section.id,
                version_id=new_version.id,
                title=section.title,
                content=section.content,
                order=section.order,
                restriction_type=section.restriction_type,
                restriction_value=section.restriction_value,
            )
            db.session.add(new_section)
        db.session.commit()
        return new_version
    else:
        return latest_version


def save_wiki_version(data, version):
    # Save sections
    if "sections" in data:
        existing_sections = {s.id: s for s in version.sections}
        for section_data in data["sections"]:
            restriction_type = section_data.get("restriction_type")
            restriction_value = section_data.get("restriction_value")
            # Robustly handle all list-based restriction types
            if restriction_type:
                if not restriction_value or restriction_value in ("null", "[]", ""):
                    values = []
                else:
                    try:
                        values = json.loads(restriction_value)
                        if not isinstance(values, list):
                            values = [values]
                    except Exception:
                        values = [restriction_value]
                # For tag, handle tag creation
                if restriction_type == "tag":
                    tag_ids = []
                    for tag_val in values:
                        if str(tag_val).isdigit():
                            tag_ids.append(int(tag_val))
                        else:
                            tag = CharacterTag.query.filter(CharacterTag.name.ilike(tag_val)).first()
                            if not tag:
                                tag = CharacterTag(name=tag_val)
                                db.session.add(tag)
                                db.session.flush()
                            tag_ids.append(tag.id)
                    restriction_value = json.dumps(tag_ids)
                else:
                    restriction_value = json.dumps(
                        [int(v) for v in values if str(v).isdigit()]
                    )
            if section_data.get("id"):
                section = existing_sections.get(section_data["id"])
                if section:
                    section.title = section_data.get("title")
                    section.content = section_data["content"]
                    section.order = section_data["order"]
                    section.restriction_type = (
                        SectionRestrictionType(section_data["restriction_type"])
                        if section_data.get("restriction_type")
                        else None
                    )
                    section.restriction_value = restriction_value
                    existing_sections.pop(section_data["id"])
            else:
                section = WikiSection(
                    id=str(uuid.uuid4()),
                    version_id=version.id,
                    title=section_data.get("title"),
                    content=section_data["content"],
                    order=section_data["order"],
                    restriction_type=(
                        SectionRestrictionType(section_data["restriction_type"])
                        if section_data.get("restriction_type")
                        else None
                    ),
                    restriction_value=restriction_value,
                )
                db.session.add(section)
        for section in existing_sections.values():
            db.session.delete(section)
    db.session.commit()


def build_wiki_tree(pages):
    tree = {}
    for page in pages:
        parts = page['slug'].split('/')
        node = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if '_pages' not in node:
                    node['_pages'] = []
                node['_pages'].append(page)
            else:
                if part not in node:
                    node[part] = {}
                node = node[part]
    return tree


@wiki_bp.route("/")
@wiki_bp.route("/list")
def wiki_list():
    pages = WikiPage.query.order_by(WikiPage.title).all()
    user = current_user if current_user.is_authenticated else None
    filtered_pages = []
    for page in pages:
        version = get_latest_published_version(page)
        if not version or version.deleted:
            continue
        visible_sections = [s for s in version.sections if has_access(s, user)]
        if not visible_sections:
            continue
        filtered_pages.append({
            'slug': page.slug,
            'title': page.title,
            'deleted': bool(getattr(version, 'deleted', False)),
            'tags': list(page.tags),
        })
    tree = build_wiki_tree(filtered_pages)
    return render_template("wiki/list.html", wiki_tree=tree)


def has_access(section, user):
    # Always allow for wiki_admin or rules_team
    if (
        user
        and user.is_authenticated
        and (user.has_role("wiki_admin") or user.has_role("rules_team"))
    ):
        return True
    if not section.restriction_type:
        return True
    # Role-based restriction
    if section.restriction_type == SectionRestrictionType.ROLE:
        if not user or not user.is_authenticated:
            return False
        return user.has_role(section.restriction_value)
    # Character-based restrictions
    if section.restriction_type in [
        SectionRestrictionType.FACTION,
        SectionRestrictionType.SPECIES,
        SectionRestrictionType.SKILL,
        SectionRestrictionType.TAG,
        SectionRestrictionType.REPUTATION,
        SectionRestrictionType.CYBERNETIC,
    ]:
        # User must have an active character
        character = None
        if user and user.is_authenticated and hasattr(user, "characters"):
            # Use the first active character (customize as needed)
            character = next((c for c in user.characters if c.status == "active"), None)
        if not character:
            return False
        values = []
        if section.restriction_value:
            try:
                values = json.loads(section.restriction_value)
            except Exception:
                values = [section.restriction_value]
        if section.restriction_type == SectionRestrictionType.FACTION:
            return character.faction_id in [int(v) for v in values]
        if section.restriction_type == SectionRestrictionType.SPECIES:
            return character.species_id in [int(v) for v in values]
        if section.restriction_type == SectionRestrictionType.SKILL:
            # Character must have at least one of the required skills
            character_skill_ids = [
                cs.skill_id for cs in getattr(character, "skills", [])
            ]
            return any(int(v) in character_skill_ids for v in values)
        if section.restriction_type == SectionRestrictionType.CYBERNETIC:
            # Character must have at least one of the required cybernetics
            character_cyber_ids = [c.id for c in getattr(character, "cybernetics", [])]
            return any(int(v) in character_cyber_ids for v in values)
        if section.restriction_type == SectionRestrictionType.TAG:
            character_tag_ids = [t.id for t in getattr(character, "tags", [])]
            return any(int(v) in character_tag_ids for v in values)
        if section.restriction_type == SectionRestrictionType.REPUTATION:
            # For reputation, values should be [faction_id, min_reputation]
            if len(values) != 2:
                return False
            faction_id = int(values[0])
            min_reputation = int(values[1])
            # Get character's reputation with the faction
            reputation = character.get_reputation(faction_id)
            return reputation >= min_reputation
    # Default: allow
    return True


@wiki_bp.route("/<path:slug>")
def wiki_view(slug):
    page = WikiPage.query.get_or_404(slug)
    is_editor = current_user.is_authenticated and current_user.has_role("plot_team")
    user = current_user if current_user.is_authenticated else None
    version_id = request.args.get("version", type=int)
    current = request.args.get("current", type=bool)
    is_historic_version = False
    is_pending_version = False

    if version_id:
        version = WikiPageVersion.query.get_or_404(version_id)
        if not version:
            return render_template("404.html"), 404
        published_version = get_latest_published_version(page)

        if (not is_editor) and (version.status != WikiPageVersionStatus.PUBLISHED):
            if published_version:
                return redirect(url_for("wiki.wiki_view", slug=slug))
            else:
                return render_template("404.html"), 404

        if (
            published_version
            and published_version.version_number > version.version_number
        ):
            is_historic_version = True
    else:
        if is_editor and not current:
            version = get_latest_version(page)
            is_pending_version = version.status == WikiPageVersionStatus.PENDING
        else:
            version = get_latest_published_version(page)

    if request.args.get("saved") == "1" and is_editor:
        flash("Page saved successfully.", "success")

    if version and version.deleted:
        if not is_editor:
            return render_template("404.html"), 404

    if not version:
        flash("No published version of this page exists.")
        return redirect(url_for("wiki.wiki_list"))

    visible_sections = [
        {
            "id": s.id,
            "title": s.title,
            "content": s.content,
            "order": s.order,
            "restriction_type": (
                s.restriction_type.name.lower() if s.restriction_type else None
            ),
            "restriction_value": s.restriction_value,
        }
        for s in version.sections
        if has_access(s, user)
    ]

    if not visible_sections:
        flash("You do not have access to view this page.")
        return redirect(url_for("wiki.wiki_view", slug="index"))

    return render_template(
        "wiki/view.html",
        page=page,
        sections=visible_sections,
        version=version,
        is_historic_version=is_historic_version,
        is_pending_version=is_pending_version,
    )


@wiki_bp.route("/_internal_pages")
def get_internal_pages():
    q = request.args.get("q", "").strip().lower()
    query = WikiPage.query
    if q:
        query = query.filter(
            (WikiPage.title.ilike(f"%{q}%")) | (WikiPage.slug.ilike(f"%{q}%"))
        )
    return [
        {
            "id": page.slug,
            "text": f"{page.title} ({page.slug})"
        }
        for page in query.order_by(WikiPage.title).limit(30)
    ]


@wiki_bp.route("/api/wiki-pages")
def api_wiki_pages():
    """API endpoint for CKEditor to get wiki pages for link dropdown"""
    q = request.args.get("q", "").strip().lower()
    query = WikiPage.query
    
    # Filter by search query if provided
    if q:
        query = query.filter(
            (WikiPage.title.ilike(f"%{q}%")) | (WikiPage.slug.ilike(f"%{q}%"))
        )
    
    # Get user for access filtering
    user = current_user if current_user.is_authenticated else None
    
    pages = []
    for page in query.order_by(WikiPage.title).limit(50):
        # Check if user has access to this page
        version = get_latest_published_version(page)
        if not version or version.deleted:
            continue
            
        visible_sections = [s for s in version.sections if has_access(s, user)]
        if not visible_sections:
            continue
            
        pages.append({
            "id": page.slug,
            "text": page.title,
            "url": url_for("wiki.wiki_view", slug=page.slug),
            "slug": page.slug
        })
    
    return jsonify(pages)


@wiki_bp.route("/<path:slug>/edit", methods=["GET"])
@login_required
def wiki_edit(slug):
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Only plot team members can edit wiki pages.", "error")
        return redirect(url_for("wiki.wiki_view", slug=slug))
    page = WikiPage.query.get_or_404(slug)
    role_descriptions = Role.descriptions()
    available_roles = [
        {"value": v, "label": role_descriptions[v]} for v in Role.values()
    ]
    version = get_latest_version(page)
    if not version:
        version = get_pending_version(page, current_user)

    sections = [
        {
            "id": s.id,
            "title": s.title,
            "content": s.content,
            "order": s.order,
            "restriction_type": (
                s.restriction_type.name.lower() if s.restriction_type else None
            ),
            "restriction_value": s.restriction_value,
        }
        for s in version.sections
    ]
    factions = [
        {"id": f.id, "name": f.name} for f in Faction.query.order_by(Faction.name).all()
    ]
    species = [
        {"id": s.id, "name": s.name} for s in Species.query.order_by(Species.name).all()
    ]
    skills = [
        {"id": sk.id, "name": sk.name} for sk in Skill.query.order_by(Skill.name).all()
    ]
    tags = [{"id": t.id, "name": t.name} for t in CharacterTag.query.order_by(CharacterTag.name).all()]
    cybernetics = [
        {"id": c.id, "name": c.name}
        for c in Cybernetic.query.order_by(Cybernetic.name).all()
    ]
    return render_template(
        "wiki/edit.html",
        page=page,
        sections=sections,
        available_roles=available_roles,
        factions=factions,
        species=species,
        skills=skills,
        tags=tags,
        cybernetics=cybernetics,
    )


@wiki_bp.route("/<path:slug>/edit", methods=["POST"])
@login_required
def wiki_edit_post(slug):
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Only plot team members can edit wiki pages.", "error")
        return redirect(url_for("wiki.wiki_view", slug=slug))
    page = WikiPage.query.get_or_404(slug)
    version = get_pending_version(page, current_user)
    if request.is_json:
        data = request.get_json()
        if not data or "sections" not in data:
            return jsonify({"success": False, "error": "Invalid data format"}), 400
        try:
            db.session.begin_nested()
            save_wiki_version(data, version)
            # Handle tags
            tag_values = data.get('tags', [])
            tag_objs = []
            for tag_val in tag_values:
                if isinstance(tag_val, int) or (isinstance(tag_val, str) and tag_val.isdigit()):
                    tag = WikiTag.query.get(int(tag_val))
                    if tag:
                        tag_objs.append(tag)
                elif isinstance(tag_val, str):
                    tag = WikiTag.query.filter_by(name=tag_val).first()
                    if not tag:
                        tag = WikiTag(name=tag_val)
                        db.session.add(tag)
                        db.session.flush()
                    tag_objs.append(tag)
            page.tags = tag_objs
            db.session.commit()
            flash("Page saved successfully")
            return jsonify(
                {"success": True, "redirect": url_for("wiki.wiki_view", slug=slug)}
            )
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        return jsonify({"success": False, "error": "Invalid data format"}), 400


@wiki_bp.route("/new", methods=["GET"])
@login_required
def wiki_new():
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied")
        return redirect(url_for("wiki.wiki_list"))
    role_descriptions = Role.descriptions()
    available_roles = [
        {"value": v, "label": role_descriptions[v]} for v in Role.values()
    ]

    factions = [
        {"id": f.id, "name": f.name} for f in Faction.query.order_by(Faction.name).all()
    ]
    species = [
        {"id": s.id, "name": s.name} for s in Species.query.order_by(Species.name).all()
    ]
    skills = [
        {"id": sk.id, "name": sk.name} for sk in Skill.query.order_by(Skill.name).all()
    ]
    tags = [{"id": t.id, "name": t.name} for t in CharacterTag.query.order_by(CharacterTag.name).all()]
    cybernetics = [
        {"id": c.id, "name": c.name}
        for c in Cybernetic.query.order_by(Cybernetic.name).all()
    ]

    return render_template("wiki/edit.html", 
        page=None, 
        sections=[],
        available_roles=available_roles,
        factions=factions,
        species=species,
        skills=skills,
        tags=tags,
        cybernetics=cybernetics,
    )


@wiki_bp.route("/new", methods=["POST"])
@login_required
def wiki_new_post():
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied")
        return redirect(url_for("wiki.wiki_view", slug="index"))
    if request.is_json:
        data = request.get_json()
        if (
            not data
            or "title" not in data
            or "slug" not in data
            or "sections" not in data
        ):
            return jsonify({"success": False, "error": "Invalid data format"}), 400
        if WikiPage.query.filter_by(slug=data["slug"]).first():
            flash("Slug already exists")
            return redirect(url_for("wiki.wiki_new"))
        page = WikiPage(title=data["title"], slug=data["slug"])
        db.session.add(page)
        db.session.flush()
        version = WikiPageVersion(
            page_slug=data["slug"],
            version_number=0,
            status=WikiPageVersionStatus.PENDING,
            created_by=current_user.id,
        )
        db.session.add(version)
        db.session.flush()
        try:
            db.session.begin_nested()
            save_wiki_version(data, version)
            # Handle tags
            tag_values = data.get('tags', [])
            tag_objs = []
            for tag_val in tag_values:
                if isinstance(tag_val, int) or (isinstance(tag_val, str) and tag_val.isdigit()):
                    tag = WikiTag.query.get(int(tag_val))
                    if tag:
                        tag_objs.append(tag)
                elif isinstance(tag_val, str):
                    tag = WikiTag.query.filter_by(name=tag_val).first()
                    if not tag:
                        tag = WikiTag(name=tag_val)
                        db.session.add(tag)
                        db.session.flush()
                    tag_objs.append(tag)
            page.tags = tag_objs
            db.session.commit()
            flash("Page created successfully")
            return jsonify(
                {
                    "success": True,
                    "redirect": url_for("wiki.wiki_view", slug=data["slug"]),
                }
            )
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        return jsonify({"success": False, "error": "Invalid data format"}), 400


@wiki_bp.route("/upload_image", methods=["POST"])
@login_required
def wiki_upload_image():
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        return {"error": "Access denied"}, 403
    file = request.files.get("file")
    if not file:
        return {"error": "No file uploaded"}, 400
    image = WikiImage(
        filename=file.filename,
        data=file.read(),
        mimetype=file.mimetype,
        uploaded_by=current_user.id,
    )
    db.session.add(image)
    db.session.commit()
    url = url_for("wiki.wiki_image", image_id=image.id)
    return {"location": url}


@wiki_bp.route("/image/<int:image_id>")
def wiki_image(image_id):
    image = WikiImage.query.get_or_404(image_id)
    return send_file(
        io.BytesIO(image.data), mimetype=image.mimetype, download_name=image.filename
    )


@wiki_bp.route("/delete/<path:slug>", methods=["POST"])
@login_required
def wiki_delete(slug):
    page = WikiPage.query.get_or_404(slug)
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied")
        return redirect(url_for("wiki.wiki_view", slug=slug))
    version = get_pending_version(page, current_user)
    if version and not version.deleted:
        version.deleted = True
        db.session.commit()
        flash("Page marked as deleted.")
    return redirect(url_for("wiki.wiki_view", slug=slug))


@wiki_bp.route("/restore/<path:slug>", methods=["POST"])
@login_required
def wiki_restore(slug):
    page = WikiPage.query.get_or_404(slug)
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied")
        return redirect(url_for("wiki.wiki_view", slug=slug))
    version = get_pending_version(page, current_user)
    if version and version.deleted:
        version.deleted = False
        db.session.commit()
        flash("Page restored.")
    return redirect(url_for("wiki.wiki_view", slug=slug))


@wiki_bp.route("/changes/pending", methods=["GET"])
@login_required
def wiki_pending_changes():
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied", "error")
        return redirect(url_for("wiki.wiki_view", slug="index"))
    pages = WikiPage.query.order_by(WikiPage.title).all()
    pending_pages = []
    for page in pages:
        latest_version = get_latest_version(page)
        published_version = get_latest_published_version(page)
        if latest_version and latest_version.status == WikiPageVersionStatus.PENDING:
            if (
                published_version
                and latest_version.deleted != published_version.deleted
            ):
                diffs = [
                    {"diff": ["[Deleted]" if latest_version.deleted else "[Restored]"]}
                ]
                continue

            published_sections = (
                {s.id: s for s in published_version.sections}
                if published_version
                else {}
            )
            diffs = []

            for section in latest_version.sections:
                pub_section = published_sections.get(section.id)
                restriction_changed = False
                if pub_section:
                    # Check for restriction changes
                    old_type = (
                        pub_section.restriction_type.name.lower()
                        if pub_section.restriction_type
                        else None
                    )
                    new_type = (
                        section.restriction_type.name.lower()
                        if section.restriction_type
                        else None
                    )
                    old_value = pub_section.restriction_value
                    new_value = section.restriction_value
                    restriction_changed = (old_type != new_type) or (
                        old_value != new_value
                    )
                    if restriction_changed:
                        diff = [
                            f"[Restriction changed: {old_type or 'None'} → {new_type or 'None'} | {old_value or 'None'} → {new_value or 'None'}]"
                        ]
                    else:
                        diff = []
                    # Always show content diff on pending changes page
                    diff += list(
                        difflib.unified_diff(
                            (pub_section.content or "").splitlines(),
                            (section.content or "").splitlines(),
                            lineterm="",
                            fromfile="Published",
                            tofile="Pending",
                        )
                    )
                    published_sections.pop(section.id)
                else:
                    diff = ["[Added]"]
                    # Always show content for new sections
                    diff += (section.content or "").splitlines()
                diffs.append({"section": section, "diff": diff})

            for section in published_sections.values():
                diff = ["[Deleted]"]
                # Always show content for deleted sections
                diff += (section.content or "").splitlines()
                diffs.append({"section": section, "diff": diff})

            pending_pages.append(
                {
                    "slug": page.slug,
                    "title": page.title,
                    "version_id": latest_version.id,
                    "version_number": latest_version.version_number,
                    "created_at": latest_version.created_at,
                    "created_by": latest_version.created_by,
                    "diffs": diffs,
                }
            )
    return render_template("wiki/pending_changes.html", pending_pages=pending_pages)


@wiki_bp.route("/changes/pending", methods=["POST"])
@login_required
def wiki_pending_changes_post():
    if not current_user.is_authenticated or not current_user.has_role("plot_team"):
        flash("Access denied", "error")
        return redirect(url_for("wiki.wiki_view", slug="index"))
    selected_slugs = request.form.getlist("selected_pages")
    changelog = request.form.get("changelog", "").strip()
    if not changelog:
        flash("Change log message is required.", "error")
        return redirect(url_for("wiki.wiki_pending_changes"))
    if not selected_slugs:
        flash("You must select at least one page to publish.", "error")
        return redirect(url_for("wiki.wiki_pending_changes"))
    published_versions = []
    for slug in selected_slugs:
        page = WikiPage.query.get(slug)
        if not page:
            continue
        latest_version = get_latest_version(page)
        if latest_version and latest_version.status == WikiPageVersionStatus.PENDING:
            # Compute diff vs. published
            published_version = get_latest_published_version(page)
            published_sections = (
                {s.id: s for s in published_version.sections}
                if published_version
                else {}
            )
            diffs = []
            for section in latest_version.sections:
                pub_section = published_sections.get(section.id)
                restriction_changed = False
                if pub_section:
                    # Check for restriction changes
                    old_type = (
                        pub_section.restriction_type.name.lower()
                        if pub_section.restriction_type
                        else None
                    )
                    new_type = (
                        section.restriction_type.name.lower()
                        if section.restriction_type
                        else None
                    )
                    old_value = pub_section.restriction_value
                    new_value = section.restriction_value
                    restriction_changed = (old_type != new_type) or (
                        old_value != new_value
                    )
                    diff = []
                    if restriction_changed:
                        diff.append(
                            f"[Restriction changed: {old_type or 'None'} → {new_type or 'None'} | {old_value or 'None'} → {new_value or 'None'}]"
                        )
                    # If any restriction, do not show content
                    if new_type or old_type:
                        diff.append(
                            "[Restricted Section: Content hidden due to access restrictions]"
                        )
                    else:
                        diff += list(
                            difflib.unified_diff(
                                (pub_section.content or "").splitlines(),
                                (section.content or "").splitlines(),
                                lineterm="",
                                fromfile="Published",
                                tofile="Pending",
                            )
                        )
                    published_sections.pop(section.id)
                else:
                    diff = ["[Added]"]
                    new_type = (
                        section.restriction_type.name.lower()
                        if section.restriction_type
                        else None
                    )
                    if new_type:
                        diff.append(
                            "[Restricted Section: Content hidden due to access restrictions]"
                        )
                    else:
                        diff += (section.content or "").splitlines()
                diffs.append("\n".join(diff))
            for section in published_sections.values():
                diff = ["[Deleted]"]
                old_type = (
                    section.restriction_type.name.lower()
                    if section.restriction_type
                    else None
                )
                if old_type:
                    diff.append(
                        "[Restricted Section: Content hidden due to access restrictions]"
                    )
                else:
                    diff += (section.content or "").splitlines()
                diffs.append("\n".join(diff))
            latest_version.diff = "\n\n".join(diffs)
            latest_version.status = WikiPageVersionStatus.PUBLISHED
            published_versions.append(latest_version)
    if published_versions:
        log = WikiChangeLog(
            user_id=current_user.id, message=changelog, versions=published_versions
        )
        db.session.add(log)
        db.session.commit()

        send_wiki_published_notification_to_all(log)
        flash("Changes published and logged.", "success")
        return redirect(url_for("wiki.wiki_change_log"))
    else:
        flash("No valid pending versions to publish.", "error")
        return redirect(url_for("wiki.wiki_pending_changes"))


@wiki_bp.route("/changes/log")
def wiki_change_log():
    logs = WikiChangeLog.query.order_by(WikiChangeLog.timestamp.desc()).all()
    return render_template("wiki/change_log.html", logs=logs)


@wiki_bp.route("/search")
def wiki_search():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template("wiki/search.html", results=[], query='')
    
    # Tag search if query starts with #
    if query.startswith('#'):
        tag_term = query[1:].strip().lower()
        tag_matches = WikiTag.query.filter(WikiTag.name.ilike(f'%{tag_term}%')).all()
        pages = set()
        for tag in tag_matches:
            for page in tag.pages:
                version = get_latest_published_version(page)
                if not version or version.deleted:
                    continue
                visible_sections = [s for s in version.sections if has_access(s, current_user)]
                if not visible_sections:
                    continue
                pages.add(page)
        results = []
        for page in pages:
            version = get_latest_published_version(page)
            results.append({
                'page': page,
                'highlighted_title': page.title,
                'sections': [],
                'tags': [t.name for t in page.tags]
            })
        return render_template("wiki/search.html", results=results, query=query)
    
    # Normal search
    pages = WikiPage.query.all()
    results = []
    def highlight_text(text, query):
        if not text:
            return text
        text_lower = text.lower()
        query_lower = query.lower()
        pos = 0
        result = []
        while True:
            pos = text_lower.find(query_lower, pos)
            if pos == -1:
                break
            result.append(text[:pos])
            result.append('<mark>' + text[pos:pos+len(query)] + '</mark>')
            text = text[pos+len(query):]
            text_lower = text_lower[pos+len(query):]
            pos = 0
        result.append(text)
        return ''.join(result)
    for page in pages:
        version = get_latest_published_version(page)
        if not version or version.deleted:
            continue
        visible_sections = [s for s in version.sections if has_access(s, current_user)]
        if not visible_sections:
            continue
        title_match = query.lower() in page.title.lower()
        highlighted_title = highlight_text(page.title, query) if title_match else page.title
        section_matches = []
        for section in visible_sections:
            section_title_match = query.lower() in (section.title or '').lower()
            section_content_match = query.lower() in (section.content or '').lower()
            if section_title_match or section_content_match:
                content = section.content or ''
                if section_content_match:
                    positions = []
                    pos = 0
                    while True:
                        pos = content.lower().find(query.lower(), pos)
                        if pos == -1:
                            break
                        positions.append(pos)
                        pos += 1
                    if positions:
                        start = max(0, positions[0] - 100)
                        end = min(len(content), positions[-1] + len(query) + 100)
                        excerpt = content[start:end]
                        if start > 0:
                            excerpt = '...' + excerpt
                        if end < len(content):
                            excerpt = excerpt + '...'
                        excerpt = highlight_text(excerpt, query)
                    else:
                        excerpt = content[:200] + '...' if len(content) > 200 else content
                else:
                    excerpt = content[:200] + '...' if len(content) > 200 else content
                section_matches.append({
                    'title': highlight_text(section.title, query) if section_title_match else section.title,
                    'excerpt': excerpt,
                    'title_match': section_title_match,
                    'content_match': section_content_match
                })
        if title_match or section_matches:
            results.append({
                'page': page,
                'highlighted_title': highlighted_title,
                'sections': section_matches
            })
    return render_template("wiki/search.html", results=results, query=query)


@wiki_bp.route('/tags', methods=['GET', 'POST'])
def wiki_tags():
    if request.method == 'POST':
        name = request.json.get('name', '').strip()
        if not name:
            return jsonify({'error': 'No tag name provided'}), 400
        tag = WikiTag.query.filter_by(name=name).first()
        if not tag:
            tag = WikiTag(name=name)
            db.session.add(tag)
            db.session.commit()
        return jsonify({'id': tag.id, 'text': tag.name})
    else:
        q = request.args.get('q', '').strip()
        tags = WikiTag.query
        if q:
            tags = tags.filter(WikiTag.name.ilike(f'%{q}%'))
        tags = tags.order_by(WikiTag.name).all()
        return jsonify({'results': [{'id': t.id, 'text': t.name} for t in tags]})


@wiki_bp.route('/live_search')
def wiki_live_search():
    query = request.args.get('q', '').strip()
    results = []
    if not query:
        return jsonify(results)
    if query.startswith('#'):
        tag_term = query[1:].strip().lower()
        tag_matches = WikiTag.query.filter(WikiTag.name.ilike(f'%{tag_term}%')).all()
        pages = set()
        for tag in tag_matches:
            for page in tag.pages:
                version = get_latest_published_version(page)
                if not version or version.deleted:
                    continue
                visible_sections = [s for s in version.sections if has_access(s, current_user)]
                if not visible_sections:
                    continue
                pages.add(page)
        for page in pages:
            results.append({
                'title': page.title,
                'slug': page.slug,
                'tags': [t.name for t in page.tags]
            })
    else:
        # Match title or tag
        pages = WikiPage.query.all()
        for page in pages:
            version = get_latest_published_version(page)
            if not version or version.deleted:
                continue
            visible_sections = [s for s in version.sections if has_access(s, current_user)]
            if not visible_sections:
                continue
            title_match = query.lower() in page.title.lower()
            tag_match = any(query.lower() in t.name.lower() for t in page.tags)
            if title_match or tag_match:
                results.append({
                    'title': page.title,
                    'slug': page.slug,
                    'tags': [t.name for t in page.tags]
                })
    return jsonify(results)
