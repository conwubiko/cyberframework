from datetime import datetime, timezone
from app.extensions import db


class ScanJob(db.Model):
    __tablename__ = 'scan_jobs'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=True)
    scan_type = db.Column(db.String(50), default='full')
    target = db.Column(db.String(200), default='localhost')
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    progress = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    findings = db.relationship('ScanFinding', backref='scan_job',
                               lazy='dynamic', cascade='all, delete-orphan')


class ScanFinding(db.Model):
    __tablename__ = 'scan_findings'

    id = db.Column(db.Integer, primary_key=True)
    scan_job_id = db.Column(db.Integer, db.ForeignKey('scan_jobs.id'), nullable=False)
    control_id = db.Column(db.String(20), default='')
    severity = db.Column(db.String(10), default='info')  # critical/high/medium/low/info
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, default='')
    remediation = db.Column(db.Text, default='')
