# 📊 NSE Index Dashboard

Track 47 NSE indices × 52 weeks with trading signals.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the dashboard
streamlit run app.py
```

## Login
Enter in the sidebar:
- **API Key** → from Angel One developer portal
- **Client ID** → your Angel One login ID
- **Password** → your Angel One login password
- **TOTP Secret** → the secret key from your authenticator setup
  (NOT the 6-digit code — the base32 secret, e.g. `JBSWY3DPEHPK3PXP`)

## Features

### Phase 1 — Core
- 47 indices across Broad Market, Sectoral, Thematic tabs
- Weekly % change heatmap (green = gain, red = loss)
- Bar or Line chart per index

### Phase 2 — Analytics
- Best 🏆 and Worst 💀 index each week
- Summary stats: avg return, volatility, green/red weeks

### Phase 3 — Trading Signals
- 🔥 **Momentum** — 4W vs 13W trend comparison
- 🔄 **Sector Rotation** — where money is flowing
- ⚡ **52W Breakout** — indices near yearly highs
- 📉 **Weakness Radar** — consecutive red streaks

## File Structure
```
nse_dashboard/
├── app.py           ← Streamlit UI (main entry)
├── api.py           ← Angel One SmartAPI login + fetch
├── tokens.py        ← All 47 index tokens
├── cache.py         ← JSON data cache
├── analytics.py     ← All signal computations
├── requirements.txt
└── cache/           ← Auto-created on first refresh
    └── index_data.json
```

## Notes
- Token list is based on Angel One's internal NSE index tokens.
  If any index fails, verify tokens from:
  https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json
- Data is cached locally. Click **Refresh Data** to re-fetch.
- Angel One allows ~3 req/sec on historical data API.
