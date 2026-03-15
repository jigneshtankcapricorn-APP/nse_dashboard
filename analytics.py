# ============================================================
# analytics.py — Phase 2 + Phase 3 Analytics & Trading Signals
# ============================================================

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────
# OUTLIER CLEANING
# Cap weekly returns at ±15% to filter API glitches
# (No real index moves >15% in a single week normally)
# ─────────────────────────────────────────────
OUTLIER_CAP = 15.0

def clean_series(series: pd.Series) -> pd.Series:
    """Cap outliers at ±15% and return cleaned series."""
    return series.clip(lower=-OUTLIER_CAP, upper=OUTLIER_CAP)


# ─────────────────────────────────────────────
# PHASE 2 — Heatmap Matrix
# ─────────────────────────────────────────────

def build_heatmap_matrix(all_data: dict, category_indices: list) -> pd.DataFrame:
    """
    Build (indices × weeks) matrix of weekly % changes.
    Columns ordered: W52 → W1 (newest first).
    Outliers capped at ±15%.
    Last column = 52W cumulative return.
    """
    frames = {}
    cumulative = {}

    for idx in category_indices:
        name = idx["name"]
        if name in all_data and not all_data[name].empty:
            df   = all_data[name]
            raw  = df.set_index("week_num")["weekly_pct"]
            cleaned = clean_series(raw)
            frames[name] = cleaned

            # 52W cumulative: compound (1 + r/100) product → %
            cum = (np.prod(1 + cleaned.values / 100) - 1) * 100
            cumulative[name] = round(cum, 2)

    if not frames:
        return pd.DataFrame()

    matrix = pd.DataFrame(frames).T
    matrix.columns = [f"W{int(c)}" for c in matrix.columns]

    # Newest week on left (W52 → W1)
    matrix = matrix[matrix.columns[::-1]]
    matrix = matrix.round(2)

    # Add 52W cumulative return as first column
    matrix.insert(0, "52W Return%", pd.Series(cumulative))

    return matrix


def get_best_worst_per_week(matrix: pd.DataFrame) -> pd.DataFrame:
    """Best and worst index each week (excludes 52W Return% column)."""
    rows = []
    week_cols = [c for c in matrix.columns if c.startswith("W")]
    for col in week_cols:
        col_data = matrix[col].dropna()
        if col_data.empty:
            continue
        best_idx  = col_data.idxmax()
        worst_idx = col_data.idxmin()
        rows.append({
            "Week":          col,
            "Best Index":    best_idx,
            "Best %":        round(col_data[best_idx], 2),
            "Worst Index":   worst_idx,
            "Worst %":       round(col_data[worst_idx], 2),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# PHASE 3 — Trading Signals
# NOTE: matrix columns are W52→W1 (newest first).
# Use iloc[:N] for most-recent N weeks (left side).
# ─────────────────────────────────────────────

def _recent_weeks(series: pd.Series, n: int) -> pd.Series:
    """Get most-recent N weeks from a reversed (W52→W1) row series."""
    week_vals = series[[c for c in series.index if c.startswith("W")]].dropna()
    return week_vals.iloc[:n]  # leftmost = newest


def compute_momentum_signal(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Momentum: Avg last 4W vs last 13W (newest = left side of matrix).
    STRONG / RISING / FADING / WEAK
    """
    rows = []
    for idx_name in matrix.index:
        series = matrix.loc[idx_name]
        week_series = series[[c for c in series.index if c.startswith("W")]].dropna()

        if len(week_series) < 4:
            continue

        avg_4w  = week_series.iloc[:4].mean()
        avg_13w = week_series.iloc[:13].mean() if len(week_series) >= 13 else week_series.mean()
        diff    = avg_4w - avg_13w

        if avg_4w > 0 and diff > 0.3:
            signal = "STRONG"
        elif avg_4w > 0 and diff >= 0:
            signal = "RISING"
        elif avg_4w < 0 and diff < 0:
            signal = "FADING"
        else:
            signal = "WEAK"

        rows.append({
            "Index":     idx_name,
            "Avg 4W %":  round(avg_4w, 2),
            "Avg 13W %": round(avg_13w, 2),
            "Momentum":  signal,
        })

    df = pd.DataFrame(rows).sort_values("Avg 4W %", ascending=False)
    return df.reset_index(drop=True)


def compute_sector_rotation(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Rotation: Last 4W avg vs prior 4W avg (newest = left).
    Positive = money flowing IN, negative = OUT.
    """
    rows = []
    for idx_name in matrix.index:
        series      = matrix.loc[idx_name]
        week_series = series[[c for c in series.index if c.startswith("W")]].dropna()

        if len(week_series) < 8:
            continue

        recent = week_series.iloc[:4].mean()   # newest 4 weeks
        prior  = week_series.iloc[4:8].mean()  # prior 4 weeks
        delta  = recent - prior

        if delta > 0.5:
            flow = "Strong Inflow"
        elif delta > 0:
            flow = "Mild Inflow"
        elif delta > -0.5:
            flow = "Mild Outflow"
        else:
            flow = "Strong Outflow"

        rows.append({
            "Index":       idx_name,
            "Recent 4W %": round(recent, 2),
            "Prior 4W %":  round(prior, 2),
            "Flow_Delta":  round(delta, 2),
            "Rotation":    flow,
        })

    df = pd.DataFrame(rows).sort_values("Flow_Delta", ascending=False)
    return df.reset_index(drop=True)


def compute_breakout_signal(all_data: dict, category_indices: list) -> pd.DataFrame:
    """
    Breakout: Distance from 52W high.
    Uses raw close prices (not % change) for accurate high/low.
    """
    rows = []
    for idx in category_indices:
        name = idx["name"]
        if name not in all_data or all_data[name].empty:
            continue

        df = all_data[name]
        if "close" not in df.columns or len(df) < 2:
            continue

        closes         = df["close"].dropna()
        current        = closes.iloc[-1]
        high_52w       = closes.max()
        low_52w        = closes.min()
        dist_from_high = ((high_52w - current) / high_52w) * 100

        if dist_from_high <= 2:
            signal = "BREAKOUT"
        elif dist_from_high <= 5:
            signal = "Near High"
        elif dist_from_high >= 20:
            signal = "Deep Correction"
        else:
            signal = "Neutral"

        rows.append({
            "Index":       name,
            "Current":     round(current, 2),
            "52W High":    round(high_52w, 2),
            "52W Low":     round(low_52w, 2),
            "% From High": round(dist_from_high, 2),
            "Signal":      signal,
        })

    df = pd.DataFrame(rows).sort_values("% From High")
    return df.reset_index(drop=True)


def compute_weakness_signal(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Weakness: Consecutive red weeks from most recent (left side of matrix).
    """
    rows = []
    # Overall category avg of most recent 4 weeks
    week_cols    = [c for c in matrix.columns if c.startswith("W")]
    recent_cols  = week_cols[:4]
    overall_avg  = matrix[recent_cols].mean(axis=1).mean()

    for idx_name in matrix.index:
        series      = matrix.loc[idx_name]
        week_series = series[[c for c in series.index if c.startswith("W")]].dropna()

        if len(week_series) < 4:
            continue

        # Count consecutive red weeks from most recent (iloc[0] = newest)
        streak = 0
        for val in week_series.values:
            if val < 0:
                streak += 1
            else:
                break

        recent_avg = week_series.iloc[:4].mean()

        if streak >= 3 and recent_avg < overall_avg:
            signal = "HIGH RISK"
        elif streak >= 2:
            signal = "WATCH"
        elif streak == 1:
            signal = "CAUTION"
        else:
            signal = "OK"

        rows.append({
            "Index":      idx_name,
            "Red Streak": streak,
            "Avg 4W %":   round(recent_avg, 2),
            "Weakness":   signal,
        })

    df = pd.DataFrame(rows).sort_values("Red Streak", ascending=False)
    return df.reset_index(drop=True)


def get_summary_stats(matrix: pd.DataFrame) -> pd.DataFrame:
    """Summary stats per index — excludes 52W Return% column."""
    rows = []
    week_cols = [c for c in matrix.columns if c.startswith("W")]
    for idx_name in matrix.index:
        series = matrix.loc[idx_name, week_cols].dropna()
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
