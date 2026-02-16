"""Email notification service."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from app.extensions import db
from app.models.notification import NotificationPreference

logger = logging.getLogger(__name__)


def send_notification(to, subject, html_body):
    """Send an email notification. Falls back to console logging in dev."""
    server = current_app.config.get('MAIL_SERVER')
    port = current_app.config.get('MAIL_PORT', 587)
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'crof@localhost')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(html_body, 'html'))

    if not server:
        logger.info('[DEV EMAIL] To: %s | Subject: %s\n%s', to, subject, html_body)
        return True

    try:
        with smtplib.SMTP(server, port) as smtp:
            smtp.ehlo()
            if port != 25:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.sendmail(sender, [to], msg.as_string())
        return True
    except Exception as e:
        logger.error('Failed to send email to %s: %s', to, e)
        return False


def should_notify(user_id, event_type):
    """Check if user wants notifications for this event type."""
    pref = NotificationPreference.query.filter_by(
        user_id=user_id, event_type=event_type
    ).first()
    if pref is None:
        return True  # default to enabled
    return pref.email_enabled


def notify_scan_complete(user, scan_job):
    """Send scan completion notification if user has it enabled."""
    if not should_notify(user.id, 'scan_complete'):
        return
    try:
        html = render_template('email/scan_complete.html',
                               user=user, scan=scan_job)
        send_notification(user.email, f'CROF: Scan {scan_job.status} - {scan_job.target}', html)
    except Exception as e:
        logger.error('Failed to send scan notification: %s', e)


def notify_backup_result(user, backup_job):
    """Send backup result notification if user has it enabled."""
    if not should_notify(user.id, 'backup_result'):
        return
    try:
        html = render_template('email/backup_result.html',
                               user=user, job=backup_job)
        send_notification(user.email, f'CROF: Backup {backup_job.status} - {backup_job.target_name}', html)
    except Exception as e:
        logger.error('Failed to send backup notification: %s', e)


def notify_assessment_complete(user, assessment):
    """Send assessment completion notification if user has it enabled."""
    if not should_notify(user.id, 'assessment_complete'):
        return
    try:
        html = render_template('email/assessment_complete.html',
                               user=user, assessment=assessment)
        send_notification(user.email, f'CROF: Assessment completed - {assessment.title}', html)
    except Exception as e:
        logger.error('Failed to send assessment notification: %s', e)
