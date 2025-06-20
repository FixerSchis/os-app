from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.extensions import db
from models.tools.user import User
from utils.email import send_email_change_verification

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'notifications':
            # Handle notification preferences
            notification_preferences = {
                'downtime_pack_enter': request.form.get('notify_downtime_pack_enter') == '1',
                'downtime_completed': request.form.get('notify_downtime_completed') == '1',
                'new_event': request.form.get('notify_new_event') == '1',
                'event_ticket_assigned': request.form.get('notify_event_ticket_assigned') == '1',
                'event_details_updated': request.form.get('notify_event_details_updated') == '1',
                'wiki_published': request.form.get('notify_wiki_published') == '1'
            }
            current_user.update_notification_preferences(notification_preferences)
            db.session.commit()
            flash('Notification preferences updated successfully')
        else:
            # Handle profile information
            current_user.first_name = request.form.get('first_name')
            current_user.surname = request.form.get('surname')
            current_user.pronouns_subject = request.form.get('pronouns_subject')
            current_user.pronouns_object = request.form.get('pronouns_object')
            db.session.commit()
            flash('Settings updated successfully')
        
        return redirect(url_for('settings.settings'))
    return render_template('settings/settings.html')

@settings_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        password = request.form.get('password')
        
        # Validate inputs
        if not new_email or not password:
            flash('Both email and password are required', 'error')
            return render_template('settings/change_email.html')
            
        # Check password
        if not current_user.check_password(password):
            flash('Incorrect password', 'error')
            return render_template('settings/change_email.html')
            
        # Request email change
        success, message_or_token = current_user.request_email_change(new_email)
        
        if success:
            try:
                send_email_change_verification(current_user, message_or_token, new_email)
                db.session.commit()
                flash('Verification email sent to your new email address. Please check your inbox and confirm the change.', 'success')
                return redirect(url_for('settings.settings'))
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to send verification email: {str(e)}', 'error')
                return render_template('settings/change_email.html')
        else:
            flash(message_or_token, 'error')
            return render_template('settings/change_email.html')
            
    return render_template('settings/change_email.html')

@settings_bp.route('/change-email/<token>')
@login_required
def confirm_email_change(token):
    success, old_email = current_user.confirm_email_change(token)
    
    if success:
        db.session.commit()
        flash(f'Your email has been successfully changed from {old_email} to {current_user.email}', 'success')
    else:
        flash('The verification link is invalid or has expired.', 'error')
        
    return redirect(url_for('settings.settings')) 