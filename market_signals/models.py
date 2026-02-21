from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AlertHistory(db.Model):
    __tablename__ = "alert_history"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    alert_type = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Float, nullable=True)
    message = db.Column(db.String(512), nullable=False)
    notified = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "alert_type": self.alert_type,
            "value": self.value,
            "message": self.message,
            "notified": self.notified,
        }


class AlertCooldown(db.Model):
    __tablename__ = "alert_cooldown"

    alert_type = db.Column(db.String(64), primary_key=True)
    last_sent = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "alert_type": self.alert_type,
            "last_sent": self.last_sent.isoformat(),
        }
