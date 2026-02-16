from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    organisation = db.Column(db.String(200), default='')
    role = db.Column(db.String(20), default='user')  # user, admin, auditor
    is_active = db.Column(db.Boolean, default=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    assessments = db.relationship('Assessment', backref='user', lazy='dynamic')
    reports = db.relationship('Report', backref='user', lazy='dynamic')
    backup_jobs = db.relationship('BackupJob', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'
