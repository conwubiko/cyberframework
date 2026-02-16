"""Notification preference model."""
from app.extensions import db


class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # scan_complete, backup_result, assessment_complete
    email_enabled = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('notification_preferences', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_type', name='uq_user_event'),
    )
