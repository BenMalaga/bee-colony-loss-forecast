"""Shared, gap-safe feature construction for the colony-loss forecasting benchmark.

Lags are built by merging on (state, t-lag) so quarter gaps (e.g. the 2019 shutdown gap)
produce NaN rather than silently shifting an adjacent quarter into the wrong slot.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

TARGET = "loss_pct"
STRESSORS = ["str_varroa", "str_pests_excl_varroa", "str_disease",
             "str_pesticides", "str_other", "str_unknown"]
LEVELS = [TARGET, "inv_max", "added_replaced", "renovated_pct"] + STRESSORS
LAGS = [1, 4]

# The freshly-fetched panel (data/processed/) is gitignored; the byte-identical
# released panel is committed so the whole pipeline reproduces offline with no API key.
DEFAULT_PANEL = "data/processed/panel.csv"
RELEASED_PANEL = "results/bee_colony_panel.csv"


def resolve_panel(path: str | None = None) -> str:
    """Pick the panel to load: explicit arg / $BEE_PANEL / fresh-fetch / committed release."""
    for candidate in (path, os.environ.get("BEE_PANEL"), DEFAULT_PANEL, RELEASED_PANEL):
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        f"No panel found. Looked for {DEFAULT_PANEL} (run src.fetch_nass + src.build_panel) "
        f"and the committed {RELEASED_PANEL}.")


def load_panel(path: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(resolve_panel(path))
    df["t"] = df["year"] * 4 + (df["quarter"] - 1)          # gap-aware quarter index
    return df.sort_values(["state_alpha", "t"]).reset_index(drop=True)


def add_lags(df: pd.DataFrame, levels=LEVELS, lags=LAGS) -> pd.DataFrame:
    out = df.copy()
    for lag in lags:
        src = df[["state_alpha", "t"] + levels].copy()
        src["t"] = src["t"] + lag
        src = src.rename(columns={c: f"{c}_lag{lag}" for c in levels})
        out = out.merge(src, on=["state_alpha", "t"], how="left")
    out["snaive"] = out[f"{TARGET}_lag4"]      # seasonal-naive forecast
    out["persist"] = out[f"{TARGET}_lag1"]     # persistence forecast
    return out


def feature_sets() -> dict[str, list[str]]:
    """The three pre-registered feature sets for the decomposition and H2."""
    loss_only = [f"{TARGET}_lag1", f"{TARGET}_lag4", "quarter"]
    lagged_full = (
        loss_only
        + [f"{s}_lag1" for s in STRESSORS]
        + [f"{s}_lag4" for s in STRESSORS]
        + ["inv_max_lag1", "added_replaced_lag1", "renovated_pct_lag1"]
    )
    concurrent = STRESSORS + [f"{TARGET}_lag1", f"{TARGET}_lag4", "quarter"]  # same-quarter stressors (H2)
    return {"loss_only": loss_only, "lagged_full": lagged_full, "concurrent": concurrent}
