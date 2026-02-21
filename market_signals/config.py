import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///market_signals.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Thresholds
    VIX_THRESHOLD = float(os.environ.get("VIX_THRESHOLD", 30))
    FEAR_GREED_THRESHOLD = float(os.environ.get("FEAR_GREED_THRESHOLD", 12))
    RSI_THRESHOLD = float(os.environ.get("RSI_THRESHOLD", 30))
    CAPITULATION_SCORE_THRESHOLD = float(
        os.environ.get("CAPITULATION_SCORE_THRESHOLD", 50)
    )

    # Twilio SMS
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
    ALERT_PHONE_NUMBER = os.environ.get("ALERT_PHONE_NUMBER", "")

    # Gmail SMTP
    GMAIL_USER = os.environ.get("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
    ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")

    # Scheduler
    ALERT_COOLDOWN_HOURS = int(os.environ.get("ALERT_COOLDOWN_HOURS", 4))
    CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL_MINUTES", 15))
