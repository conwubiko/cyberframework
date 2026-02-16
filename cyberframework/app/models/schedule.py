"""Scheduled scan model."""
from datetime import datetime, timezone
from app.extensions import db


class ScanSchedule(db.Model):
    __tablename__ = 'scan_schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    target = db.Column(db.String(200), default='localhost')
    scan_type = db.Column(db.String(50), default='full')
    frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('scan_schedules', lazy='dynamic'))
