import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _get(config, key: str, default: str = "") -> str:
    """Retrieve a value from either a dict-like or attribute-based config."""
    try:
        return config[key]
    except (TypeError, KeyError):
        return getattr(config, key, default)


def send_email(subject: str, html_body: str, config) -> bool:
    """Send an HTML alert email via Gmail SMTP SSL. Returns True on success."""
    gmail_user     = _get(config, "GMAIL_USER")
    gmail_password = _get(config, "GMAIL_APP_PASSWORD")
    recipient      = _get(config, "ALERT_EMAIL")

    if not all([gmail_user, gmail_password, recipient]):
        logger.warning("Gmail credentials incomplete — email not sent")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())

        logger.info("Email sent to %s: %s", recipient, subject)
        return True
    except Exception as exc:
        logger.exception("Failed to send email")
        return False


def build_alert_email(alert_type: str, status: dict) -> tuple[str, str]:
    """Build (subject, html_body) for the alert email."""
    titles = {
        "vix": "VIX Spike Detected",
        "fear_greed": "Extreme Fear — Fear & Greed Alert",
        "rsi": "SPY RSI Oversold",
        "capitulation": "Market Capitulation Signal",
    }
    title = titles.get(alert_type, "Market Alert")
    subject = f"[Market Alert] {title} — Capitulation Risk"

    vix = status.get("vix", {})
    fg = status.get("fear_greed", {})
    cap = status.get("capitulation", {})

    def row(label, value, triggered=False):
        color = "#e74c3c" if triggered else "#ecf0f1"
        return (
            f"<tr>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #34495e;color:#bdc3c7'>{label}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #34495e;color:{color};font-weight:bold'>{value}</td>"
            f"</tr>"
        )

    vix_val = vix.get("value", "N/A")
    fg_score = fg.get("score", "N/A")
    rsi_val = cap.get("rsi", "N/A")
    cap_score = cap.get("score", "N/A")
    signals_html = "".join(
        f"<li style='color:#e74c3c'>{s}</li>" for s in cap.get("signals", [])
    ) or "<li style='color:#2ecc71'>None active</li>"

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="background:#1a1a2e;font-family:Arial,sans-serif;padding:20px">
  <div style="max-width:600px;margin:0 auto;background:#16213e;border-radius:8px;overflow:hidden">
    <div style="background:#e74c3c;padding:20px 24px">
      <h1 style="color:#fff;margin:0;font-size:22px">&#128680; {title}</h1>
    </div>
    <div style="padding:24px">
      <table style="width:100%;border-collapse:collapse">
        {row("VIX", f"{vix_val} (threshold: {vix.get('threshold','30')})", vix.get('triggered', False))}
        {row("VIX Level", vix.get('level','—'))}
        {row("Fear &amp; Greed", f"{fg_score} — {fg.get('rating','—')} (threshold: {fg.get('threshold','12')})", fg.get('triggered', False))}
        {row("SPY RSI", f"{rsi_val} (threshold: {cap.get('rsi_threshold','30')})", cap.get('rsi_triggered', False))}
        {row("SPY 1-day change", f"{cap.get('day_change','N/A')}%")}
        {row("SPY 5-day change", f"{cap.get('week_change','N/A')}%")}
        {row("Capitulation Score", f"{cap_score}/100", cap.get('capitulation', False))}
      </table>
      <h3 style="color:#ecf0f1;margin-top:20px">Active Signals</h3>
      <ul style="padding-left:20px">{signals_html}</ul>
      <p style="color:#7f8c8d;font-size:12px;margin-top:24px">
        This is an automated alert from your Market Signals monitor.
      </p>
    </div>
  </div>
</body>
</html>
"""
    return subject, html


def build_test_email() -> tuple[str, str]:
    subject = "[Market Alert] Test Notification"
    html = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="background:#1a1a2e;font-family:Arial,sans-serif;padding:20px">
  <div style="max-width:600px;margin:0 auto;background:#16213e;border-radius:8px;padding:24px">
    <h2 style="color:#2ecc71">&#10003; Test Notification Successful</h2>
    <p style="color:#ecf0f1">Your Market Signals email alerts are configured correctly.</p>
  </div>
</body>
</html>
"""
    return subject, html
