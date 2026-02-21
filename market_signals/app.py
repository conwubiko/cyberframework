"""
Market Signals Alert Web App
Flask application factory, routes, and APScheduler initialization.
"""

import logging
import pytz
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config
from models import db, AlertHistory, AlertCooldown, AlertRecipient
from notifications.sms import send_sms
from notifications.email_alert import send_email, build_alert_email, build_test_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")


def _is_market_hours() -> bool:
    """Return True if current ET time is within 9:15 AM – 4:15 PM on a weekday."""
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now_et.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=15, second=0, microsecond=0)
    return market_open <= now_et <= market_close


def _scheduled_check(app: Flask) -> None:
    if not _is_market_hours():
        logger.debug("Outside market hours — skipping scheduled check")
        return
    with app.app_context():
        from checker import run_check
        try:
            run_check()
        except Exception:
            logger.exception("Scheduled check failed")


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Database ─────────────────────────────────────────────────────────
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ── Scheduler ────────────────────────────────────────────────────────
    scheduler = BackgroundScheduler(timezone=ET)
    scheduler.add_job(
        func=lambda: _scheduled_check(app),
        trigger=IntervalTrigger(minutes=app.config["CHECK_INTERVAL_MINUTES"]),
        id="market_check",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    app.scheduler = scheduler

    # ── Routes ───────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        from checker import run_check
        try:
            status = run_check()
            return jsonify({"ok": True, "data": status})
        except Exception as exc:
            logger.exception("Status check failed")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/alerts")
    def api_alerts():
        limit = min(int(request.args.get("limit", 50)), 200)
        alerts = (
            AlertHistory.query.order_by(AlertHistory.timestamp.desc())
            .limit(limit)
            .all()
        )
        return jsonify({"ok": True, "data": [a.to_dict() for a in alerts]})

    @app.route("/api/check", methods=["POST"])
    def api_check():
        from checker import run_check
        try:
            result = run_check()
            return jsonify({"ok": True, "data": result})
        except Exception as exc:
            logger.exception("Manual check failed")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        mutable_keys = [
            "VIX_THRESHOLD",
            "FEAR_GREED_THRESHOLD",
            "RSI_THRESHOLD",
            "CAPITULATION_SCORE_THRESHOLD",
            "ALERT_COOLDOWN_HOURS",
            "CHECK_INTERVAL_MINUTES",
        ]
        if request.method == "GET":
            return jsonify(
                {"ok": True, "data": {k: app.config[k] for k in mutable_keys}}
            )

        payload = request.get_json(force=True, silent=True) or {}
        updated = {}
        for key in mutable_keys:
            if key in payload:
                try:
                    app.config[key] = float(payload[key]) if "." in str(payload[key]) else int(payload[key])
                    updated[key] = app.config[key]
                except (ValueError, TypeError):
                    pass
        return jsonify({"ok": True, "updated": updated})

    @app.route("/admin")
    def admin():
        return render_template("admin.html")

    # ── Recipient CRUD ────────────────────────────────────────────────────

    @app.route("/api/recipients", methods=["GET"])
    def api_recipients_list():
        recipients = AlertRecipient.query.order_by(AlertRecipient.id).all()
        return jsonify({"ok": True, "data": [r.to_dict() for r in recipients]})

    @app.route("/api/recipients", methods=["POST"])
    def api_recipients_add():
        payload = request.get_json(force=True, silent=True) or {}
        name  = (payload.get("name") or "").strip()
        email = (payload.get("email") or "").strip().lower()

        if not name or not email or "@" not in email:
            return jsonify({"ok": False, "error": "Valid name and email required"}), 400

        if AlertRecipient.query.filter_by(email=email).first():
            return jsonify({"ok": False, "error": "Email already exists"}), 409

        recipient = AlertRecipient(name=name, email=email, active=True)
        db.session.add(recipient)
        db.session.commit()
        return jsonify({"ok": True, "data": recipient.to_dict()}), 201

    @app.route("/api/recipients/<int:rid>", methods=["DELETE"])
    def api_recipients_delete(rid):
        recipient = db.session.get(AlertRecipient, rid)
        if not recipient:
            return jsonify({"ok": False, "error": "Recipient not found"}), 404
        db.session.delete(recipient)
        db.session.commit()
        return jsonify({"ok": True})

    @app.route("/api/recipients/<int:rid>", methods=["PATCH"])
    def api_recipients_update(rid):
        recipient = db.session.get(AlertRecipient, rid)
        if not recipient:
            return jsonify({"ok": False, "error": "Recipient not found"}), 404

        payload = request.get_json(force=True, silent=True) or {}
        if "active" in payload:
            recipient.active = bool(payload["active"])
        if "name" in payload and payload["name"].strip():
            recipient.name = payload["name"].strip()
        db.session.commit()
        return jsonify({"ok": True, "data": recipient.to_dict()})

    @app.route("/api/test-notification", methods=["POST"])
    def api_test_notification():
        sms_msg = "\U0001f6a8 MARKET ALERT TEST: Your SMS notifications are working correctly."
        subject, html = build_test_email()

        # Collect active DB recipients; fall back to config ALERT_EMAIL if none
        db_recipients = [
            r.email
            for r in AlertRecipient.query.filter_by(active=True).order_by(AlertRecipient.id).all()
        ]

        sms_ok   = send_sms(sms_msg, app.config)
        email_ok = send_email(subject, html, app.config, recipients=db_recipients or None)

        return jsonify(
            {
                "ok": True,
                "sms_sent": sms_ok,
                "email_sent": email_ok,
                "recipients_count": len(db_recipients),
            }
        )

    return app


# Make config subscriptable for notifications (pass app.config which is a dict-like)
# The checker uses current_app.config which is already dict-like — no change needed.

app = create_app()

if __name__ == "__main__":
    import atexit
    atexit.register(lambda: app.scheduler.shutdown(wait=False))
    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
