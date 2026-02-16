import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, request
from flask_login import login_required, current_user
from app.models.assessment import Assessment
from app.models.report import Report
from app.services.report_generator import generate_report
from app.services.audit import log_action
from app.extensions import db

report_bp = Blueprint('report', __name__, url_prefix='/report')


@report_bp.route('/')
@login_required
def list_reports():
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template('report/list.html', reports=reports)


@report_bp.route('/generate/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
def generate(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('report.list_reports'))
    if assessment.status != 'completed':
        flash('Assessment must be completed first.', 'warning')
        return redirect(url_for('assessment.view_assessment', assessment_id=assessment_id))

    if request.method == 'POST':
        fmt = request.form.get('format', 'pdf')
        report = generate_report(assessment_id, current_user.id, fmt)
        if report:
            log_action(current_user, 'report_generate', 'Report', report.id, report.title)
            flash(f'Report generated successfully ({report.format.upper()}).', 'success')
            return redirect(url_for('report.list_reports'))
        flash('Failed to generate report.', 'danger')
        return redirect(url_for('report.generate', assessment_id=assessment_id))

    return render_template('report/generate.html', assessment=assessment)


@report_bp.route('/download/<int:report_id>')
@login_required
def download(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('report.list_reports'))
    if not os.path.exists(report.file_path):
        flash('Report file not found.', 'danger')
        return redirect(url_for('report.list_reports'))
    return send_file(report.file_path, as_attachment=True)


@report_bp.route('/view/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('report.list_reports'))
    if report.format == 'html' and os.path.exists(report.file_path):
        with open(report.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    return redirect(url_for('report.download', report_id=report_id))


@report_bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('report.list_reports'))
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted.', 'info')
    return redirect(url_for('report.list_reports'))
