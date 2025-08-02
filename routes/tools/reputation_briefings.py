from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.database.faction import Faction
from models.database.reputation_briefing import ReputationBriefing, ReputationBriefingLevel
from models.enums import CharacterStatus, ReputationBriefingStatus
from models.event import Event
from models.extensions import db
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.user import User
from utils.decorators import email_verified_required
from utils.email import send_notification_email
from utils.permission_decorators import permission_required

reputation_briefings_bp = Blueprint("reputation_briefings", __name__)


@reputation_briefings_bp.route("/")
@login_required
@email_verified_required
def index():
    """List reputation briefings - admin view for plot team, user view for regular users."""
    if current_user.has_permission("plot.reputation_briefings"):
        # Admin view - show all briefings
        briefings = ReputationBriefing.get_by_status_order()
        return render_template(
            "tools/reputation_briefings/admin_list.html",
            briefings=briefings,
            ReputationBriefingStatus=ReputationBriefingStatus,
        )
    else:
        # User view - show only briefings they can access
        user_briefings = []
        for character in Character.query.filter_by(
            user_id=current_user.id, status=CharacterStatus.ACTIVE.value
        ).all():
            for briefing in ReputationBriefing.query.filter_by(
                status=ReputationBriefingStatus.SUBMITTED.value
            ).all():
                # Check if character meets criteria
                character_reputation = character.get_reputation(briefing.faction_id)
                if character_reputation > 0:
                    min_reputation = min(level.reputation_required for level in briefing.levels)
                    if character_reputation >= min_reputation:
                        # Check if character has a ticket for this event
                        ticket = EventTicket.query.filter_by(
                            event_id=briefing.event_id, character_id=character.id
                        ).first()
                        if ticket:
                            user_briefings.append(
                                {
                                    "briefing": briefing,
                                    "character": character,
                                    "max_level": max(
                                        level.reputation_required
                                        for level in briefing.levels
                                        if character_reputation >= level.reputation_required
                                    ),
                                }
                            )

        return render_template(
            "tools/reputation_briefings/user_list.html",
            briefings=user_briefings,
        )


@reputation_briefings_bp.route("/create", methods=["GET", "POST"])
@login_required
@email_verified_required
@permission_required(permissions=["plot.reputation_briefings"])
def create():
    """Create a new reputation briefing."""
    if request.method == "POST":
        event_id = request.form.get("event_id")
        faction_id = request.form.get("faction_id")
        subject = request.form.get("subject")
        action = request.form.get("action")

        if not all([event_id, faction_id, subject]):
            flash("All fields are required", "error")
            return redirect(url_for("reputation_briefings.create"))

        # Create the briefing
        briefing = ReputationBriefing(
            event_id=event_id,
            faction_id=faction_id,
            subject=subject,
            created_by_user_id=current_user.id,
        )

        # Process levels
        level_count = 0
        for i in range(10):  # Allow up to 10 levels
            reputation_required = request.form.get(f"reputation_required_{i}")
            content = request.form.get(f"content_{i}")

            if reputation_required and content:
                try:
                    reputation_required = int(reputation_required)
                    if reputation_required < 1:
                        flash(f"Reputation required must be at least 1 for level {i + 1}", "error")
                        return redirect(url_for("reputation_briefings.create"))
                except ValueError:
                    flash(f"Reputation required must be a number for level {i + 1}", "error")
                    return redirect(url_for("reputation_briefings.create"))

                level = ReputationBriefingLevel(
                    reputation_required=reputation_required,
                    content=content,
                )
                briefing.levels.append(level)
                level_count += 1

        if level_count == 0:
            flash("At least one level is required", "error")
            return redirect(url_for("reputation_briefings.create"))

        # Set status based on action
        if action == "save_and_send":
            briefing.status = ReputationBriefingStatus.SUBMITTED.value
            db.session.add(briefing)
            db.session.commit()

            # Send notifications
            _send_briefing_notifications(briefing)

            flash("Briefing created and sent successfully", "success")
        else:  # save_as_draft
            briefing.status = ReputationBriefingStatus.INCOMPLETE.value
            db.session.add(briefing)
            db.session.commit()
            flash("Briefing saved as draft", "success")

        return redirect(url_for("reputation_briefings.index"))

    # GET request - show form
    events = Event.query.order_by(Event.start_date.desc()).all()
    factions = Faction.query.order_by(Faction.name).all()

    return render_template(
        "tools/reputation_briefings/create.html",
        events=events,
        factions=factions,
    )


@reputation_briefings_bp.route("/<int:briefing_id>/edit", methods=["GET"])
@login_required
@email_verified_required
@permission_required(permissions=["plot.reputation_briefings"])
def edit(briefing_id):
    """Edit an incomplete reputation briefing."""
    briefing = ReputationBriefing.query.get_or_404(briefing_id)

    if not briefing.can_edit(current_user):
        flash("This briefing cannot be edited", "error")
        return redirect(url_for("reputation_briefings.index"))

    if request.method == "POST":
        event_id = request.form.get("event_id")
        faction_id = request.form.get("faction_id")
        subject = request.form.get("subject")
        action = request.form.get("action")

        if not all([event_id, faction_id, subject]):
            flash("All fields are required", "error")
            return redirect(url_for("reputation_briefings.edit", briefing_id=briefing_id))

        # Update briefing
        briefing.event_id = event_id
        briefing.faction_id = faction_id
        briefing.subject = subject

        # Clear existing levels
        for level in briefing.levels:
            db.session.delete(level)

        # Process levels
        level_count = 0
        for i in range(10):  # Allow up to 10 levels
            reputation_required = request.form.get(f"reputation_required_{i}")
            content = request.form.get(f"content_{i}")

            if reputation_required and content:
                try:
                    reputation_required = int(reputation_required)
                    if reputation_required < 1:
                        flash(f"Reputation required must be at least 1 for level {i + 1}", "error")
                        return redirect(
                            url_for("reputation_briefings.edit", briefing_id=briefing_id)
                        )
                except ValueError:
                    flash(f"Reputation required must be a number for level {i + 1}", "error")
                    return redirect(url_for("reputation_briefings.edit", briefing_id=briefing_id))

                level = ReputationBriefingLevel(
                    reputation_required=reputation_required,
                    content=content,
                )
                briefing.levels.append(level)
                level_count += 1

        if level_count == 0:
            flash("At least one level is required", "error")
            return redirect(url_for("reputation_briefings.edit", briefing_id=briefing_id))

        # Set status based on action
        if action == "discard":
            briefing.status = ReputationBriefingStatus.DISCARDED.value
            flash("Briefing discarded", "success")
        elif action == "save_and_send":
            briefing.status = ReputationBriefingStatus.SUBMITTED.value
            db.session.commit()

            # Send notifications
            _send_briefing_notifications(briefing)

            flash("Briefing updated and sent successfully", "success")
        else:  # save_as_draft
            briefing.status = ReputationBriefingStatus.INCOMPLETE.value
            flash("Briefing saved as draft", "success")

        db.session.commit()
        return redirect(url_for("reputation_briefings.index"))

    # GET request - show form
    events = Event.query.order_by(Event.start_date.desc()).all()
    factions = Faction.query.order_by(Faction.name).all()

    return render_template(
        "tools/reputation_briefings/edit.html",
        briefing=briefing,
        events=events,
        factions=factions,
    )


@reputation_briefings_bp.route("/<int:briefing_id>/reopen")
@login_required
@email_verified_required
@permission_required(permissions=["plot.reputation_briefings"])
def reopen(briefing_id):
    """Reopen a discarded briefing."""
    briefing = ReputationBriefing.query.get_or_404(briefing_id)
    if briefing.status != ReputationBriefingStatus.DISCARDED:
        flash("Only discarded briefings can be reopened", "error")
        return redirect(url_for("reputation_briefings.index"))

    briefing.status = ReputationBriefingStatus.INCOMPLETE
    db.session.commit()
    flash("Briefing reopened", "success")
    return redirect(url_for("reputation_briefings.index"))


@reputation_briefings_bp.route("/<int:briefing_id>/view")
@login_required
@email_verified_required
def view(briefing_id):
    """View a reputation briefing."""
    briefing = ReputationBriefing.query.get_or_404(briefing_id)

    if not briefing.can_view(current_user):
        flash("You do not have permission to view this briefing", "error")
        return redirect(url_for("reputation_briefings.index"))

    # For regular users, check if they have a character that meets the criteria
    if not current_user.has_permission("plot.reputation_briefings"):
        user_characters = Character.query.filter_by(
            user_id=current_user.id, status=CharacterStatus.ACTIVE.value
        ).all()

        eligible_character = None
        for character in user_characters:
            character_reputation = character.get_reputation(briefing.faction_id)
            if character_reputation > 0:
                min_reputation = min(level.reputation_required for level in briefing.levels)
                if character_reputation >= min_reputation:
                    # Check if character has a ticket for this event
                    ticket = EventTicket.query.filter_by(
                        event_id=briefing.event_id, character_id=character.id
                    ).first()
                    if ticket:
                        eligible_character = character
                        break

        if not eligible_character:
            flash("You do not have permission to view this briefing", "error")
            return redirect(url_for("reputation_briefings.index"))

        # Get the maximum level the character can see
        character_reputation = eligible_character.get_reputation(briefing.faction_id)
        available_levels = [
            level for level in briefing.levels if level.reputation_required <= character_reputation
        ]

        return render_template(
            "tools/reputation_briefings/view.html",
            briefing=briefing,
            character=eligible_character,
            available_levels=available_levels,
            ReputationBriefingStatus=ReputationBriefingStatus,
        )

    # Admin view - show all levels
    return render_template(
        "tools/reputation_briefings/view.html",
        briefing=briefing,
        character=None,
        available_levels=briefing.levels,
        ReputationBriefingStatus=ReputationBriefingStatus,
    )


def _send_briefing_notifications(briefing):
    """Send notifications to eligible characters when a briefing is submitted."""
    eligible_characters = briefing.get_eligible_characters()

    for character in eligible_characters:
        user = character.user
        if user.should_notify("reputation_briefing"):
            # Get the levels this character can see
            character_reputation = character.get_reputation(briefing.faction_id)
            available_levels = [
                level
                for level in briefing.levels
                if level.reputation_required <= character_reputation
            ]

            send_notification_email(
                user,
                "reputation_briefing",
                briefing=briefing,
                character=character,
                available_levels=available_levels,
            )
