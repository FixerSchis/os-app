from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from utils.notifications import get_user_notifications

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/api/notifications")
@login_required
def get_notifications():
    """Get notifications for the current user."""
    notifications = get_user_notifications()
    return jsonify({"notifications": notifications, "count": len(notifications)})
