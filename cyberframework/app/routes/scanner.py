import threading
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.scan import ScanJob, ScanFinding
from app.models.assessment import Assessment
from app.services.scanner_engine import run_scan, SCAN_MODULES
from app.services.audit import log_action
from datetime import datetime, timezone

scanner_bp = Blueprint('scanner', __name__, url_prefix='/scanner')


@scanner_bp.route('/')
@login_required
def list_scans():
    scans = ScanJob.query.filter_by(user_id=current_user.id).order_by(ScanJob.created_at.desc()).all()
    return render_template('scanner/list.html', scans=scans)


@scanner_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_scan():
    if request.method == 'POST':
        target = request.form.get('target', 'localhost').strip()
        scan_type = request.form.get('scan_type', 'full')

        # Optionally create an associated assessment
        assessment = Assessment(
            user_id=current_user.id,
            organisation_id=current_user.organisation_id,
            title=f"Automated Scan — {target} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            type='scan',
        )
        db.session.add(assessment)
        db.session.flush()

        job = ScanJob(
            user_id=current_user.id,
            organisation_id=current_user.organisation_id,
            assessment_id=assessment.id,
            scan_type=scan_type,
            target=target,
        )
        db.session.add(job)
        db.session.commit()
        log_action(current_user, 'scan_start', 'ScanJob', job.id, f'{scan_type} scan on {target}')

        # Launch scan in background thread
        app = current_app._get_current_object()
        thread = threading.Thread(target=run_scan, args=(job.id, app))
        thread.daemon = True
        thread.start()

        flash('Scan started. Monitoring progress...', 'info')
        return redirect(url_for('scanner.view_scan', scan_id=job.id))

    return render_template('scanner/new.html', modules=SCAN_MODULES)


@scanner_bp.route('/<int:scan_id>')
@login_required
def view_scan(scan_id):
    scan = ScanJob.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('scanner.list_scans'))
    findings = scan.findings.order_by(
        db.case(
            (ScanFinding.severity == 'critical', 0),
            (ScanFinding.severity == 'high', 1),
            (ScanFinding.severity == 'medium', 2),
            (ScanFinding.severity == 'low', 3),
            else_=4
        )
    ).all()
    return render_template('scanner/view.html', scan=scan, findings=findings)


@scanner_bp.route('/<int:scan_id>/status')
@login_required
def scan_status(scan_id):
    scan = ScanJob.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        return jsonify({'error': 'denied'}), 403
    return jsonify({
        'status': scan.status,
        'progress': scan.progress,
    })
