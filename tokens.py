# ============================================================
# tokens.py — VERIFIED NSE Index Tokens from ScripMaster
# Last verified: March 2026 from OpenAPIScripMaster.json
# ============================================================
# Indices NOT available in Angel One ScripMaster (removed):
#   NIFTY LargeMidcap 250, NIFTY Total Market,
#   NIFTY Healthcare, NIFTY Consumer Durables, NIFTY Oil & Gas,
#   NIFTY Fin Services 25/50, NIFTY India Digital, NIFTY India Defence,
#   NIFTY India Manufacturing, NIFTY Housing, NIFTY Transportation,
#   NIFTY India Tourism, NIFTY EV & New Age Auto,
#   NIFTY Non-Cyclical Consumer, NIFTY Mobility, NIFTY REITs & InvITs
# ============================================================

INDICES = {
    "Broad Market": [
        {"name": "NIFTY 50",              "token": "99926000", "symbol": "NIFTY"},
        {"name": "NIFTY Next 50",         "token": "99926013", "symbol": "NIFTYNXT50"},
        {"name": "NIFTY 100",             "token": "99926012", "symbol": "NIFTY 100"},
        {"name": "NIFTY 200",             "token": "99926033", "symbol": "NIFTY 200"},
        {"name": "NIFTY 500",             "token": "99926004", "symbol": "NIFTY 500"},
        {"name": "NIFTY Midcap 50",       "token": "99926014", "symbol": "NIFTY MIDCAP 50"},
        {"name": "NIFTY Midcap 100",      "token": "99926011", "symbol": "NIFTY MIDCAP 100"},
        {"name": "NIFTY Midcap 150",      "token": "99926060", "symbol": "NIFTY MIDCAP 150"},
        {"name": "NIFTY Smallcap 50",     "token": "99926061", "symbol": "NIFTY SMLCAP 50"},
        {"name": "NIFTY Smallcap 100",    "token": "99926032", "symbol": "NIFTY SMLCAP 100"},
        {"name": "NIFTY Smallcap 250",    "token": "99926062", "symbol": "NIFTY SMLCAP 250"},
        {"name": "NIFTY MidSmallcap 400", "token": "99926063", "symbol": "NIFTY MIDSML 400"},
    ],
    "Sectoral": [
        {"name": "NIFTY Bank",             "token": "99926009", "symbol": "BANKNIFTY"},
        {"name": "NIFTY Auto",             "token": "99926029", "symbol": "NIFTY AUTO"},
        {"name": "NIFTY Fin Services",     "token": "99926037", "symbol": "FINNIFTY"},
        {"name": "NIFTY FMCG",            "token": "99926021", "symbol": "NIFTY FMCG"},
        {"name": "NIFTY IT",              "token": "99926008", "symbol": "NIFTY IT"},
        {"name": "NIFTY Media",           "token": "99926031", "symbol": "NIFTY MEDIA"},
        {"name": "NIFTY Metal",           "token": "99926030", "symbol": "NIFTY METAL"},
        {"name": "NIFTY Pharma",          "token": "99926023", "symbol": "NIFTY PHARMA"},
        {"name": "NIFTY PSU Bank",        "token": "99926025", "symbol": "NIFTY PSU BANK"},
        {"name": "NIFTY Realty",          "token": "99926018", "symbol": "NIFTY REALTY"},
        {"name": "NIFTY Private Bank",    "token": "99926047", "symbol": "NIFTY PVT BANK"},
        {"name": "NIFTY Energy",          "token": "99926020", "symbol": "NIFTY ENERGY"},
        {"name": "NIFTY Infrastructure",  "token": "99926019", "symbol": "NIFTY INFRA"},
        {"name": "NIFTY PSE",             "token": "99926024", "symbol": "NIFTY PSE"},
        {"name": "NIFTY Services Sector", "token": "99926026", "symbol": "NIFTY SERV SECTOR"},
    ],
    "Thematic": [
        {"name": "NIFTY Commodities",       "token": "99926035", "symbol": "NIFTY COMMODITIES"},
        {"name": "NIFTY India Consumption", "token": "99926036", "symbol": "NIFTY CONSUMPTION"},
        {"name": "NIFTY CPSE",             "token": "99926041", "symbol": "NIFTY CPSE"},
        {"name": "NIFTY MNC",              "token": "99926022", "symbol": "NIFTY MNC"},
        {"name": "NIFTY Services Sector",  "token": "99926026", "symbol": "NIFTY SERV SECTOR"},
    ],
}

def get_all_indices():
    all_indices = []
    for category, indices in INDICES.items():
        for idx in indices:
            all_indices.append({**idx, "category": category})
    return all_indices
