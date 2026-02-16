"""Audit logging service."""
from flask import request
from app.extensions import db
from app.models.audit import AuditLog


def log_action(user, action, target_type='', target_id=None, details=''):
    """Record an audit log entry."""
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.remote_addr or '' if request else '',
    )
    db.session.add(entry)
    db.session.commit()
