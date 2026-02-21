import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def _classify_level(value: float) -> str:
    if value < 15:
        return "Low"
    if value < 20:
        return "Normal"
    if value < 30:
        return "Elevated"
    if value < 40:
        return "High"
    return "Extreme"


def get_vix_data(threshold: float = 30) -> dict:
    """Fetch VIX from Yahoo Finance and classify the stress level."""
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="10d")

        if hist.empty or len(hist) < 2:
            return {"error": "No VIX data returned", "triggered": False}

        current = float(hist["Close"].iloc[-1])
        previous = float(hist["Close"].iloc[-2])
        change_pct = ((current - previous) / previous) * 100

        return {
            "value": round(current, 2),
            "previous_close": round(previous, 2),
            "change_pct": round(change_pct, 2),
            "level": _classify_level(current),
            "threshold": threshold,
            "triggered": current > threshold,
            "error": None,
        }
    except Exception as exc:
        logger.exception("Failed to fetch VIX data")
        return {"error": str(exc), "triggered": False}
