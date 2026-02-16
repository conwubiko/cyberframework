import threading
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.backup import BackupJob
from app.services.backup_orchestrator import run_backup, encrypt_config
from app.services.audit import log_action

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')


@backup_bp.route('/')
@login_required
def list_jobs():
    jobs = BackupJob.query.filter_by(user_id=current_user.id).order_by(BackupJob.created_at.desc()).all()
    return render_template('backup/list.html', jobs=jobs)


@backup_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if not current_user.is_admin:
        flash('Admin access required for backup operations.', 'danger')
        return redirect(url_for('backup.list_jobs'))

    if request.method == 'POST':
        provider = request.form.get('provider', 'rsync')
        target_name = request.form.get('target_name', '').strip()

        config = {}
        if provider == 'rsync':
            config = {
                'source': request.form.get('rsync_source', '.'),
                'destination': request.form.get('rsync_dest', '/tmp/backup'),
                'options': request.form.get('rsync_options', '-avz'),
            }
        elif provider == 'veeam':
            config = {
                'host': request.form.get('veeam_host', ''),
                'port': int(request.form.get('veeam_port', 9419)),
                'username': request.form.get('veeam_user', ''),
                'password': request.form.get('veeam_pass', ''),
                'job_name': request.form.get('veeam_job', ''),
            }
        elif provider == 'aws':
            config = {
                'access_key': request.form.get('aws_key', ''),
                'secret_key': request.form.get('aws_secret', ''),
                'region': request.form.get('aws_region', 'us-east-1'),
                'vault_name': request.form.get('aws_vault', 'Default'),
                'resource_arn': request.form.get('aws_arn', ''),
                'iam_role_arn': request.form.get('aws_role', ''),
            }

        encrypted_config = encrypt_config(config)

        job = BackupJob(
            user_id=current_user.id,
            provider=provider,
            target_name=target_name or f"{provider} backup",
            target_config=encrypted_config,
        )
        db.session.add(job)
        db.session.commit()
        log_action(current_user, 'backup_start', 'BackupJob', job.id, f'{provider}: {target_name}')

        app = current_app._get_current_object()
        thread = threading.Thread(target=run_backup, args=(job.id, app))
        thread.daemon = True
        thread.start()

        flash('Backup job started.', 'info')
        return redirect(url_for('backup.view_job', job_id=job.id))

    return render_template('backup/new.html')


@backup_bp.route('/<int:job_id>')
@login_required
def view_job(job_id):
    job = BackupJob.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('backup.list_jobs'))
    return render_template('backup/view.html', job=job)


@backup_bp.route('/<int:job_id>/status')
@login_required
def job_status(job_id):
    job = BackupJob.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        return jsonify({'error': 'denied'}), 403
    return jsonify({
        'status': job.status,
        'progress': job.progress,
    })
