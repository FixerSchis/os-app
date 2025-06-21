from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.enums import CharacterStatus
from models.extensions import db
from models.tools.character import Character
from models.tools.message import Message
from utils.decorators import npc_required
from utils.email import send_notification_email

bp = Blueprint("messages", __name__)


@bp.route("/")
@login_required
def messages():
    if current_user.has_role("npc"):
        # For NPCs, show messages that either have no response OR are sent by their
        # active characters
        characters = Character.query.filter_by(status=CharacterStatus.ACTIVE.value).all()
        character_ids = [
            char.id
            for char in current_user.characters
            if char.status == CharacterStatus.ACTIVE.value
        ]

        if character_ids:
            messages = Message.query.filter(
                (Message.response.is_(None)) | (Message.sender_id.in_(character_ids))
            ).all()
        else:
            messages = Message.query.filter(Message.response.is_(None)).all()

        return render_template(
            "messages/npc_messages.html", messages=messages, characters=characters
        )
    else:
        # For regular users, show only their character's messages
        active_character = current_user.get_active_character()
        if not active_character:
            flash("You need an active character to use the messaging system.", "error")
            return redirect(url_for("index"))

        messages = Message.query.filter_by(sender_id=active_character.id).all()
        return render_template("messages/user_messages.html", messages=messages)


@bp.route("/messages/send", methods=["POST"])
@login_required
def send_message():
    if current_user.has_role("npc"):
        sender_id = request.form.get("sender_id")
        paid_in_cash = request.form.get("paid_in_cash") == "true"
    else:
        active_character = current_user.get_active_character()
        if not active_character:
            flash("You need an active character to send messages.", "error")
            return redirect(url_for("messages.messages"))
        sender_id = active_character.id
        paid_in_cash = False

    recipient_name = request.form.get("recipient_name")
    content = request.form.get("content")

    if not all([sender_id, recipient_name, content]):
        flash("All fields are required.", "error")
        return redirect(url_for("messages.messages"))

    sender = Character.query.get(sender_id)
    if not sender:
        flash("Invalid sender.", "error")
        return redirect(url_for("messages.messages"))

    # Check if character can afford the message cost before creating the message
    if not paid_in_cash:
        if not sender.can_afford(10):
            flash("Insufficient funds. Messages cost 10 ec.", "error")
            return redirect(url_for("messages.messages"))

    # Create the message first
    message = Message(sender_id=sender_id, recipient_name=recipient_name, content=content)
    db.session.add(message)

    # Deduct funds only after the message is successfully created
    if not paid_in_cash:
        sender.spend_funds(10, editor_user_id=current_user.id, reason="Send message")

    db.session.commit()

    flash("Message sent successfully!", "success")
    return redirect(url_for("messages.messages"))


@bp.route("/messages/<int:message_id>/respond", methods=["POST"])
@npc_required
def respond_to_message(message_id):
    message = Message.query.get_or_404(message_id)
    response_text = request.form.get("response")

    if not response_text:
        flash("Response cannot be empty.", "error")
        return redirect(url_for("messages.messages"))

    message.add_response(response_text)
    db.session.commit()

    # Add response to character's pack
    if not message.sender.character_pack:
        message.sender.character_pack = {}
    if "messages" not in message.sender.character_pack:
        message.sender.character_pack["messages"] = []

    # Add the response message
    message.sender.character_pack["messages"].append(
        {
            "type": "sms_response",
            "recipient_name": message.recipient_name,
            "question": message.content,
            "response": response_text,
        }
    )

    # Send email notification to the user if they want it
    if message.sender.user:
        send_notification_email(message.sender.user, "message_responded", message=message)

    flash("Response sent successfully!", "success")
    return redirect(url_for("messages.messages"))
