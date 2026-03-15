# ============================================================
# token_resolver.py — Auto-fetch correct tokens from Angel One ScripMaster
# ============================================================
# Downloads the official ScripMaster JSON from Angel One and
# matches each index name to its correct token.
# Falls back to hardcoded tokens if fetch fails.
# ============================================================

import requests
import json
import os
import time

SCRIPMASTER_URL  = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
CACHE_FILE       = os.path.join(os.path.dirname(__file__), "cache", "scripmaster_tokens.json")

# ── Name aliases: our display name → possible names in ScripMaster ──
NAME_ALIASES = {
    "NIFTY 50":                      ["Nifty 50", "NIFTY 50", "Nifty50"],
    "NIFTY Next 50":                 ["Nifty Next 50", "NIFTY NEXT 50", "Nifty Next50"],
    "NIFTY 100":                     ["Nifty 100", "NIFTY 100"],
    "NIFTY 200":                     ["Nifty 200", "NIFTY 200"],
    "NIFTY 500":                     ["Nifty 500", "NIFTY 500"],
    "NIFTY Midcap 50":               ["Nifty Midcap 50", "NIFTY MIDCAP 50", "Nifty MidCap 50"],
    "NIFTY Midcap 100":              ["Nifty Midcap 100", "NIFTY MIDCAP 100"],
    "NIFTY Midcap 150":              ["Nifty Midcap 150", "NIFTY MIDCAP 150"],
    "NIFTY Smallcap 50":             ["Nifty Smallcap 50", "NIFTY SMALLCAP 50"],
    "NIFTY Smallcap 100":            ["Nifty Smallcap 100", "NIFTY SMALLCAP 100"],
    "NIFTY Smallcap 250":            ["Nifty Smallcap 250", "NIFTY SMALLCAP 250"],
    "NIFTY MidSmallcap 400":         ["Nifty MidSmallcap 400", "NIFTY MIDSMALLCAP 400", "Nifty Mid Small cap 400"],
    "NIFTY LargeMidcap 250":         ["Nifty LargeMidcap 250", "NIFTY LARGEMIDCAP 250", "Nifty Large Midcap 250"],
    "NIFTY Total Market":            ["Nifty Total Market", "NIFTY TOTAL MARKET"],
    "NIFTY Bank":                    ["Nifty Bank", "NIFTY BANK", "Bank Nifty"],
    "NIFTY Auto":                    ["Nifty Auto", "NIFTY AUTO"],
    "NIFTY Financial Services":      ["Nifty Financial Services", "NIFTY FIN SERVICE", "Nifty Fin Service"],
    "NIFTY FMCG":                    ["Nifty FMCG", "NIFTY FMCG"],
    "NIFTY IT":                      ["Nifty IT", "NIFTY IT"],
    "NIFTY Media":                   ["Nifty Media", "NIFTY MEDIA"],
    "NIFTY Metal":                   ["Nifty Metal", "NIFTY METAL"],
    "NIFTY Pharma":                  ["Nifty Pharma", "NIFTY PHARMA"],
    "NIFTY PSU Bank":                ["Nifty PSU Bank", "NIFTY PSU BANK"],
    "NIFTY Realty":                  ["Nifty Realty", "NIFTY REALTY"],
    "NIFTY Private Bank":            ["Nifty Private Bank", "NIFTY PRIVATE BANK", "Nifty Pvt Bank"],
    "NIFTY Energy":                  ["Nifty Energy", "NIFTY ENERGY"],
    "NIFTY Infrastructure":          ["Nifty Infrastructure", "NIFTY INFRA", "Nifty Infra"],
    "NIFTY Healthcare":              ["Nifty Healthcare", "NIFTY HEALTHCARE"],
    "NIFTY Consumer Durables":       ["Nifty Consumer Durables", "NIFTY CONSR DURBL", "Nifty Cons Dur"],
    "NIFTY Oil & Gas":               ["Nifty Oil & Gas", "NIFTY OIL AND GAS", "Nifty Oil and Gas"],
    "NIFTY PSE":                     ["Nifty PSE", "NIFTY PSE"],
    "NIFTY Fin Services 25/50":      ["Nifty Fin Services 25 50", "NIFTY FIN SER 25 50", "Nifty FinSrv 25/50"],
    "NIFTY Commodities":             ["Nifty Commodities", "NIFTY COMMODITIES"],
    "NIFTY India Consumption":       ["Nifty India Consumption", "NIFTY CONSUMPTION", "Nifty Consumption"],
    "NIFTY CPSE":                    ["Nifty CPSE", "NIFTY CPSE"],
    "NIFTY India Digital":           ["Nifty India Digital", "NIFTY INDIA DIGITAL"],
    "NIFTY India Defence":           ["Nifty India Defence", "NIFTY INDIA DEFENCE", "Nifty India Defense"],
    "NIFTY India Manufacturing":     ["Nifty India Manufacturing", "NIFTY INDIA MFG"],
    "NIFTY MNC":                     ["Nifty MNC", "NIFTY MNC"],
    "NIFTY Services Sector":         ["Nifty Services Sector", "NIFTY SERV SECTOR"],
    "NIFTY Housing":                 ["Nifty Housing", "NIFTY HOUSING"],
    "NIFTY Transportation & Logistics": ["Nifty Transportation & Logistics", "NIFTY TRAN LOGISTIC"],
    "NIFTY India Tourism":           ["Nifty India Tourism", "NIFTY INDIA TOURISM"],
    "NIFTY EV & New Age Auto":       ["Nifty EV & New Age Auto", "NIFTY EV"],
    "NIFTY Non-Cyclical Consumer":   ["Nifty Non-Cyclical Consumer", "NIFTY NON CYC CONS"],
    "NIFTY Mobility":                ["Nifty Mobility", "NIFTY MOBILITY"],
    "NIFTY REITs & InvITs":          ["Nifty REITs & InvITs", "NIFTY REITS INVITS"],
}


def _load_cached_tokens() -> dict:
    """Load previously resolved tokens from cache file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_token_cache(token_map: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(token_map, f, indent=2)


def fetch_and_resolve_tokens(progress_cb=None) -> dict:
    """
    Downloads ScripMaster JSON, matches each index by name,
    returns dict: {our_index_name: resolved_token}
    Also caches result to disk.
    """
    if progress_cb: progress_cb("Downloading Angel One ScripMaster (once per session)...")

    try:
        resp = requests.get(SCRIPMASTER_URL, timeout=60,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        instruments = resp.json()
    except Exception as e:
        if progress_cb: progress_cb(f"ScripMaster fetch failed: {e} — using cached tokens")
        return _load_cached_tokens()

    if progress_cb: progress_cb(f"ScripMaster loaded ({len(instruments):,} instruments). Matching indices...")

    # Build lookup: lowercase name → token
    name_to_token = {}
    for inst in instruments:
        if inst.get("exch_seg") == "NSE":
            name  = inst.get("name", "").strip()
            token = inst.get("token", "")
            if name and token:
                name_to_token[name.lower()] = token

    token_map   = {}
    unresolved  = []

    for our_name, aliases in NAME_ALIASES.items():
        resolved = None
        for alias in aliases:
            if alias.lower() in name_to_token:
                resolved = name_to_token[alias.lower()]
                break

        if resolved:
            token_map[our_name] = resolved
        else:
            unresolved.append(our_name)

    if progress_cb:
        progress_cb(f"Resolved {len(token_map)}/{len(NAME_ALIASES)} tokens. "
                    f"Unresolved: {unresolved if unresolved else 'None ✅'}")

    _save_token_cache(token_map)
    return token_map


def get_token(our_name: str, resolved_map: dict, fallback_map: dict) -> str:
    """Get token — prefer resolved, fall back to hardcoded."""
    return resolved_map.get(our_name) or fallback_map.get(our_name, "")
