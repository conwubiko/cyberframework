from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.assessment import Assessment
from app.models.scan import ScanJob
from app.models.report import Report
from app.models.backup import BackupJob

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at.desc()).all()
    scan_jobs = ScanJob.query.filter_by(user_id=current_user.id).order_by(ScanJob.created_at.desc()).limit(5).all()
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).limit(5).all()
    backup_jobs = BackupJob.query.filter_by(user_id=current_user.id).order_by(BackupJob.created_at.desc()).limit(5).all()

    completed_assessments = [a for a in assessments if a.status == 'completed']
    latest = completed_assessments[0] if completed_assessments else None

    return render_template('dashboard/index.html',
                           assessments=assessments,
                           scan_jobs=scan_jobs,
                           reports=reports,
                           backup_jobs=backup_jobs,
                           latest_assessment=latest,
                           total_assessments=len(assessments),
                           total_scans=len(scan_jobs),
                           total_reports=len(reports))
