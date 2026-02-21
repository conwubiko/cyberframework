import logging
import requests

logger = logging.getLogger(__name__)

CNN_API_URL = (
    "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
}


def get_fear_greed(threshold: float = 12) -> dict:
    """Fetch the CNN Fear & Greed Index from the unofficial API endpoint."""
    try:
        response = requests.get(CNN_API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        fg = data.get("fear_and_greed", {})
        score = float(fg.get("score", -1))
        rating = fg.get("rating", "unknown")
        timestamp = fg.get("timestamp", "")

        if score < 0:
            return {"error": "Invalid score from CNN API", "triggered": False}

        return {
            "score": round(score, 1),
            "rating": rating,
            "timestamp": timestamp,
            "threshold": threshold,
            "triggered": score < threshold,
            "error": None,
        }
    except Exception as exc:
        logger.exception("Failed to fetch Fear & Greed data")
        return {"error": str(exc), "triggered": False}
