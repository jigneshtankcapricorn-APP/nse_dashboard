# ============================================================
# app.py — NSE Index Dashboard (Phase 1 + 2 + 3)
# Run with: streamlit run app.py
# ============================================================

import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from tokens    import INDICES
from api       import login_angel, fetch_weekly_data
from cache     import save_cache, load_cache, get_last_updated, cache_exists
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
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }

    /* ── Login Card ── */
    .login-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 24px;
        padding: 52px 60px 44px 60px;
        text-align: center;
        box-shadow: 0 12px 48px rgba(0,0,0,0.5);
    }
    .login-logo  { font-size: 64px; margin-bottom: 6px; }
    .login-title { font-size: 28px; font-weight: 800; color: #ffffff; margin-bottom: 4px; }
    .login-sub   { font-size: 14px; color: #8888aa; margin-bottom: 36px; line-height: 1.6; }
    .login-badge {
        display: inline-block;
        background: #12122a;
        border: 1px solid #2a2a5a;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 11px;
        color: #5566aa;
        margin-top: 28px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "app_authed" not in st.session_state: st.session_state.app_authed = False
if "session"    not in st.session_state: st.session_state.session    = None
if "all_data"   not in st.session_state: st.session_state.all_data   = {}

# Hide sidebar on all login screens
if not st.session_state.logged_in:
    st.markdown("""
    <style>
        [data-testid="stSidebar"]        { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 1 — App Username / Password Gate
# ─────────────────────────────────────────────
if not st.session_state.app_authed:

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">📊</div>
            <div class="login-title">NSE Index Dashboard</div>
            <div class="login-sub">
                47 Indices &nbsp;·&nbsp; 52 Weeks &nbsp;·&nbsp; Live Signals<br>
                Broad Market · Sectoral · Thematic
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        username_input = st.text_input("Username", placeholder="Enter username")
        password_input = st.text_input("Password", placeholder="Enter password", type="password")

        st.write("")
        auth_clicked = st.button("Login  →", use_container_width=True, type="primary")

        st.markdown(
            "<div class='login-badge'>🔒 Secured · NSE Index Dashboard</div>",
            unsafe_allow_html=True,
        )

        if auth_clicked:
            try:
                valid_user = st.secrets["APP_USERNAME"]
                valid_pass = st.secrets["APP_PASSWORD"]
            except KeyError as e:
                st.error(f"Missing secret: {e}. Add APP_USERNAME and APP_PASSWORD in Streamlit Secrets.")
                st.stop()

            if username_input == valid_user and password_input == valid_pass:
                st.session_state.app_authed = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    st.stop()

# ─────────────────────────────────────────────
# STEP 2 — Connect to Angel One
# ─────────────────────────────────────────────
if not st.session_state.logged_in:

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">📊</div>
            <div class="login-title">NSE Index Dashboard</div>
            <div class="login-sub">
                Authenticated ✅<br>Now connect your Angel One account to load live data.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        connect_clicked = st.button(
            "🔐  Connect to Angel One",
            use_container_width=True,
            type="primary",
        )

        st.markdown(
            "<div class='login-badge'>🔒 Credentials loaded from Streamlit Secrets · Never stored in code</div>",
            unsafe_allow_html=True,
        )

        if connect_clicked:
            try:
                api_key     = st.secrets["API_KEY"]
                client_id   = st.secrets["CLIENT_ID"]
                password    = st.secrets["PASSWORD"]
                totp_secret = st.secrets["TOTP_KEY"]
            except KeyError as e:
                st.error(f"Missing secret key: {e}. Add it in Streamlit Cloud → Settings → Secrets.")
                st.stop()

            with st.spinner("Connecting to Angel One..."):
                try:
                    session = login_angel(api_key, client_id, password, totp_secret)
                    st.session_state.session   = session
                    st.session_state.logged_in = True
                    if cache_exists():
                        st.session_state.all_data = load_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    st.stop()


# ─────────────────────────────────────────────
# SIDEBAR — visible only after login
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("📊 NSE Dashboard")
    st.markdown("---")

    st.subheader("📅 Settings")
    weeks = st.selectbox(
        "Time Period", [4, 13, 26, 52], index=3,
        format_func=lambda x: f"Last {x} weeks"
    )

    st.markdown("---")
    refresh_btn = st.button("🔄 Refresh Data", use_container_width=True, type="primary")
    last_upd = get_last_updated()
    st.caption(f"Last updated: {last_upd}")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.session   = None
        st.session_state.all_data  = {}
        st.rerun()

    st.markdown("---")
    st.caption("⚠️ If any index fails, verify token at:\nmargincalculator.angelbroking.com")


# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
session = st.session_state.session

if refresh_btn:
    all_indices = []
    for cat, lst in INDICES.items():
        all_indices.extend(lst)

    progress = st.progress(0, text="Fetching index data...")
    all_data = {}
    errors   = []
    total    = len(all_indices)

    for i, idx in enumerate(all_indices):
        name  = idx["name"]
        token = idx["token"]
        try:
            df = fetch_weekly_data(session, token, weeks=52)
            all_data[name] = df
        except Exception as e:
            all_data[name] = pd.DataFrame()
            errors.append(f"{name}: {e}")

        progress.progress((i + 1) / total, text=f"Fetching {name} ({i+1}/{total})...")
        time.sleep(0.15)

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
# HELPERS
# ─────────────────────────────────────────────
def filter_weeks(data: dict, n: int) -> dict:
    filtered = {}
    for name, df in data.items():
        if df is not None and not df.empty:
            filtered[name] = df.tail(n).copy()
            filtered[name]["week_num"] = range(1, len(filtered[name]) + 1)
    return filtered


def render_heatmap(matrix: pd.DataFrame):
    if matrix.empty:
        st.warning("No data available.")
        return

    def color_cell(val):
        if pd.isna(val):
            return "background-color: #2a2a3e; color: #666"
        if   val >  10: bg = "#004400"
        elif val >   2: bg = "#006600"
        elif val >   1: bg = "#008800"
        elif val >   0: bg = "#00aa44"
        elif val >  -1: bg = "#cc2200"
        elif val >  -2: bg = "#aa0000"
        else:           bg = "#880000"
        return f"background-color: {bg}; color: white; font-weight: 600"

    def color_cumulative(val):
        """Stronger color scale for the 52W Return% column."""
        if pd.isna(val):
            return "background-color: #2a2a3e; color: #666"
        if   val >  30: bg = "#003300"; border = "3px solid #00ff88"
        elif val >  15: bg = "#005500"; border = "2px solid #00cc66"
        elif val >   0: bg = "#007700"; border = ""
        elif val > -15: bg = "#aa0000"; border = ""
        else:           bg = "#660000"; border = "2px solid #ff4444"
        style = f"background-color: {bg}; color: white; font-weight: 800; font-size: 13px"
        return style

    # Single styling function — pandas 2.x compatible (use .map not .applymap)
    def style_all(val, col_name):
        if col_name == "52W Return%":
            return color_cumulative(val)
        return color_cell(val)

    styled = matrix.style.apply(
        lambda col: [style_all(v, col.name) for v in col], axis=0
    ).format("{:+.2f}%", na_rep="—")
    st.dataframe(styled, use_container_width=True, height=500)


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
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#666")

    fig.update_layout(
        title=f"{index_name} — Weekly % Change",
        xaxis_title="Week", yaxis_title="% Change",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
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
    st.info("👈 Click **Refresh Data** in the sidebar to fetch all 47 indices.")
    st.stop()

filtered_data = filter_weeks(all_data, weeks)


# ─────────────────────────────────────────────
# TABS
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

        st.subheader(f"🌡️ Heatmap — {category} ({len(cat_indices)} indices × last {weeks} weeks)")
        render_heatmap(matrix)

        st.subheader("🏆 Best & 💀 Worst Performer — Each Week")
        bw = get_best_worst_per_week(matrix)
        if not bw.empty:
            st.dataframe(
                bw.style.map(
                    lambda v: "color:#00cc66;font-weight:bold" if isinstance(v, float) and v > 0
                    else ("color:#ff4444;font-weight:bold" if isinstance(v, float) and v < 0 else ""),
                    subset=["Best %", "Worst %"],
                ),
                use_container_width=True, height=300,
            )

        with st.expander("📋 Summary Stats (Avg, Volatility, Green/Red weeks)"):
            stats = get_summary_stats(matrix)
            st.dataframe(stats, use_container_width=True)

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
# TRADING SIGNALS TAB
# ─────────────────────────────────────────────
with tab_signals:
    st.subheader("🚦 Trading Signals — All 47 Indices")
    st.caption("Signals computed from weekly % change data.")

    all_cat_indices = []
    for cat, lst in INDICES.items():
        all_cat_indices.extend(lst)
    full_matrix = build_heatmap_matrix(filtered_data, all_cat_indices)

    if full_matrix.empty:
        st.warning("No data loaded yet. Please click Refresh Data.")
        st.stop()

    sig1, sig2, sig3, sig4 = st.tabs([
        "🔥 Momentum", "🔄 Sector Rotation", "⚡ 52W Breakout", "📉 Weakness Radar",
    ])

    with sig1:
        st.markdown("**Momentum** — Avg last 4W vs 13W. 🔥 STRONG · 📈 RISING · 📉 FADING · ❄️ WEAK")
        mom = compute_momentum_signal(full_matrix)
        if not mom.empty:
            def style_mom(val):
                m = {"STRONG": "#00ff88", "RISING": "#88ff44", "FADING": "#ffaa00", "WEAK": "#ff4444"}
                return f"color:{m[val]};font-weight:bold" if val in m else ""
            st.dataframe(mom.style.map(style_mom, subset=["Momentum"]),
                         use_container_width=True, height=600)

    with sig2:
        st.markdown("**Rotation** — Last 4W vs prior 4W. 🟢 Strong Inflow · 🔴 Strong Outflow")
        rot = compute_sector_rotation(full_matrix)
        if not rot.empty:
            st.dataframe(
                rot.style.map(
                    lambda v: "color:#00cc66" if isinstance(v, float) and v > 0
                    else ("color:#ff4444" if isinstance(v, float) and v < 0 else ""),
                    subset=["Flow_Delta"],
                ),
                use_container_width=True, height=600,
            )

    with sig3:
        st.markdown("**Breakout** — Distance from 52W high. ⚡ BREAKOUT (<2%) · 🚨 Deep Correction (>20%)")
        bo = compute_breakout_signal(all_data, all_cat_indices)
        if not bo.empty:
            def style_bo(val):
                m = {"BREAKOUT": "color:#00ff88;font-weight:bold", "Near High": "color:#88ff44",
                     "Deep Correction": "color:#ff4444;font-weight:bold", "Neutral": "color:#aaaaaa"}
                return m.get(str(val), "color:#aaaaaa")
            st.dataframe(bo.style.map(style_bo, subset=["Signal"]),
                         use_container_width=True, height=600)

    with sig4:
        st.markdown("**Weakness** — Consecutive red weeks. 🚨 HIGH RISK · ⚠️ WATCH · 🟡 CAUTION · ✅ OK")
        weak = compute_weakness_signal(full_matrix)
        if not weak.empty:
            def style_weak(val):
                m = {"HIGH RISK": "color:#ff2222;font-weight:bold", "WATCH": "color:#ff8800;font-weight:bold",
                     "CAUTION": "color:#ffcc00", "OK": "color:#00cc66"}
                return m.get(str(val), "")
            st.dataframe(weak.style.map(style_weak, subset=["Weakness"]),
                         use_container_width=True, height=600)

    # Signal Summary Board
    st.markdown("---")
    st.subheader("📋 Signal Summary Board")
    c1, c2, c3, c4 = st.columns(4)

    rot_df  = compute_sector_rotation(full_matrix)
    bo_df   = compute_breakout_signal(all_data, all_cat_indices)
    weak_df = compute_weakness_signal(full_matrix)
    mom_df  = compute_momentum_signal(full_matrix)

    with c1:
        st.markdown("**🔥 Top Momentum**")
        for x in mom_df[mom_df["Momentum"] == "STRONG"]["Index"].tolist()[:5]:
            st.success(x)

    with c2:
        st.markdown("**🟢 Strong Inflow**")
        for x in rot_df[rot_df["Rotation"] == "Strong Inflow"]["Index"].tolist()[:5]:
            st.success(x)

    with c3:
        st.markdown("**⚡ Breakouts**")
        for x in bo_df[bo_df["Signal"] == "BREAKOUT"]["Index"].tolist()[:5]:
            st.info(x)

    with c4:
        st.markdown("**🚨 High Risk**")
        for x in weak_df[weak_df["Weakness"] == "HIGH RISK"]["Index"].tolist()[:5]:
            st.error(x)
