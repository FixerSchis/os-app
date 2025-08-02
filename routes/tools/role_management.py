from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.permissions import Permission, Role
from models.extensions import db
from models.tools.user import User
from utils.permission_decorators import permission_required

bp = Blueprint("role_management", __name__)


@bp.route("/roles")
@login_required
@permission_required(permissions=["user.roles"])
def role_list():
    """List all roles sorted by permission count (most to least) with owner always at top."""
    # Get all roles
    roles = Role.query.all()

    # Sort by permission count (most to least)
    roles.sort(key=lambda role: len(role.permissions), reverse=True)

    # Ensure owner is always at the top
    owner_role = next((role for role in roles if role.name == "owner"), None)
    if owner_role:
        roles.remove(owner_role)
        roles.insert(0, owner_role)

    # Get all users for the promote modal
    users = User.query.all()

    return render_template("tools/role_management/list.html", roles=roles, users=users)


@bp.route("/roles/<int:role_id>")
@login_required
@permission_required(permissions=["user.roles"])
def role_view(role_id):
    """View a specific role and its permissions."""
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    return render_template(
        "tools/role_management/view.html", role=role, all_permissions=all_permissions
    )


@bp.route("/roles/new", methods=["GET", "POST"])
@login_required
@permission_required(permissions=["user.roles"])
def role_create():
    """Create a new role."""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        permission_ids = request.form.getlist("permissions")

        if not name:
            flash("Role name is required.", "error")
            return redirect(url_for("role_management.role_create"))

        # Check if role name already exists
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash("A role with this name already exists.", "error")
            return redirect(url_for("role_management.role_create"))

        # Create new role
        role = Role(name=name, description=description, is_system_role=False)
        db.session.add(role)

        # Add permissions (excluding owner.promote for non-owner roles)
        for permission_id in permission_ids:
            permission = Permission.query.get(permission_id)
            if permission and permission.name != "owner.promote":
                role.add_permission(permission)

        db.session.commit()
        flash(f"Role '{name}' created successfully.", "success")
        return redirect(url_for("role_management.role_list"))

    all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    return render_template("tools/role_management/create.html", all_permissions=all_permissions)


@bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required(permissions=["user.roles"])
def role_edit(role_id):
    """Edit a role."""
    role = Role.query.get_or_404(role_id)

    # Owner role cannot be edited
    if role.name == "owner":
        flash("The owner role cannot be edited.", "error")
        return redirect(url_for("role_management.role_list"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        permission_ids = request.form.getlist("permissions")

        if not name:
            flash("Role name is required.", "error")
            return redirect(url_for("role_management.role_edit", role_id=role_id))

        # Check if role name already exists (excluding current role)
        existing_role = Role.query.filter(Role.name == name, Role.id != role_id).first()
        if existing_role:
            flash("A role with this name already exists.", "error")
            return redirect(url_for("role_management.role_edit", role_id=role_id))

        # Update role
        role.name = name
        role.description = description

        # Clear existing permissions and add new ones
        role.permissions.clear()
        for permission_id in permission_ids:
            permission = Permission.query.get(permission_id)
            if permission:
                # Only allow owner.promote for owner role
                if permission.name == "owner.promote" and role.name != "owner":
                    continue
                role.add_permission(permission)

        db.session.commit()
        flash(f"Role '{name}' updated successfully.", "success")
        return redirect(url_for("role_management.role_list"))

    all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    return render_template(
        "tools/role_management/edit.html", role=role, all_permissions=all_permissions
    )


@bp.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
@permission_required(permissions=["user.roles"])
def role_delete(role_id):
    """Delete a role."""
    role = Role.query.get_or_404(role_id)

    # Owner and default roles cannot be deleted
    if role.name == "owner":
        flash("The owner role cannot be deleted.", "error")
        return redirect(url_for("role_management.role_list"))

    if role.name == "default":
        flash("The default role cannot be deleted.", "error")
        return redirect(url_for("role_management.role_list"))

    # Check if any users are using this role
    users_with_role = User.query.filter_by(role_id=role_id).count()
    if users_with_role > 0:
        flash(
            f"Cannot delete role '{role.name}' because {users_with_role} user(s) are assigned to it.",
            "error",
        )
        return redirect(url_for("role_management.role_list"))

    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' deleted successfully.", "success")
    return redirect(url_for("role_management.role_list"))


@bp.route("/roles/promote-user", methods=["POST"])
@login_required
@permission_required(permissions=["owner.promote"])
def promote_user():
    """Promote a user to owner role (only available to current owner)."""
    if not current_user.has_permission("owner.promote"):
        flash("You do not have permission to promote users to owner.", "error")
        return redirect(url_for("role_management.role_list"))

    user_id = request.form.get("user_id")
    if not user_id:
        flash("User ID is required.", "error")
        return redirect(url_for("role_management.role_list"))

    user = User.query.get_or_404(user_id)

    # Find the next highest role based on permission count
    all_roles = Role.query.all()
    roles_by_permission_count = sorted(
        all_roles, key=lambda role: len(role.permissions), reverse=True
    )

    # Remove owner from the list and get the next highest
    non_owner_roles = [role for role in roles_by_permission_count if role.name != "owner"]
    if not non_owner_roles:
        flash("No other roles available for assignment.", "error")
        return redirect(url_for("role_management.role_list"))

    next_highest_role = non_owner_roles[0]

    # Assign the new owner role to the user
    user.role = Role.query.filter_by(name="owner").first()

    # Assign the next highest role to the current user
    current_user.role = next_highest_role

    db.session.commit()
    flash(
        f"User {user.username} has been promoted to owner. You now have the {next_highest_role.name} role.",
        "success",
    )
    return redirect(url_for("role_management.role_list"))


@bp.route("/permissions")
@login_required
@permission_required(permissions=["user.roles"])
def permission_list():
    """List all permissions grouped by category."""
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()

    # Group permissions by category
    permissions_by_category = {}
    for permission in permissions:
        if permission.category not in permissions_by_category:
            permissions_by_category[permission.category] = []
        permissions_by_category[permission.category].append(permission)

    return render_template(
        "tools/role_management/permissions.html", permissions_by_category=permissions_by_category
    )
