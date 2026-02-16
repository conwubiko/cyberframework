"""Audit log model for tracking user actions."""
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), default='')
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))
