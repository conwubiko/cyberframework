"""Export routes for CSV and Excel downloads."""
from flask import Blueprint, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.assessment import Assessment
from app.models.scan import ScanJob
from app.services.exporter import (
    export_assessment_csv, export_assessment_excel,
    export_findings_csv, export_findings_excel,
)

export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.route('/assessment/<int:assessment_id>/csv')
@login_required
def assessment_csv(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    data = export_assessment_csv(assessment_id)
    if data is None:
        flash('Assessment not found.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    return Response(
        data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=assessment_{assessment_id}.csv'}
    )


@export_bp.route('/assessment/<int:assessment_id>/excel')
@login_required
def assessment_excel(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    data = export_assessment_excel(assessment_id)
    if data is None:
        flash('Assessment not found.', 'danger')
        return redirect(url_for('assessment.list_assessments'))

    return Response(
        data,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=assessment_{assessment_id}.xlsx'}
    )


@export_bp.route('/scan/<int:scan_id>/csv')
@login_required
def scan_csv(scan_id):
    scan = ScanJob.query.get_or_404(scan_id)
    if scan.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('scanner.list_scans'))

    data = export_findings_csv(scan_id)
    if data is None:
        flash('Scan not found.', 'danger')
        return redirect(url_for('scanner.list_scans'))

    return Response(
        data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=scan_{scan_id}_findings.csv'}
    )


@export_bp.route('/scan/<int:scan_id>/excel')
@login_required
def scan_excel(scan_id):
    scan = ScanJob.query.get_or_404(scan_id)
    if scan.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('scanner.list_scans'))

    data = export_findings_excel(scan_id)
    if data is None:
        flash('Scan not found.', 'danger')
        return redirect(url_for('scanner.list_scans'))

    return Response(
        data,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=scan_{scan_id}_findings.xlsx'}
    )
