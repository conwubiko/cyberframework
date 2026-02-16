from datetime import datetime, timezone
from app.extensions import db


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    format = db.Column(db.String(10), default='pdf')  # pdf / html
    file_path = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
