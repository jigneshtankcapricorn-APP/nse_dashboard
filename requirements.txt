# ============================================================
# cache.py — Daily JSON Cache for Index Data
# ============================================================

import os
import json
import pandas as pd
from datetime import datetime

CACHE_DIR  = os.path.join(os.path.dirname(__file__), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "index_data.json")
META_FILE  = os.path.join(CACHE_DIR, "meta.json")


def _ensure_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def save_cache(all_data: dict):
    """
    all_data: {index_name: DataFrame with week_end, close, weekly_pct, week_num}
    """
    _ensure_dir()
    serializable = {}
    for name, df in all_data.items():
        if df is not None and not df.empty:
            df_copy = df.copy()
            df_copy["week_end"] = df_copy["week_end"].astype(str)
            serializable[name] = df_copy.to_dict(orient="records")

    with open(CACHE_FILE, "w") as f:
        json.dump(serializable, f)

    with open(META_FILE, "w") as f:
        json.dump({"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f)


def load_cache() -> dict:
    """Returns dict of {index_name: DataFrame} or empty dict if no cache."""
    if not os.path.exists(CACHE_FILE):
        return {}

    with open(CACHE_FILE, "r") as f:
        raw = json.load(f)

    result = {}
    for name, records in raw.items():
        df = pd.DataFrame(records)
        df["week_end"] = pd.to_datetime(df["week_end"])
        result[name] = df

    return result


def get_last_updated() -> str:
    if not os.path.exists(META_FILE):
        return "Never"
    with open(META_FILE, "r") as f:
        meta = json.load(f)
    return meta.get("last_updated", "Unknown")


def cache_exists() -> bool:
    return os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 10
