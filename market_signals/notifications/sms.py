import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)


def _get(config, key: str, default: str = "") -> str:
    """Retrieve a value from either a dict-like or attribute-based config."""
    try:
        return config[key]
    except (TypeError, KeyError):
        return getattr(config, key, default)


def send_sms(message: str, config) -> bool:
    """Send an SMS alert via Twilio. Returns True on success."""
    account_sid = _get(config, "TWILIO_ACCOUNT_SID")
    auth_token   = _get(config, "TWILIO_AUTH_TOKEN")
    from_number  = _get(config, "TWILIO_FROM_NUMBER")
    to_number    = _get(config, "ALERT_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number, to_number]):
        logger.warning("Twilio credentials incomplete — SMS not sent")
        return False

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        logger.info("SMS sent: SID=%s", msg.sid)
        return True
    except Exception as exc:
        logger.exception("Failed to send SMS")
        return False


def build_sms_message(alert_type: str, value: float, threshold: float) -> str:
    labels = {
        "vix": f"VIX={value:.1f} (>{threshold:.0f})",
        "fear_greed": f"Fear&Greed={value:.1f} (<{threshold:.0f})",
        "rsi": f"SPY RSI={value:.1f} (<{threshold:.0f})",
        "capitulation": f"Capitulation Score={value:.0f} (>={threshold:.0f})",
    }
    detail = labels.get(alert_type, f"{alert_type}={value}")
    return f"\U0001f6a8 MARKET ALERT: {detail}. Check your dashboard for details."
