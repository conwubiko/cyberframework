"""
Main signal checker — fetches all signals in parallel, evaluates triggers,
enforces cooldowns, fires notifications, and persists alert history.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from flask import current_app

from models import db, AlertHistory, AlertCooldown
from signals.vix import get_vix_data
from signals.fear_greed import get_fear_greed
from signals.capitulation import get_capitulation_signals
from notifications.sms import send_sms, build_sms_message
from notifications.email_alert import send_email, build_alert_email

logger = logging.getLogger(__name__)


def _is_on_cooldown(alert_type: str, cooldown_hours: int) -> bool:
    record = db.session.get(AlertCooldown, alert_type)
    if record is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
    last = record.last_sent
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last > cutoff


def _update_cooldown(alert_type: str) -> None:
    record = db.session.get(AlertCooldown, alert_type)
    now = datetime.now(timezone.utc)
    if record is None:
        db.session.add(AlertCooldown(alert_type=alert_type, last_sent=now))
    else:
        record.last_sent = now
    db.session.commit()


def _log_alert(alert_type: str, value: float, message: str, notified: bool) -> None:
    entry = AlertHistory(
        alert_type=alert_type,
        value=value,
        message=message,
        notified=notified,
    )
    db.session.add(entry)
    db.session.commit()


def _send_notifications(alert_type: str, value: float, threshold: float, status: dict, config) -> bool:
    sms_msg = build_sms_message(alert_type, value, threshold)
    subject, html = build_alert_email(alert_type, status)

    sms_ok = send_sms(sms_msg, config)
    email_ok = send_email(subject, html, config)
    return sms_ok or email_ok


def run_check() -> dict:
    """Fetch all signals, evaluate triggers, fire alerts if needed."""
    config = current_app.config

    # ── Fetch in parallel ────────────────────────────────────────────────
    tasks = {
        "vix": lambda: get_vix_data(threshold=config["VIX_THRESHOLD"]),
        "fear_greed": lambda: get_fear_greed(threshold=config["FEAR_GREED_THRESHOLD"]),
        "capitulation": lambda: get_capitulation_signals(
            capitulation_threshold=config["CAPITULATION_SCORE_THRESHOLD"],
            rsi_threshold=config["RSI_THRESHOLD"],
        ),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                logger.exception("Signal fetch failed: %s", name)
                results[name] = {"error": str(exc), "triggered": False}

    vix_data = results["vix"]
    fg_data = results["fear_greed"]
    cap_data = results["capitulation"]

    status = {
        "vix": vix_data,
        "fear_greed": fg_data,
        "capitulation": cap_data,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "alerts_fired": [],
    }

    cooldown_hours = config["ALERT_COOLDOWN_HOURS"]

    # ── Evaluate each trigger ────────────────────────────────────────────
    alert_specs = [
        {
            "type": "vix",
            "data": vix_data,
            "value": vix_data.get("value", 0),
            "threshold": config["VIX_THRESHOLD"],
            "message": (
                f"VIX={vix_data.get('value','?')} exceeded threshold "
                f"{config['VIX_THRESHOLD']} (level: {vix_data.get('level','?')})"
            ),
        },
        {
            "type": "fear_greed",
            "data": fg_data,
            "value": fg_data.get("score", 100),
            "threshold": config["FEAR_GREED_THRESHOLD"],
            "message": (
                f"Fear & Greed={fg_data.get('score','?')} below threshold "
                f"{config['FEAR_GREED_THRESHOLD']} ({fg_data.get('rating','?')})"
            ),
        },
        {
            "type": "rsi",
            "data": cap_data,
            "value": cap_data.get("rsi", 100),
            "threshold": config["RSI_THRESHOLD"],
            "message": (
                f"SPY RSI={cap_data.get('rsi','?')} below threshold "
                f"{config['RSI_THRESHOLD']} (oversold)"
            ),
        },
        {
            "type": "capitulation",
            "data": cap_data,
            "value": cap_data.get("score", 0),
            "threshold": config["CAPITULATION_SCORE_THRESHOLD"],
            "message": (
                f"Capitulation score={cap_data.get('score','?')} >= "
                f"{config['CAPITULATION_SCORE_THRESHOLD']}. "
                f"Signals: {', '.join(cap_data.get('signals', []))}"
            ),
        },
    ]

    for spec in alert_specs:
        if not spec["data"].get("triggered", False):
            continue
        if spec["data"].get("error"):
            continue

        alert_type = spec["type"]

        if _is_on_cooldown(alert_type, cooldown_hours):
            logger.info("Alert %s is on cooldown — skipping", alert_type)
            status["alerts_fired"].append(
                {"type": alert_type, "status": "cooldown"}
            )
            continue

        notified = _send_notifications(
            alert_type, spec["value"], spec["threshold"], status, config
        )
        _update_cooldown(alert_type)
        _log_alert(alert_type, spec["value"], spec["message"], notified)

        status["alerts_fired"].append(
            {"type": alert_type, "status": "sent" if notified else "logged"}
        )
        logger.info("Alert fired: %s (notified=%s)", alert_type, notified)

    return status
