"""Organisation model for multi-tenancy."""
from datetime import datetime, timezone
from app.extensions import db


class Organisation(db.Model):
    __tablename__ = 'organisations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship('User', backref='org', lazy='dynamic')
