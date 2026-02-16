from datetime import datetime, timezone
from app.extensions import db


class BackupJob(db.Model):
    __tablename__ = 'backup_jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(30), nullable=False)  # rsync/veeam/aws/azure
    target_name = db.Column(db.String(200), nullable=False)
    target_config = db.Column(db.Text, default='')  # encrypted JSON
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    progress = db.Column(db.Integer, default=0)
    log = db.Column(db.Text, default='')
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
