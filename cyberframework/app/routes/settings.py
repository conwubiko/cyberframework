"""User settings routes — notification preferences."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import NotificationPreference

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

EVENT_TYPES = [
    ('scan_complete', 'Scan Completion'),
    ('backup_result', 'Backup Result'),
    ('assessment_complete', 'Assessment Completion'),
]


@settings_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        for event_type, _ in EVENT_TYPES:
            enabled = request.form.get(event_type) == 'on'
            pref = NotificationPreference.query.filter_by(
                user_id=current_user.id, event_type=event_type
            ).first()
            if pref:
                pref.email_enabled = enabled
            else:
                pref = NotificationPreference(
                    user_id=current_user.id,
                    event_type=event_type,
                    email_enabled=enabled,
                )
                db.session.add(pref)
        db.session.commit()
        flash('Notification preferences saved.', 'success')
        return redirect(url_for('settings.notifications'))

    prefs = {}
    for pref in NotificationPreference.query.filter_by(user_id=current_user.id).all():
        prefs[pref.event_type] = pref.email_enabled

    return render_template('settings/notifications.html',
                           event_types=EVENT_TYPES, prefs=prefs)
