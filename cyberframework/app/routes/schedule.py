"""Scheduled scan routes."""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.schedule import ScanSchedule
from app.services.audit import log_action

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


@schedule_bp.route('/')
@login_required
def list_schedules():
    schedules = ScanSchedule.query.filter_by(
        user_id=current_user.id
    ).order_by(ScanSchedule.created_at.desc()).all()
    return render_template('schedule/list.html', schedules=schedules)


@schedule_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_schedule():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        target = request.form.get('target', 'localhost').strip()
        scan_type = request.form.get('scan_type', 'full')
        frequency = request.form.get('frequency', 'daily')

        if not name:
            flash('Schedule name is required.', 'danger')
            return render_template('schedule/new.html')

        now = datetime.now(timezone.utc)
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        else:
            next_run = now + timedelta(days=30)

        schedule = ScanSchedule(
            user_id=current_user.id,
            name=name,
            target=target,
            scan_type=scan_type,
            frequency=frequency,
            next_run=next_run,
        )
        db.session.add(schedule)
        db.session.commit()
        log_action(current_user, 'schedule_create', 'ScanSchedule', schedule.id, name)
        flash(f'Schedule "{name}" created. Next run: {next_run.strftime("%Y-%m-%d %H:%M")} UTC', 'success')
        return redirect(url_for('schedule.list_schedules'))

    return render_template('schedule/new.html')


@schedule_bp.route('/<int:schedule_id>/toggle', methods=['POST'])
@login_required
def toggle_schedule(schedule_id):
    schedule = ScanSchedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('schedule.list_schedules'))

    schedule.is_active = not schedule.is_active
    db.session.commit()
    status = 'activated' if schedule.is_active else 'paused'
    flash(f'Schedule "{schedule.name}" {status}.', 'success')
    return redirect(url_for('schedule.list_schedules'))


@schedule_bp.route('/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    schedule = ScanSchedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('schedule.list_schedules'))

    name = schedule.name
    log_action(current_user, 'schedule_delete', 'ScanSchedule', schedule.id, name)
    db.session.delete(schedule)
    db.session.commit()
    flash(f'Schedule "{name}" deleted.', 'info')
    return redirect(url_for('schedule.list_schedules'))
