# ============================================================
# tokens.py — NSE Index Token Map for Angel One SmartAPI
# ============================================================

INDICES = {
    "Broad Market": [
        {"name": "NIFTY 50",              "token": "99926000", "symbol": "Nifty 50"},
        {"name": "NIFTY Next 50",         "token": "99926013", "symbol": "Nifty Next 50"},
        {"name": "NIFTY 100",             "token": "99926012", "symbol": "Nifty 100"},
        {"name": "NIFTY 200",             "token": "99926017", "symbol": "Nifty 200"},
        {"name": "NIFTY 500",             "token": "99926001", "symbol": "Nifty 500"},
        {"name": "NIFTY Midcap 50",       "token": "99926008", "symbol": "Nifty Midcap 50"},
        {"name": "NIFTY Midcap 100",      "token": "99926011", "symbol": "Nifty Midcap 100"},
        {"name": "NIFTY Midcap 150",      "token": "99926014", "symbol": "Nifty Midcap 150"},
        {"name": "NIFTY Smallcap 50",     "token": "99926022", "symbol": "Nifty Smallcap 50"},
        {"name": "NIFTY Smallcap 100",    "token": "99926010", "symbol": "Nifty Smallcap 100"},
        {"name": "NIFTY Smallcap 250",    "token": "99926016", "symbol": "Nifty Smallcap 250"},
        {"name": "NIFTY MidSmallcap 400", "token": "99926015", "symbol": "Nifty MidSmallcap 400"},
        {"name": "NIFTY LargeMidcap 250", "token": "99926018", "symbol": "Nifty LargeMidcap 250"},
        {"name": "NIFTY Total Market",    "token": "99926034", "symbol": "Nifty Total Market"},
    ],
    "Sectoral": [
        {"name": "NIFTY Bank",                   "token": "99926009", "symbol": "Nifty Bank"},
        {"name": "NIFTY Auto",                   "token": "99926002", "symbol": "Nifty Auto"},
        {"name": "NIFTY Financial Services",     "token": "99926021", "symbol": "Nifty Fin Service"},
        {"name": "NIFTY FMCG",                   "token": "99926003", "symbol": "Nifty FMCG"},
        {"name": "NIFTY IT",                     "token": "99926004", "symbol": "Nifty IT"},
        {"name": "NIFTY Media",                  "token": "99926005", "symbol": "Nifty Media"},
        {"name": "NIFTY Metal",                  "token": "99926006", "symbol": "Nifty Metal"},
        {"name": "NIFTY Pharma",                 "token": "99926007", "symbol": "Nifty Pharma"},
        {"name": "NIFTY PSU Bank",               "token": "99926023", "symbol": "Nifty PSU Bank"},
        {"name": "NIFTY Realty",                 "token": "99926024", "symbol": "Nifty Realty"},
        {"name": "NIFTY Private Bank",           "token": "99926032", "symbol": "Nifty Pvt Bank"},
        {"name": "NIFTY Energy",                 "token": "99926025", "symbol": "Nifty Energy"},
        {"name": "NIFTY Infrastructure",         "token": "99926026", "symbol": "Nifty Infra"},
        {"name": "NIFTY Healthcare",             "token": "99926027", "symbol": "Nifty Healthcare"},
        {"name": "NIFTY Consumer Durables",      "token": "99926033", "symbol": "Nifty Cons Dur"},
        {"name": "NIFTY Oil & Gas",              "token": "99926029", "symbol": "Nifty Oil & Gas"},
        {"name": "NIFTY PSE",                    "token": "99926028", "symbol": "Nifty PSE"},
        {"name": "NIFTY Fin Services 25/50",     "token": "99926031", "symbol": "Nifty FinSrv 25/50"},
    ],
    "Thematic": [
        {"name": "NIFTY Commodities",                "token": "99926037", "symbol": "Nifty Commodities"},
        {"name": "NIFTY India Consumption",          "token": "99926038", "symbol": "Nifty Consumption"},
        {"name": "NIFTY CPSE",                       "token": "99926039", "symbol": "Nifty CPSE"},
        {"name": "NIFTY India Digital",              "token": "99926046", "symbol": "Nifty Digital"},
        {"name": "NIFTY India Defence",              "token": "99926047", "symbol": "Nifty Defence"},
        {"name": "NIFTY India Manufacturing",        "token": "99926048", "symbol": "Nifty Mfg"},
        {"name": "NIFTY MNC",                        "token": "99926040", "symbol": "Nifty MNC"},
        {"name": "NIFTY Services Sector",            "token": "99926041", "symbol": "Nifty Services"},
        {"name": "NIFTY Housing",                    "token": "99926049", "symbol": "Nifty Housing"},
        {"name": "NIFTY Transportation & Logistics", "token": "99926050", "symbol": "Nifty Trans & Logis"},
        {"name": "NIFTY India Tourism",              "token": "99926051", "symbol": "Nifty Tourism"},
        {"name": "NIFTY EV & New Age Auto",          "token": "99926052", "symbol": "Nifty EV"},
        {"name": "NIFTY Non-Cyclical Consumer",      "token": "99926053", "symbol": "Nifty Non-Cycl"},
        {"name": "NIFTY Mobility",                   "token": "99926054", "symbol": "Nifty Mobility"},
        {"name": "NIFTY REITs & InvITs",             "token": "99926055", "symbol": "Nifty REITs"},
    ],
}

def get_all_indices():
    all_indices = []
    for category, indices in INDICES.items():
        for idx in indices:
            all_indices.append({**idx, "category": category})
    return all_indices
