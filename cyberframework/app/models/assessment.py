from datetime import datetime, timezone
from app.extensions import db


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), default='questionnaire')  # questionnaire / scan
    status = db.Column(db.String(20), default='in_progress')  # in_progress / completed
    overall_score = db.Column(db.Float, default=0.0)
    maturity_level = db.Column(db.String(30), default='Initial')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    responses = db.relationship('AssessmentResponse', backref='assessment',
                                lazy='dynamic', cascade='all, delete-orphan')
    scan_jobs = db.relationship('ScanJob', backref='assessment', lazy='dynamic')
    reports = db.relationship('Report', backref='assessment', lazy='dynamic')


class AssessmentResponse(db.Model):
    __tablename__ = 'assessment_responses'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    control_id = db.Column(db.String(20), nullable=False)
    function_id = db.Column(db.String(20), nullable=False)
    answer = db.Column(db.String(10), default='no')  # yes / partial / no / na
    score = db.Column(db.Float, default=0.0)
    evidence_notes = db.Column(db.Text, default='')
