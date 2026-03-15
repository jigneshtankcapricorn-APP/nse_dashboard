# ============================================================
# api.py — Angel One SmartAPI Login + Historical Data Fetch
# Uses direct HTTP requests (no SmartAPI SDK) for Python 3.14 compatibility
# ============================================================

import pyotp
import requests
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://apiconnect.angelbroking.com"

LOGIN_URL  = f"{BASE_URL}/rest/auth/angelbroking/user/v1/loginByPassword"
CANDLE_URL = f"{BASE_URL}/rest/secure/angelbroking/historical/v1/getCandleData"


def login_angel(api_key: str, client_id: str, password: str, totp_secret: str) -> dict:
    """
    Login to Angel One via direct REST API.
    Returns session dict with jwt_token, refresh_token, feed_token.
    Raises Exception on failure.
    """
    totp = pyotp.TOTP(totp_secret).now()

    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "X-UserType":    "USER",
        "X-SourceID":    "WEB",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "127.0.0.1",
        "X-MACAddress":  "00:00:00:00:00:00",
        "X-PrivateKey":  api_key,
    }

    payload = {
        "clientcode": client_id,
        "password":   password,
        "totp":       totp,
    }

    resp = requests.post(LOGIN_URL, json=payload, headers=headers, timeout=15)

    if resp.status_code != 200:
        raise Exception(f"Login HTTP error {resp.status_code}: {resp.text}")

    data = resp.json()
    if not data.get("status"):
        raise Exception(f"Angel One Login Failed: {data.get('message', 'Unknown error')}")

    session = data.get("data", {})
    session["api_key"] = api_key   # carry api_key for subsequent calls
    return session


def fetch_weekly_data(session: dict, token: str, weeks: int = 52) -> pd.DataFrame:
    """
    Fetch daily OHLC for the last `weeks` weeks for a given index token.
    Resampled to weekly (Friday close) with weekly % change.
    """
    end_date   = datetime.now()
    start_date = end_date - timedelta(weeks=weeks + 2)  # +2 buffer for weekends/holidays

    from_str = start_date.strftime("%Y-%m-%d 09:00")
    to_str   = end_date.strftime("%Y-%m-%d 15:30")

    headers = {
        "Content-Type":    "application/json",
        "Accept":          "application/json",
        "X-UserType":      "USER",
        "X-SourceID":      "WEB",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP":"127.0.0.1",
        "X-MACAddress":    "00:00:00:00:00:00",
        "X-PrivateKey":    session["api_key"],
        "Authorization":   f"Bearer {session['jwtToken']}",
    }

    payload = {
        "exchange":    "NSE",
        "symboltoken": token,
        "interval":    "ONE_DAY",
        "fromdate":    from_str,
        "todate":      to_str,
    }

    resp = requests.post(CANDLE_URL, json=payload, headers=headers, timeout=20)

    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code} for token {token}: {resp.text}")

    data = resp.json()
    if not data.get("status"):
        raise Exception(f"No data for token {token}: {data.get('message', '')}")

    raw = data.get("data", [])
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)

    # Resample to weekly (Friday close)
    weekly     = df["close"].resample("W-FRI").last().dropna()
    weekly_pct = weekly.pct_change() * 100
    weekly_pct = weekly_pct.dropna().tail(weeks)

    result = pd.DataFrame({
        "week_end":   weekly_pct.index,
        "close":      weekly.reindex(weekly_pct.index).values,
        "weekly_pct": weekly_pct.values,
    })
    result.reset_index(drop=True, inplace=True)
    result["week_num"] = range(1, len(result) + 1)

    return result
