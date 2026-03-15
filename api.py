# ============================================================
# api.py — Angel One SmartAPI Login + Historical Data Fetch
# ============================================================

import pyotp
import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect


def login_angel(api_key: str, client_id: str, password: str, totp_secret: str):
    """
    Login to Angel One SmartAPI.
    Returns (obj, auth_token) on success, raises Exception on failure.
    """
    obj = SmartConnect(api_key=api_key)
    totp = pyotp.TOTP(totp_secret).now()
    data = obj.generateSession(client_id, password, totp)

    if not data or data.get("status") is False:
        msg = data.get("message", "Login failed") if data else "No response from API"
        raise Exception(f"Angel One Login Failed: {msg}")

    return obj


def fetch_weekly_data(obj: SmartConnect, token: str, weeks: int = 52) -> pd.DataFrame:
    """
    Fetch daily OHLC for the last `weeks` weeks for a given index token.
    Returns a DataFrame with columns: [date, open, high, low, close, volume]
    Resampled to weekly (Friday close).
    """
    end_date   = datetime.now()
    start_date = end_date - timedelta(weeks=weeks + 2)  # +2 buffer for weekends

    from_str = start_date.strftime("%Y-%m-%d 09:00")
    to_str   = end_date.strftime("%Y-%m-%d 15:30")

    params = {
        "exchange":    "NSE",
        "symboltoken": token,
        "interval":    "ONE_DAY",
        "fromdate":    from_str,
        "todate":      to_str,
    }

    try:
        resp = obj.getCandleData(params)
    except Exception as e:
        raise Exception(f"API call failed for token {token}: {e}")

    if not resp or resp.get("status") is False:
        raise Exception(f"No data returned for token {token}: {resp.get('message', '')}")

    raw = resp.get("data", [])
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)

    # Resample to weekly using Friday as week-end
    weekly = df["close"].resample("W-FRI").last().dropna()

    # Calculate weekly % change
    weekly_pct = weekly.pct_change() * 100
    weekly_pct = weekly_pct.dropna()

    # Keep only last `weeks` weeks
    weekly_pct = weekly_pct.tail(weeks)

    result = pd.DataFrame({
        "week_end":    weekly_pct.index,
        "close":       weekly.reindex(weekly_pct.index).values,
        "weekly_pct":  weekly_pct.values,
    })
    result.reset_index(drop=True, inplace=True)
    result["week_num"] = range(1, len(result) + 1)

    return result
