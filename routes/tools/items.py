from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, or_

from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.enums import CharacterAuditAction, CharacterStatus, Role
from models.extensions import db
from models.tools.character import Character, CharacterAuditLog
from models.tools.character_inventory import (
    CharacterItem,
    ItemTransferRequest,
    ItemTransferRequestItem,
    ItemTransferStatus,
)
from models.tools.user import User
from utils.decorators import email_verified_required, user_admin_required

items_bp = Blueprint("tools_items", __name__)


@items_bp.route("/")
@login_required
@email_verified_required
def items_list():
    """Display the items page - different views for user_admin vs regular users."""

    if current_user.has_role(Role.USER_ADMIN.value):
        return _admin_items_view()
    else:
        return _user_items_view()


def _admin_items_view():
    """Admin view - shows all item transfer requests and character inventories."""

    # Get search parameters
    search_query = request.args.get("search", "").strip()

    # Get all pending transfer requests
    pending_requests = (
        ItemTransferRequest.query.filter_by(status=ItemTransferStatus.PENDING.value)
        .order_by(ItemTransferRequest.requested_at.desc())
        .all()
    )

    # Get all characters with their inventory counts, filtered by search if provided
    characters_query = Character.query.filter_by(status=CharacterStatus.ACTIVE.value)

    if search_query:
        # Search by character name or user_id.character_id format
        characters_query = characters_query.join(User).filter(
            db.or_(
                Character.name.ilike(f"%{search_query}%"),
                db.func.concat(User.user_id, ".", Character.character_id).ilike(
                    f"%{search_query}%"
                ),
                User.first_name.ilike(f"%{search_query}%"),
                User.surname.ilike(f"%{search_query}%"),
            )
        )

    characters = characters_query.all()
    character_inventories = {}

    for character in characters:
        inventory_items = (
            CharacterItem.query.filter_by(character_id=character.id)
            .join(Item)
            .join(ItemBlueprint)
            .order_by(ItemBlueprint.name)
            .all()
        )
        character_inventories[character.id] = {
            "character": character,
            "inventory_count": len(inventory_items),
            "inventory_items": inventory_items,
        }

    return render_template(
        "tools/items/admin_list.html",
        pending_requests=pending_requests,
        character_inventories=character_inventories,
        ItemTransferStatus=ItemTransferStatus,
        search_query=search_query,
    )


def _user_items_view():
    """User view - shows their active characters' inventories and transfer requests."""

    # Get user's active characters
    user_characters = Character.query.filter_by(
        user_id=current_user.id, status=CharacterStatus.ACTIVE.value
    ).all()

    if not user_characters:
        flash("You need an active character to access the items page.", "error")
        return redirect(url_for("characters.character_list"))

    # Get inventory for each character
    character_inventories = {}
    for character in user_characters:
        inventory_items = (
            CharacterItem.query.filter_by(character_id=character.id)
            .join(Item)
            .join(ItemBlueprint)
            .order_by(ItemBlueprint.name)
            .all()
        )
        character_inventories[character.id] = {
            "character": character,
            "inventory_items": inventory_items,
        }

    # Get user's pending transfer requests
    user_requests = (
        ItemTransferRequest.query.filter(
            ItemTransferRequest.requesting_character_id.in_([c.id for c in user_characters])
        )
        .order_by(ItemTransferRequest.requested_at.desc())
        .all()
    )

    # Get all active characters for transfer target selection
    all_characters = Character.query.filter_by(status=CharacterStatus.ACTIVE.value).all()

    return render_template(
        "tools/items/user_list.html",
        character_inventories=character_inventories,
        user_requests=user_requests,
        all_characters=all_characters,
        ItemTransferStatus=ItemTransferStatus,
    )


@items_bp.route("/character/<int:character_id>/inventory")
@login_required
@email_verified_required
@user_admin_required
def character_inventory(character_id):
    """Admin view of a specific character's inventory."""

    character = Character.query.get_or_404(character_id)

    # Get inventory items
    inventory_items = (
        CharacterItem.query.filter_by(character_id=character_id)
        .join(Item)
        .join(ItemBlueprint)
        .order_by(ItemBlueprint.name)
        .all()
    )

    # Get all available items for assignment
    all_items = Item.query.join(ItemBlueprint).order_by(ItemBlueprint.name).all()

    # Get items not in character's inventory
    assigned_item_ids = {ci.item_id for ci in inventory_items}
    available_items = [item for item in all_items if item.id not in assigned_item_ids]

    # Get all item blueprints for creating new items
    item_blueprints = ItemBlueprint.query.order_by(ItemBlueprint.name).all()

    return render_template(
        "tools/items/character_inventory.html",
        character=character,
        inventory_items=inventory_items,
        available_items=available_items,
        item_blueprints=item_blueprints,
    )


@items_bp.route("/character/<int:character_id>/assign-item", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def assign_item_to_character(character_id):
    """Assign an item to a character (admin only)."""

    Character.query.get_or_404(character_id)  # Verify character exists
    item_id = request.form.get("item_id", type=int)
    blueprint_id = request.form.get("blueprint_id", type=int)

    if not item_id and not blueprint_id:
        flash("Please select an existing item or a blueprint to create a new item.", "error")
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))

    if item_id and blueprint_id:
        flash("Please select either an existing item OR a blueprint, not both.", "error")
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))

    # Handle creating new item from blueprint
    if blueprint_id:
        blueprint = ItemBlueprint.query.get(blueprint_id)
        if not blueprint:
            flash("Invalid blueprint selected.", "error")
            return redirect(url_for("tools_items.character_inventory", character_id=character_id))

        # Create new item from blueprint
        # Find the next available item_id for this blueprint
        existing_items = (
            Item.query.filter_by(blueprint_id=blueprint_id).order_by(Item.item_id.desc()).first()
        )
        next_item_id = 1 if not existing_items else existing_items.item_id + 1

        # Calculate expiry based on previous event number + 4
        from datetime import datetime

        from models.event import Event

        # Get the most recent event that has ended
        previous_event = (
            Event.query.filter(Event.end_date <= datetime.now())
            .order_by(Event.end_date.desc())
            .first()
        )

        # Calculate expiry: previous event number + 4, or 0 if no previous event
        if previous_event:
            try:
                previous_event_number = int(previous_event.event_number)
                expiry = previous_event_number + 4
            except (ValueError, TypeError):
                # If event_number is not a valid integer, default to 0
                expiry = 0
        else:
            expiry = 0

        new_item = Item(
            blueprint_id=blueprint_id,
            item_id=next_item_id,
            expiry=expiry,
        )
        db.session.add(new_item)
        db.session.flush()  # Flush to get the new item ID

        item_id = new_item.id
        item_description = f"Item created from blueprint: {blueprint.name} ({new_item.full_code})"
    else:
        # Use existing item
        item = Item.query.get(item_id)
        if not item:
            flash("Invalid item selected.", "error")
            return redirect(url_for("tools_items.character_inventory", character_id=character_id))
        item_description = f"Item assigned: {item.blueprint.name} ({item.full_code})"

    # Check if item is already assigned to this character
    existing_assignment = CharacterItem.query.filter_by(
        character_id=character_id, item_id=item_id
    ).first()

    if existing_assignment:
        flash("This item is already assigned to this character.", "error")
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))

    # Create the assignment
    character_item = CharacterItem(
        character_id=character_id,
        item_id=item_id,
        assigned_by_user_id=current_user.id,
    )

    db.session.add(character_item)
    db.session.flush()  # Flush to get the character_item.id

    # Create audit log for item assignment
    audit_log = CharacterAuditLog(
        character_id=character_id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes=item_description,
    )
    db.session.add(audit_log)

    db.session.commit()

    flash("Item assigned successfully.", "success")

    # Redirect back to the page the user came from
    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    elif request.form.get("from_character_edit"):
        # If coming from character edit page, redirect back there
        return redirect(url_for("characters.edit", character_id=character_id))
    else:
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))


@items_bp.route("/character/<int:character_id>/remove-item", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def remove_item_from_character(character_id):
    """Remove an item from a character (admin only)."""

    Character.query.get_or_404(character_id)  # Verify character exists
    character_item_id = request.form.get("character_item_id", type=int)

    if not character_item_id:
        flash("Please select an item to remove.", "error")
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))

    # Find the character item
    character_item = CharacterItem.query.filter_by(
        id=character_item_id, character_id=character_id
    ).first()

    if not character_item:
        flash("Item not found in character's inventory.", "error")
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))

    # Create audit log for item removal
    audit_log = CharacterAuditLog(
        character_id=character_id,
        editor_user_id=current_user.id,
        action=CharacterAuditAction.STATUS_CHANGE.value,
        changes=(
            f"Item removed: {character_item.item.blueprint.name} "
            f"({character_item.item.full_code})"
        ),
    )
    db.session.add(audit_log)

    db.session.delete(character_item)
    db.session.commit()

    flash("Item removed successfully.", "success")

    # Redirect back to the page the user came from
    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    elif request.form.get("from_character_edit"):
        # If coming from character edit page, redirect back there
        return redirect(url_for("characters.edit", character_id=character_id))
    else:
        return redirect(url_for("tools_items.character_inventory", character_id=character_id))


@items_bp.route("/transfer-request", methods=["POST"])
@login_required
@email_verified_required
def create_transfer_request():
    """Create a new item transfer request."""

    requesting_character_id = request.form.get("requesting_character_id", type=int)
    target_character_id = request.form.get("target_character_id", type=int)
    item_ids = request.form.getlist("item_ids[]")
    notes = request.form.get("notes", "").strip()

    if not requesting_character_id or not target_character_id or not item_ids:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("tools_items.items_list"))

    # Verify the requesting character belongs to the current user
    requesting_character = Character.query.filter_by(
        id=requesting_character_id, user_id=current_user.id
    ).first()

    if not requesting_character:
        flash("Invalid requesting character.", "error")
        return redirect(url_for("tools_items.items_list"))

    # Verify the target character exists and is active
    target_character = Character.query.filter_by(
        id=target_character_id, status=CharacterStatus.ACTIVE.value
    ).first()

    if not target_character:
        flash("Invalid target character.", "error")
        return redirect(url_for("tools_items.items_list"))

    # Verify all items belong to the requesting character
    character_items = CharacterItem.query.filter(
        CharacterItem.id.in_(item_ids), CharacterItem.character_id == requesting_character_id
    ).all()

    if len(character_items) != len(item_ids):
        flash("Some selected items are not in your inventory.", "error")
        return redirect(url_for("tools_items.items_list"))

    # Create the transfer request
    transfer_request = ItemTransferRequest(
        requesting_character_id=requesting_character_id,
        target_character_id=target_character_id,
        status=ItemTransferStatus.PENDING.value,
        notes=notes if notes else None,
    )

    db.session.add(transfer_request)
    db.session.flush()  # Get the ID

    # Add items to the transfer request
    for character_item in character_items:
        transfer_request_item = ItemTransferRequestItem(
            transfer_request_id=transfer_request.id,
            character_item_id=character_item.id,
        )
        db.session.add(transfer_request_item)

    db.session.commit()

    flash("Transfer request created successfully.", "success")
    return redirect(url_for("tools_items.items_list"))


@items_bp.route("/transfer-request/<int:request_id>/process", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def process_transfer_request(request_id):
    """Process a transfer request (approve or deny)."""

    transfer_request = ItemTransferRequest.query.get_or_404(request_id)
    action = request.form.get("action")
    notes = request.form.get("notes", "")

    if action not in ["approve", "deny"]:
        flash("Invalid action.", "error")
        return redirect(url_for("tools_items.items_list"))

    if action == "approve":
        # Move items from requesting character to target character
        for request_item in transfer_request.items:
            character_item = request_item.character_item

            # Create audit log for requesting character (item removed)
            requesting_audit = CharacterAuditLog(
                character_id=transfer_request.requesting_character_id,
                editor_user_id=current_user.id,
                action=CharacterAuditAction.STATUS_CHANGE.value,
                changes=(
                    f"Item transferred to {transfer_request.target_character.name}: "
                    f"{character_item.item.blueprint.name} ({character_item.item.full_code})"
                ),
            )
            db.session.add(requesting_audit)

            # Create audit log for target character (item received)
            target_audit = CharacterAuditLog(
                character_id=transfer_request.target_character_id,
                editor_user_id=current_user.id,
                action=CharacterAuditAction.STATUS_CHANGE.value,
                changes=(
                    f"Item received from {transfer_request.requesting_character.name}: "
                    f"{character_item.item.blueprint.name} ({character_item.item.full_code})"
                ),
            )
            db.session.add(target_audit)

            # Update the character assignment
            character_item.character_id = transfer_request.target_character_id
            character_item.assigned_by_user_id = current_user.id

            # Remove the transfer request item
            db.session.delete(request_item)

        transfer_request.status = ItemTransferStatus.APPROVED.value
        flash("Transfer request approved.", "success")
    else:
        # Just mark as denied
        transfer_request.status = ItemTransferStatus.DENIED.value
        flash("Transfer request denied.", "success")

    transfer_request.processed_at = db.func.now()
    transfer_request.processed_by_user_id = current_user.id
    transfer_request.notes = notes

    db.session.commit()

    return redirect(url_for("tools_items.items_list"))


@items_bp.route("/api/characters")
@login_required
@email_verified_required
def api_characters():
    """API endpoint for character search (for Select2)."""

    q = request.args.get("q", "").strip()

    # Build query
    query = Character.query.filter_by(status=CharacterStatus.ACTIVE.value)

    if q:
        # Search by character name or player reference
        query = query.filter(
            or_(
                Character.name.ilike(f"%{q}%"),
                and_(
                    Character.user_id.cast(db.String).ilike(f"%{q}%"),
                    Character.character_id.cast(db.String).ilike(f"%{q}%"),
                ),
            )
        )

    characters = query.order_by(Character.name).limit(20).all()

    results = []
    for character in characters:
        player_ref = f"{character.user_id}.{character.character_id}"
        results.append({"id": character.id, "text": f"{character.name} ({player_ref})"})

    return jsonify({"results": results})
