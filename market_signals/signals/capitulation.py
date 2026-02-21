import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Scoring weights
RSI_POINTS = 30
DAY_DROP_POINTS = 20
WEEK_DROP_POINTS = 25
VIX_SPIKE_POINTS = 25

RSI_PERIOD = 14
RSI_OVERSOLD = 30
DAY_DROP_THRESHOLD = 3.0   # percent
WEEK_DROP_THRESHOLD = 7.0  # percent
VIX_SPIKE_THRESHOLD = 20.0 # percent


def _compute_rsi(closes: pd.Series, period: int = RSI_PERIOD) -> float:
    """Compute RSI using Wilder's smoothing method."""
    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)

    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("inf"))
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def get_capitulation_signals(
    capitulation_threshold: float = 50,
    rsi_threshold: float = RSI_OVERSOLD,
) -> dict:
    """
    Calculate a composite capitulation score from SPY and VIX data.

    Score breakdown (max 100):
      - SPY RSI < 30       → +30 pts
      - SPY 1-day drop > 3%→ +20 pts
      - SPY 5-day drop > 7%→ +25 pts
      - VIX 1-day spike > 20% → +25 pts
    """
    try:
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="3mo")

        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="10d")

        if spy_hist.empty or len(spy_hist) < RSI_PERIOD + 1:
            return {"error": "Insufficient SPY data", "triggered": False}

        if vix_hist.empty or len(vix_hist) < 2:
            return {"error": "Insufficient VIX data for spike calc", "triggered": False}

        # RSI
        rsi = _compute_rsi(spy_hist["Close"])

        # Price drops
        spy_current = float(spy_hist["Close"].iloc[-1])
        spy_yesterday = float(spy_hist["Close"].iloc[-2])
        spy_5d_ago = float(spy_hist["Close"].iloc[-6]) if len(spy_hist) >= 6 else spy_current

        day_change = ((spy_current - spy_yesterday) / spy_yesterday) * 100
        week_change = ((spy_current - spy_5d_ago) / spy_5d_ago) * 100

        # VIX spike
        vix_current = float(vix_hist["Close"].iloc[-1])
        vix_previous = float(vix_hist["Close"].iloc[-2])
        vix_spike_pct = ((vix_current - vix_previous) / vix_previous) * 100

        # Build signal list and compute score
        active_signals = []
        score = 0

        if rsi < rsi_threshold:
            score += RSI_POINTS
            active_signals.append(f"SPY RSI oversold ({rsi:.1f} < {rsi_threshold})")

        if day_change < -DAY_DROP_THRESHOLD:
            score += DAY_DROP_POINTS
            active_signals.append(
                f"SPY 1-day drop ({day_change:.1f}% < -{DAY_DROP_THRESHOLD}%)"
            )

        if week_change < -WEEK_DROP_THRESHOLD:
            score += WEEK_DROP_POINTS
            active_signals.append(
                f"SPY 5-day drop ({week_change:.1f}% < -{WEEK_DROP_THRESHOLD}%)"
            )

        if vix_spike_pct > VIX_SPIKE_THRESHOLD:
            score += VIX_SPIKE_POINTS
            active_signals.append(
                f"VIX spike ({vix_spike_pct:.1f}% > {VIX_SPIKE_THRESHOLD}%)"
            )

        return {
            "score": score,
            "signals": active_signals,
            "capitulation": score >= capitulation_threshold,
            "triggered": score >= capitulation_threshold,
            "rsi": round(rsi, 2),
            "rsi_threshold": rsi_threshold,
            "rsi_triggered": rsi < rsi_threshold,
            "day_change": round(day_change, 2),
            "week_change": round(week_change, 2),
            "vix_spike_pct": round(vix_spike_pct, 2),
            "spy_price": round(spy_current, 2),
            "capitulation_threshold": capitulation_threshold,
            "error": None,
        }
    except Exception as exc:
        logger.exception("Failed to compute capitulation signals")
        return {"error": str(exc), "triggered": False}
