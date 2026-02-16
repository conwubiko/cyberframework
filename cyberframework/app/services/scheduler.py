"""Background scheduler for automated scans."""
import time
import threading
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def _calc_next_run(frequency, from_time=None):
    """Calculate the next run time based on frequency."""
    now = from_time or datetime.now(timezone.utc)
    if frequency == 'daily':
        return now + timedelta(days=1)
    elif frequency == 'weekly':
        return now + timedelta(weeks=1)
    elif frequency == 'monthly':
        return now + timedelta(days=30)
    return now + timedelta(days=1)


def _check_schedules(app):
    """Check for due schedules and trigger scans."""
    from app.extensions import db
    from app.models.schedule import ScanSchedule
    from app.models.scan import ScanJob
    from app.models.assessment import Assessment
    from app.services.scanner_engine import run_scan

    with app.app_context():
        now = datetime.now(timezone.utc)
        due = ScanSchedule.query.filter(
            ScanSchedule.is_active == True,
            ScanSchedule.next_run <= now
        ).all()

        for schedule in due:
            try:
                # Create assessment for scan
                assessment = Assessment(
                    user_id=schedule.user_id,
                    organisation_id=None,
                    title=f"Scheduled Scan - {schedule.name} - {now.strftime('%Y-%m-%d %H:%M')}",
                    type='scan',
                )
                db.session.add(assessment)
                db.session.flush()

                job = ScanJob(
                    user_id=schedule.user_id,
                    assessment_id=assessment.id,
                    scan_type=schedule.scan_type,
                    target=schedule.target,
                )
                db.session.add(job)

                schedule.last_run = now
                schedule.next_run = _calc_next_run(schedule.frequency, now)
                db.session.commit()

                # Run scan in background thread
                thread = threading.Thread(target=run_scan, args=(job.id, app))
                thread.daemon = True
                thread.start()

                logger.info('Scheduled scan triggered: %s (job %d)', schedule.name, job.id)
            except Exception as e:
                logger.error('Failed to trigger scheduled scan %s: %s', schedule.name, e)
                db.session.rollback()


def start_scheduler(app):
    """Start the background scheduler thread."""
    def _loop():
        while True:
            try:
                _check_schedules(app)
            except Exception as e:
                logger.error('Scheduler error: %s', e)
            time.sleep(60)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    logger.info('Scan scheduler started.')
