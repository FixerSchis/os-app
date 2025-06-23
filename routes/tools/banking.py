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
    # --- Data for Transfer Target Dropdown (always all active accounts) ---
    all_characters = Character.query.filter_by(status=CharacterStatus.ACTIVE.value).all()
    all_groups = Group.query.all()
    target_accounts = []
    for char in all_characters:
        target_accounts.append(
            {"type": "character", "id": char.id, "name": f"{char.name} (Character)"}
        )
    for group in all_groups:
        target_accounts.append({"type": "group", "id": group.id, "name": f"{group.name} (Group)"})

    # --- Logic for Admins ---
    if current_user.has_role("user_admin"):
        source_accounts = target_accounts  # Admins can source from any account
        return render_template(
            "banking/bank.html",
            characters_for_select=all_characters,
            groups_for_select=all_groups,
            source_accounts=source_accounts,
            target_accounts=target_accounts,
        )

    # --- Logic for non-admins ---
    user_characters = Character.query.filter_by(
        user_id=current_user.id, status=CharacterStatus.ACTIVE.value
    ).all()

    if not user_characters:
        flash("You need an active character to access banking", "error")
        return redirect(url_for("characters.character_list"))

    user_groups = list({char.group for char in user_characters if char.group})
    source_accounts = []
    for char in user_characters:
        source_accounts.append(
            {
                "type": "character",
                "id": char.id,
                "name": f"{char.name} (Character)",
                "balance": char.bank_account,
            }
        )
    for group in user_groups:
        source_accounts.append(
            {
                "type": "group",
                "id": group.id,
                "name": f"{group.name} (Group)",
                "balance": group.bank_account,
            }
        )

    # --- Multiple active characters ---
    if len(user_characters) > 1:
        return render_template(
            "banking/bank.html",
            characters_for_select=user_characters,
            groups_for_select=user_groups,
            source_accounts=source_accounts,
            target_accounts=target_accounts,
        )

    # --- Single active character ---
    single_character = user_characters[0]
    show_source_dropdown = single_character.group is not None

    return render_template(
        "banking/bank.html",
        active_character=single_character,
        active_character_group=single_character.group,
        show_source_dropdown=show_source_dropdown,
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
        old_balance = account.bank_account
        if new_balance != old_balance:
            account.set_funds(new_balance, current_user.id, "Admin balance update")
    else:
        account = Group.query.get_or_404(account_id)
        old_balance = account.bank_account
        if new_balance != old_balance:
            account.set_funds(new_balance, current_user.id, "Admin balance update")

    db.session.commit()
    flash("Balance updated successfully", "success")
    return redirect(url_for("banking.bank"))


@banking_bp.route("/transfer", methods=["POST"])
@login_required
@email_verified_required
def transfer():
    source_type = request.form.get("source_type_hidden")
    source_id = request.form.get("source_id_hidden")
    target_type = request.form.get("target_type_hidden")
    target_id = request.form.get("target_id_hidden")
    amount = request.form.get("amount")

    # This handles the case for a single character with no group,
    # where the hidden fields aren't used.
    if not source_type and not source_id:
        source_type = request.form.get("source_type")
        source_id = request.form.get("source_id")

    try:
        amount = int(amount)
    except (ValueError, TypeError):
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
        source_name = source.name
    else:
        source = Group.query.get_or_404(source_id)
        if not current_user.has_role("user_admin"):
            active_character = Character.query.filter_by(
                user_id=current_user.id, status=CharacterStatus.ACTIVE.value
            ).first()
            if not active_character or active_character.group_id != source.id:
                flash("You do not have access to this account", "error")
                return redirect(url_for("banking.bank"))
        source_name = source.name

    # Check if source has enough money
    if source.bank_account < amount:
        flash("Insufficient funds", "error")
        return redirect(url_for("banking.bank"))

    # Get target account
    if target_type == "character":
        target = Character.query.get_or_404(target_id)
        target_name = target.name
    else:
        target = Group.query.get_or_404(target_id)
        target_name = target.name

    # Perform transfer using centralized methods
    if source_type == "character":
        # Remove funds from source character
        source.remove_funds(amount, current_user.id, f"Transfer to {target_name}")
    else:
        # Source is a group
        source.remove_funds(amount, current_user.id, f"Transfer to {target_name}")

    if target_type == "character":
        # Add funds to target character
        target.add_funds(amount, current_user.id, f"Transfer from {source_name}")
    else:
        # Add funds to target group
        target.add_funds(amount, current_user.id, f"Transfer from {source_name}")

    db.session.commit()

    flash("Transfer completed successfully", "success")
    return redirect(url_for("banking.bank"))
