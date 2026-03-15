# ============================================================
# analytics.py — Phase 2 + Phase 3 Analytics & Trading Signals
# ============================================================

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────
# PHASE 2 — Best / Worst Index Per Week
# ─────────────────────────────────────────────

def build_heatmap_matrix(all_data: dict, category_indices: list) -> pd.DataFrame:
    """
    Build a (indices × weeks) matrix of weekly % changes.
    Rows = index names, Columns = Week 1, Week 2, ...
    """
    frames = {}
    for idx in category_indices:
        name = idx["name"]
        if name in all_data and not all_data[name].empty:
            df = all_data[name]
            series = df.set_index("week_num")["weekly_pct"]
            frames[name] = series

    if not frames:
        return pd.DataFrame()

    matrix = pd.DataFrame(frames).T
    matrix.columns = [f"W{int(c)}" for c in matrix.columns]
    return matrix.round(2)


def get_best_worst_per_week(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    For each week column, find best and worst performing index.
    Returns DataFrame: week | best_index | best_pct | worst_index | worst_pct
    """
    rows = []
    for col in matrix.columns:
        col_data = matrix[col].dropna()
        if col_data.empty:
            continue
        best_idx  = col_data.idxmax()
        worst_idx = col_data.idxmin()
        rows.append({
            "Week":         col,
            "🏆 Best Index":  best_idx,
            "Best %":        round(col_data[best_idx], 2),
            "💀 Worst Index": worst_idx,
            "Worst %":       round(col_data[worst_idx], 2),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# PHASE 3 — Trading Signals
# ─────────────────────────────────────────────

def compute_momentum_signal(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    🔥 Momentum: Compare avg return last 4 weeks vs last 13 weeks.
    Signal = STRONG / RISING / FADING / WEAK
    """
    rows = []
    for idx_name in matrix.index:
        series = matrix.loc[idx_name].dropna()
        if len(series) < 4:
            continue

        avg_4w  = series.tail(4).mean()
        avg_13w = series.tail(13).mean() if len(series) >= 13 else series.mean()

        diff = avg_4w - avg_13w

        if avg_4w > 0 and diff > 0.3:
            signal = "🔥 STRONG"
        elif avg_4w > 0 and diff >= 0:
            signal = "📈 RISING"
        elif avg_4w < 0 and diff < 0:
            signal = "📉 FADING"
        else:
            signal = "❄️ WEAK"

        rows.append({
            "Index":        idx_name,
            "Avg 4W %":     round(avg_4w, 2),
            "Avg 13W %":    round(avg_13w, 2),
            "Momentum":     signal,
        })

    df = pd.DataFrame(rows).sort_values("Avg 4W %", ascending=False)
    return df.reset_index(drop=True)


def compute_sector_rotation(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    🔄 Sector Rotation: Compare last 4 weeks avg vs prior 4 weeks avg.
    Positive delta = Money flowing IN. Negative = Money flowing OUT.
    """
    rows = []
    for idx_name in matrix.index:
        series = matrix.loc[idx_name].dropna()
        if len(series) < 8:
            continue

        recent = series.tail(4).mean()
        prior  = series.iloc[-8:-4].mean()
        delta  = recent - prior

        if delta > 0.5:
            flow = "🟢 Strong Inflow"
        elif delta > 0:
            flow = "🟡 Mild Inflow"
        elif delta > -0.5:
            flow = "🟠 Mild Outflow"
        else:
            flow = "🔴 Strong Outflow"

        rows.append({
            "Index":        idx_name,
            "Recent 4W %":  round(recent, 2),
            "Prior 4W %":   round(prior, 2),
            "Δ Flow":       round(delta, 2),
            "Rotation":     flow,
        })

    df = pd.DataFrame(rows).sort_values("Δ Flow", ascending=False)
    return df.reset_index(drop=True)


def compute_breakout_signal(all_data: dict, category_indices: list) -> pd.DataFrame:
    """
    ⚡ Breakout: Is current close near 52-week high?
    Distance from 52-week high < 2% → BREAKOUT
    """
    rows = []
    for idx in category_indices:
        name = idx["name"]
        if name not in all_data or all_data[name].empty:
            continue

        df = all_data[name]
        if "close" not in df.columns or len(df) < 2:
            continue

        closes       = df["close"].dropna()
        current      = closes.iloc[-1]
        high_52w     = closes.max()
        low_52w      = closes.min()
        dist_from_high = ((high_52w - current) / high_52w) * 100

        if dist_from_high <= 2:
            signal = "⚡ BREAKOUT"
        elif dist_from_high <= 5:
            signal = "🔔 Near High"
        elif dist_from_high >= 20:
            signal = "🚨 Deep Correction"
        else:
            signal = "➖ Neutral"

        rows.append({
            "Index":           name,
            "Current":         round(current, 2),
            "52W High":        round(high_52w, 2),
            "52W Low":         round(low_52w, 2),
            "% From High":     round(dist_from_high, 2),
            "Signal":          signal,
        })

    df = pd.DataFrame(rows).sort_values("% From High")
    return df.reset_index(drop=True)


def compute_weakness_signal(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    📉 Weakness: Consecutive red weeks + below category average.
    """
    rows = []
    overall_avg = matrix.tail(4).mean(axis=0).mean()  # rolling category avg

    for idx_name in matrix.index:
        series = matrix.loc[idx_name].dropna()
        if len(series) < 4:
            continue

        # Count consecutive red weeks from the end
        streak = 0
        for val in reversed(series.values):
            if val < 0:
                streak += 1
            else:
                break

        recent_avg = series.tail(4).mean()

        if streak >= 3 and recent_avg < overall_avg:
            signal = "🚨 HIGH RISK"
        elif streak >= 2:
            signal = "⚠️ WATCH"
        elif streak == 1:
            signal = "🟡 CAUTION"
        else:
            signal = "✅ OK"

        rows.append({
            "Index":          idx_name,
            "Red Streak":     streak,
            "Avg 4W %":       round(recent_avg, 2),
            "Weakness":       signal,
        })

    df = pd.DataFrame(rows).sort_values("Red Streak", ascending=False)
    return df.reset_index(drop=True)


def get_summary_stats(matrix: pd.DataFrame) -> pd.DataFrame:
    """Overall summary: avg return + volatility per index."""
    rows = []
    for idx_name in matrix.index:
        series = matrix.loc[idx_name].dropna()
        if series.empty:
            continue
        rows.append({
            "Index":      idx_name,
            "Avg W%":     round(series.mean(), 2),
            "Volatility": round(series.std(), 2),
            "Max Gain":   round(series.max(), 2),
            "Max Loss":   round(series.min(), 2),
            "Green Wks":  int((series > 0).sum()),
            "Red Wks":    int((series < 0).sum()),
        })
    return pd.DataFrame(rows).sort_values("Avg W%", ascending=False).reset_index(drop=True)
