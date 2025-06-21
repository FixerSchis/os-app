from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.enums import CharacterStatus
from models.extensions import db
from models.tools.character import Character
from models.tools.group import Group
from utils.decorators import email_verified_required, user_admin_required

banking_bp = Blueprint("banking", __name__)


@banking_bp.route("/")
@login_required
@email_verified_required
def bank():
    if not current_user.has_role("user_admin") and not current_user.has_active_character():
        flash("You need an active character to access banking", "error")
        return redirect(url_for("characters.character_list"))

    # Get active character for non-admin users
    active_character = None
    if not current_user.has_role("user_admin"):
        active_character = Character.query.filter_by(
            user_id=current_user.id, status=CharacterStatus.ACTIVE.value
        ).first()

    # Get all characters and groups for admin users
    all_characters = []
    all_groups = []
    if current_user.has_role("user_admin"):
        all_characters = Character.query.filter_by(status=CharacterStatus.ACTIVE.value).all()
        all_groups = Group.query.all()

    # Get selected accounts if admin
    selected_character = None
    selected_group = None
    if current_user.has_role("user_admin"):
        character_id = request.args.get("character_id")
        group_id = request.args.get("group_id")

        if character_id:
            selected_character = Character.query.get(character_id)
        if group_id:
            selected_group = Group.query.get(group_id)

    # Get available source accounts for transfer
    source_accounts = []
    if current_user.has_role("user_admin"):
        # Add all character accounts
        for char in all_characters:
            source_accounts.append(
                {
                    "type": "character",
                    "id": char.id,
                    "name": f"{char.name} (Character)",
                    "balance": char.bank_account,
                }
            )
        # Add all group accounts
        for group in all_groups:
            source_accounts.append(
                {
                    "type": "group",
                    "id": group.id,
                    "name": f"{group.name} (Group)",
                    "balance": group.bank_account,
                }
            )
    elif active_character:
        source_accounts.append(
            {
                "type": "character",
                "id": active_character.id,
                "name": f"{active_character.name} (Character)",
                "balance": active_character.bank_account,
            }
        )
        if active_character.group:
            source_accounts.append(
                {
                    "type": "group",
                    "id": active_character.group.id,
                    "name": f"{active_character.group.name} (Group)",
                    "balance": active_character.group.bank_account,
                }
            )

    # Get all target accounts for transfer
    target_accounts = []
    for char in all_characters:
        target_accounts.append(
            {"type": "character", "id": char.id, "name": f"{char.name} (Character)"}
        )
    for group in all_groups:
        target_accounts.append({"type": "group", "id": group.id, "name": f"{group.name} (Group)"})

    return render_template(
        "banking/bank.html",
        active_character=active_character,
        selected_character=selected_character,
        selected_group=selected_group,
        all_characters=all_characters,
        all_groups=all_groups,
        source_accounts=source_accounts,
        target_accounts=target_accounts,
    )


@banking_bp.route("/update-balance", methods=["POST"])
@login_required
@email_verified_required
@user_admin_required
def update_balance():
    account_type = request.form.get("account_type")
    account_id = request.form.get("account_id")
    new_balance = request.form.get("balance")

    try:
        new_balance = int(new_balance)
    except ValueError:
        flash("Invalid balance amount", "error")
        return redirect(url_for("banking.bank"))

    if account_type == "character":
        account = Character.query.get_or_404(account_id)
    else:
        account = Group.query.get_or_404(account_id)

    account.bank_account = new_balance
    db.session.commit()

    flash("Balance updated successfully", "success")
    return redirect(url_for("banking.bank"))


@banking_bp.route("/transfer", methods=["POST"])
@login_required
@email_verified_required
def transfer():
    source_type = request.form.get("source_type")
    source_id = request.form.get("source_id")
    target_type = request.form.get("target_type")
    target_id = request.form.get("target_id")
    amount = request.form.get("amount")

    try:
        amount = int(amount)
    except ValueError:
        flash("Invalid amount", "error")
        return redirect(url_for("banking.bank"))

    if amount <= 0:
        flash("Amount must be positive", "error")
        return redirect(url_for("banking.bank"))

    # Get source account
    if source_type == "character":
        source = Character.query.get_or_404(source_id)
        if not current_user.has_role("user_admin") and source.user_id != current_user.id:
            flash("You do not have access to this account", "error")
            return redirect(url_for("banking.bank"))
    else:
        source = Group.query.get_or_404(source_id)
        if not current_user.has_role("user_admin"):
            active_character = Character.query.filter_by(
                user_id=current_user.id, status=CharacterStatus.ACTIVE.value
            ).first()
            if not active_character or active_character.group_id != source.id:
                flash("You do not have access to this account", "error")
                return redirect(url_for("banking.bank"))

    # Check if source has enough money
    if source.bank_account < amount:
        flash("Insufficient funds", "error")
        return redirect(url_for("banking.bank"))

    # Get target account
    if target_type == "character":
        target = Character.query.get_or_404(target_id)
    else:
        target = Group.query.get_or_404(target_id)

    # Perform transfer
    source.bank_account -= amount
    target.bank_account += amount
    db.session.commit()

    flash("Transfer completed successfully", "success")
    return redirect(url_for("banking.bank"))
