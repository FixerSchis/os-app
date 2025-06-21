from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.extensions import db, login_manager
from models.enums import Role, CharacterStatus
import secrets
from datetime import datetime, timedelta


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    player_id = db.Column(db.Integer, unique=True, nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=True)
    pronouns_subject = db.Column(db.String(20), nullable=True)
    pronouns_object = db.Column(db.String(20), nullable=True)
    roles = db.Column(
        db.String(255), nullable=False, default=""
    )
    character_points = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    characters = db.relationship('Character', back_populates='user', cascade='all, delete-orphan')
    assigned_tickets = db.relationship('EventTicket', back_populates='assigned_by', foreign_keys='EventTicket.assigned_by_id')
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Email change fields
    new_email = db.Column(db.String(120), nullable=True)
    email_change_token = db.Column(db.String(100), nullable=True)
    email_change_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Notification preferences
    notify_downtime_pack_enter = db.Column(db.Boolean, default=True)
    notify_downtime_completed = db.Column(db.Boolean, default=True)
    notify_new_event = db.Column(db.Boolean, default=True)
    notify_event_ticket_assigned = db.Column(db.Boolean, default=True)
    notify_event_details_updated = db.Column(db.Boolean, default=True)
    notify_wiki_published = db.Column(db.Boolean, default=True)
    
    # Theme preference
    dark_mode_preference = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        roles = (self.roles or "").split(",")
        if role_name == "owner":
            return "owner" in roles
        elif role_name == "admin":
            return "owner" in roles or "admin" in roles
        else:
            return "owner" in roles or "admin" in roles or role_name in roles

    def has_any_role(self, role_names):
        """Check if the user has any of the specified roles."""
        return any(self.has_role(role_name) for role_name in role_names)

    def add_role(self, role_name):
        if role_name in Role.values() and not self.has_role(role_name):
            current_roles = (self.roles or "").split(",") if self.roles else []
            current_roles.append(role_name)
            self.roles = ",".join([r for r in current_roles if r])

    def remove_role(self, role_name):
        if self.has_role(role_name):
            current_roles = (self.roles or "").split(",")
            current_roles = [r for r in current_roles if r and r != role_name]
            self.roles = ",".join(current_roles)

    @property
    def role_list(self):
        return [role for role in (self.roles or "").split(",") if role]

    def add_character_points(self, points):
        """Add character points to the user's total."""
        self.character_points += points

    def can_spend_character_points(self, points):
        """Check if the user has enough character points to spend."""
        return self.character_points >= points

    def spend_character_points(self, points):
        """Spend character points from the user's total."""
        if not self.can_spend_character_points(points):
            raise ValueError("Not enough character points")
        self.character_points -= points

    def has_active_character(self):
        """Check if the user has any active characters."""
        from models.tools.character import Character
        return Character.query.filter_by(
            user_id=self.id,
            status=CharacterStatus.ACTIVE.value
        ).first() is not None
    
    def get_active_character(self):
        """Get the user's active character."""
        from models.tools.character import Character
        return Character.query.filter_by(
            user_id=self.id,
            status=CharacterStatus.ACTIVE.value
        ).first()
        
    def generate_verification_token(self):
        """Generate a new email verification token."""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token
    
    def verify_email(self, token):
        """Verify the user's email with the given token."""
        if (self.verification_token and 
            self.verification_token == token and 
            self.verification_token_expires > datetime.utcnow()):
            self.email_verified = True
            self.verification_token = None
            self.verification_token_expires = None
            return True
        return False
        
    def is_verified(self):
        """Check if the user's email is verified."""
        return self.email_verified
    
    def request_email_change(self, new_email):
        """Request to change the user's email address."""
        if new_email == self.email:
            return False, "New email is the same as current email"
        
        if User.query.filter_by(email=new_email).first():
            return False, "Email address is already in use"
        
        self.new_email = new_email
        self.email_change_token = secrets.token_urlsafe(32)
        self.email_change_token_expires = datetime.utcnow() + timedelta(hours=24)
        return True, self.email_change_token
    
    def confirm_email_change(self, token):
        """Confirm the email change with the given token."""
        if (self.email_change_token and 
            self.email_change_token == token and 
            self.email_change_token_expires > datetime.utcnow() and
            self.new_email):
            
            # Update email address
            self.email = self.new_email
            self.new_email = None
            self.email_change_token = None
            self.email_change_token_expires = None
            return True
        return False
    
    def generate_reset_token(self):
        """Generate a password reset token."""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify that the reset token is valid."""
        if (self.reset_token and 
            self.reset_token == token and 
            self.reset_token_expires > datetime.utcnow()):
            return True
        return False
    
    def reset_password(self, token, new_password):
        """Reset the user's password with the given token."""
        if self.verify_reset_token(token):
            self.set_password(new_password)
            self.reset_token = None
            self.reset_token_expires = None
            return True
        return False

    def should_notify(self, notification_type):
        """Check if the user should receive a specific type of notification."""
        if not self.email_verified:
            return False
        notification_map = {
            'downtime_pack_enter': self.notify_downtime_pack_enter,
            'downtime_completed': self.notify_downtime_completed,
            'new_event': self.notify_new_event,
            'event_ticket_assigned': self.notify_event_ticket_assigned,
            'event_details_updated': self.notify_event_details_updated,
            'wiki_published': self.notify_wiki_published
        }
        return notification_map.get(notification_type, False)

    def update_notification_preferences(self, preferences):
        """Update notification preferences from a dictionary."""
        for key, value in preferences.items():
            if hasattr(self, f'notify_{key}'):
                setattr(self, f'notify_{key}', bool(value))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
