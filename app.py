# ============================================================
# app.py — NSE Index Dashboard (Phase 1 + 2 + 3)
# ============================================================
# Run with: streamlit run app.py
# ============================================================

import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from tokens   import INDICES
from api      import login_angel, fetch_weekly_data
from cache    import save_cache, load_cache, get_last_updated, cache_exists
from analytics import (
    build_heatmap_matrix,
    get_best_worst_per_week,
    compute_momentum_signal,
    compute_sector_rotation,
    compute_breakout_signal,
    compute_weakness_signal,
    get_summary_stats,
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Index Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 4px 0;
    }
    .signal-strong  { color: #00ff88; font-weight: bold; }
    .signal-weak    { color: #ff4444; font-weight: bold; }
    .signal-neutral { color: #ffaa00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR — LOGIN + CONTROLS
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("📊 NSE Dashboard")
    st.markdown("---")

    st.subheader("🔐 Angel One Login")
    api_key     = st.text_input("API Key",      type="password")
    client_id   = st.text_input("Client ID")
    password    = st.text_input("Password",     type="password")
    totp_secret = st.text_input("TOTP Secret",  type="password",
                                help="Your Angel One TOTP secret key (not the 6-digit OTP)")

    st.markdown("---")
    st.subheader("📅 Settings")
    weeks = st.selectbox("Time Period", [4, 13, 26, 52], index=3,
                         format_func=lambda x: f"Last {x} weeks")

    st.markdown("---")
    refresh_btn = st.button("🔄 Refresh Data", use_container_width=True, type="primary")
    last_upd    = get_last_updated()
    st.caption(f"Last updated: {last_upd}")

    st.markdown("---")
    st.caption("⚠️ Token mismatches can occur. Verify at: margincalculator.angelbroking.com")


# ─────────────────────────────────────────────
# DATA FETCH LOGIC
# ─────────────────────────────────────────────
if "all_data" not in st.session_state:
    st.session_state.all_data = {}

if refresh_btn:
    if not all([api_key, client_id, password, totp_secret]):
        st.sidebar.error("Please fill all login fields first.")
    else:
        with st.spinner("🔐 Logging in to Angel One..."):
            try:
                obj = login_angel(api_key, client_id, password, totp_secret)
                st.sidebar.success("✅ Logged in!")
            except Exception as e:
                st.sidebar.error(f"Login failed: {e}")
                st.stop()

        all_indices = []
        for cat, lst in INDICES.items():
            all_indices.extend(lst)

        progress   = st.progress(0, text="Fetching index data...")
        all_data   = {}
        errors     = []
        total      = len(all_indices)

        for i, idx in enumerate(all_indices):
            name  = idx["name"]
            token = idx["token"]
            try:
                df = fetch_weekly_data(obj, token, weeks=52)
                all_data[name] = df
            except Exception as e:
                all_data[name] = pd.DataFrame()
                errors.append(f"{name}: {e}")

            progress.progress((i + 1) / total,
                              text=f"Fetching {name} ({i+1}/{total})...")
            time.sleep(0.15)  # avoid rate limit

        progress.empty()
        save_cache(all_data)
        st.session_state.all_data = all_data

        if errors:
            with st.expander(f"⚠️ {len(errors)} indices had errors"):
                for e in errors:
                    st.warning(e)
        else:
            st.sidebar.success(f"✅ All {total} indices loaded!")

elif cache_exists() and not st.session_state.all_data:
    st.session_state.all_data = load_cache()

all_data = st.session_state.all_data


# ─────────────────────────────────────────────
# HELPER: filter data to selected week range
# ─────────────────────────────────────────────
def filter_weeks(data: dict, n: int) -> dict:
    filtered = {}
    for name, df in data.items():
        if df is not None and not df.empty:
            filtered[name] = df.tail(n).copy()
            filtered[name]["week_num"] = range(1, len(filtered[name]) + 1)
    return filtered


# ─────────────────────────────────────────────
# HELPER: styled heatmap table
# ─────────────────────────────────────────────
def render_heatmap(matrix: pd.DataFrame):
    if matrix.empty:
        st.warning("No data available.")
        return

    def color_cell(val):
        if pd.isna(val):
            return "background-color: #2a2a3e; color: #666"
        if val > 2:
            bg = "#006600"
        elif val > 1:
            bg = "#008800"
        elif val > 0:
            bg = "#00aa44"
        elif val > -1:
            bg = "#cc2200"
        elif val > -2:
            bg = "#aa0000"
        else:
            bg = "#880000"
        return f"background-color: {bg}; color: white; font-weight: 600"

    styled = matrix.style.applymap(color_cell).format("{:+.2f}%", na_rep="—")
    st.dataframe(styled, use_container_width=True, height=500)


# ─────────────────────────────────────────────
# HELPER: Bar / Line chart for single index
# ─────────────────────────────────────────────
def render_index_chart(df: pd.DataFrame, index_name: str, chart_type: str):
    if df is None or df.empty:
        st.warning("No data for this index.")
        return

    weeks_label = [f"W{int(w)}" for w in df["week_num"]]
    pcts        = df["weekly_pct"].values
    colors      = ["#00cc66" if p >= 0 else "#ff4444" for p in pcts]

    if chart_type == "Bar Chart":
        fig = go.Figure(go.Bar(
            x=weeks_label, y=pcts,
            marker_color=colors,
            text=[f"{p:+.2f}%" for p in pcts],
            textposition="outside",
        ))
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weeks_label, y=pcts,
            mode="lines+markers",
            line=dict(color="#4da6ff", width=2),
            marker=dict(color=colors, size=8),
            text=[f"{p:+.2f}%" for p in pcts],
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#666")

    fig.update_layout(
        title=f"{index_name} — Weekly % Change",
        xaxis_title="Week",
        yaxis_title="% Change",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="white"),
        height=420,
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.title("📊 NSE Index Tracker — 47 Indices × 52 Weeks")
st.caption("Phase 1: Heatmap  |  Phase 2: Best/Worst  |  Phase 3: Trading Signals")

if not all_data:
    st.info("👈 Enter your Angel One credentials in the sidebar and click **Refresh Data** to begin.")
    st.stop()

filtered_data = filter_weeks(all_data, weeks)


# ─────────────────────────────────────────────
# TABS: Broad Market | Sectoral | Thematic | 🚦 Signals
# ─────────────────────────────────────────────
tab_broad, tab_sector, tab_thematic, tab_signals = st.tabs([
    "📈 Broad Market",
    "🏭 Sectoral",
    "🎯 Thematic",
    "🚦 Trading Signals",
])


def render_category_tab(tab, category: str):
    with tab:
        cat_indices = INDICES[category]
        matrix = build_heatmap_matrix(filtered_data, cat_indices)

        # ── Section 1: Heatmap ──
        st.subheader(f"🌡️ Heatmap — {category} ({len(cat_indices)} indices × last {weeks} weeks)")
        render_heatmap(matrix)

        # ── Section 2: Best / Worst per week ──
        st.subheader("🏆 Best & 💀 Worst Performer — Each Week")
        bw = get_best_worst_per_week(matrix)
        if not bw.empty:
            st.dataframe(
                bw.style
                  .applymap(lambda v: "color: #00cc66; font-weight:bold"
                             if isinstance(v, float) and v > 0
                             else ("color: #ff4444; font-weight:bold"
                                   if isinstance(v, float) and v < 0
                                   else ""),
                             subset=["Best %", "Worst %"]),
                use_container_width=True, height=300,
            )

        # ── Section 3: Summary stats ──
        with st.expander("📋 Summary Stats (Avg, Volatility, Green/Red weeks)"):
            stats = get_summary_stats(matrix)
            st.dataframe(stats, use_container_width=True)

        # ── Section 4: Index Chart ──
        st.subheader("📈 Index Deep Dive — Weekly Chart")
        col1, col2 = st.columns([3, 1])
        with col1:
            available = [i["name"] for i in cat_indices if i["name"] in filtered_data]
            sel_index = st.selectbox("Select Index", available, key=f"sel_{category}")
        with col2:
            chart_type = st.radio("Chart Type", ["Bar Chart", "Line Chart"],
                                  key=f"ct_{category}", horizontal=True)

        if sel_index:
            render_index_chart(filtered_data.get(sel_index), sel_index, chart_type)


render_category_tab(tab_broad,    "Broad Market")
render_category_tab(tab_sector,   "Sectoral")
render_category_tab(tab_thematic, "Thematic")


# ─────────────────────────────────────────────
# TAB 4: TRADING SIGNALS (PHASE 3)
# ─────────────────────────────────────────────
with tab_signals:
    st.subheader("🚦 Trading Signals — All 47 Indices")
    st.caption("Signals computed from the last 52 weeks of weekly % change data.")

    # Build full matrix across ALL categories
    all_cat_indices = []
    for cat, lst in INDICES.items():
        all_cat_indices.extend(lst)
    full_matrix = build_heatmap_matrix(filtered_data, all_cat_indices)

    if full_matrix.empty:
        st.warning("No data loaded yet. Please refresh first.")
        st.stop()

    sig1, sig2, sig3, sig4 = st.tabs([
        "🔥 Momentum",
        "🔄 Sector Rotation",
        "⚡ 52W Breakout",
        "📉 Weakness Radar",
    ])

    with sig1:
        st.markdown("""
        **Momentum Signal** — Compares avg return of last 4 weeks vs last 13 weeks.
        - 🔥 STRONG → Accelerating uptrend
        - 📈 RISING → Positive & improving
        - 📉 FADING → Was good, now slowing
        - ❄️ WEAK  → Downtrend / no momentum
        """)
        mom = compute_momentum_signal(full_matrix)
        if not mom.empty:
            def style_momentum(val):
                if "STRONG" in str(val): return "color:#00ff88;font-weight:bold"
                if "RISING" in str(val): return "color:#88ff44;font-weight:bold"
                if "FADING" in str(val): return "color:#ffaa00;font-weight:bold"
                if "WEAK"   in str(val): return "color:#ff4444;font-weight:bold"
                return ""
            st.dataframe(
                mom.style.applymap(style_momentum, subset=["Momentum"]),
                use_container_width=True, height=600,
            )

    with sig2:
        st.markdown("""
        **Sector Rotation** — Compares last 4 weeks vs prior 4 weeks.
        - 🟢 Strong Inflow → Fresh money entering
        - 🟡 Mild Inflow  → Slowly gaining interest
        - 🟠 Mild Outflow → Money starting to leave
        - 🔴 Strong Outflow → Sector being dumped
        """)
        rot = compute_sector_rotation(full_matrix)
        if not rot.empty:
            def color_delta(val):
                if isinstance(val, float):
                    return "color:#00cc66" if val > 0 else "color:#ff4444"
                return ""
            st.dataframe(
                rot.style.applymap(color_delta, subset=["Δ Flow"]),
                use_container_width=True, height=600,
            )

    with sig3:
        st.markdown("""
        **52-Week Breakout** — How far is each index from its 52-week high?
        - ⚡ BREAKOUT → Within 2% of 52W high (Buy signal)
        - 🔔 Near High → Within 5%
        - 🚨 Deep Correction → >20% below high (Value zone or downtrend)
        """)
        bo = compute_breakout_signal(all_data, all_cat_indices)
        if not bo.empty:
            def style_signal(val):
                if "BREAKOUT" in str(val): return "color:#00ff88;font-weight:bold"
                if "Near"     in str(val): return "color:#88ff44"
                if "Deep"     in str(val): return "color:#ff4444;font-weight:bold"
                return "color:#aaaaaa"
            st.dataframe(
                bo.style.applymap(style_signal, subset=["Signal"]),
                use_container_width=True, height=600,
            )

    with sig4:
        st.markdown("""
        **Weakness Radar** — Consecutive red weeks + below average returns.
        - 🚨 HIGH RISK → 3+ red weeks & below category avg
        - ⚠️ WATCH     → 2 consecutive red weeks
        - 🟡 CAUTION   → 1 red week
        - ✅ OK        → Currently green or recovering
        """)
        weak = compute_weakness_signal(full_matrix)
        if not weak.empty:
            def style_weakness(val):
                if "HIGH RISK" in str(val): return "color:#ff2222;font-weight:bold"
                if "WATCH"     in str(val): return "color:#ff8800;font-weight:bold"
                if "CAUTION"   in str(val): return "color:#ffcc00"
                if "OK"        in str(val): return "color:#00cc66"
                return ""
            st.dataframe(
                weak.style.applymap(style_weakness, subset=["Weakness"]),
                use_container_width=True, height=600,
            )

    # ── Signal Summary Board ──
    st.markdown("---")
    st.subheader("📋 Signal Summary Board")
    c1, c2, c3, c4 = st.columns(4)

    if not full_matrix.empty:
        mom_strong = compute_momentum_signal(full_matrix)
        rot_df     = compute_sector_rotation(full_matrix)
        bo_df      = compute_breakout_signal(all_data, all_cat_indices)
        weak_df    = compute_weakness_signal(full_matrix)

        with c1:
            top_mom = mom_strong[mom_strong["Momentum"].str.contains("STRONG")]["Index"].tolist()
            st.markdown("**🔥 Top Momentum**")
            for x in top_mom[:5]:
                st.success(x)

        with c2:
            inflow = rot_df[rot_df["Rotation"].str.contains("Strong Inflow")]["Index"].tolist()
            st.markdown("**🟢 Strong Inflow**")
            for x in inflow[:5]:
                st.success(x)

        with c3:
            breakouts = bo_df[bo_df["Signal"].str.contains("BREAKOUT")]["Index"].tolist()
            st.markdown("**⚡ Breakouts**")
            for x in breakouts[:5]:
                st.info(x)

        with c4:
            risky = weak_df[weak_df["Weakness"].str.contains("HIGH RISK")]["Index"].tolist()
            st.markdown("**🚨 High Risk**")
            for x in risky[:5]:
                st.error(x)
