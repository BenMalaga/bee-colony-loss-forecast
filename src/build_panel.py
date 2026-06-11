"""Build the tidy state x quarter modeling panel from raw NASS pulls.

Run AFTER `python -m src.fetch_nass --confirm-prereg-locked`.

Field mapping is LOCKED from the discovered NASS short_desc / reference_period_desc values
(names only -- see data/raw/bee_colony_short_descs.txt and PRE_REGISTRATION.md "Field mapping").
Outputs:
  data/processed/panel_long.csv  -- tidy long (one row per state x period x series)
  data/processed/panel.csv       -- wide quarterly modeling panel (state x year x quarter)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
PROC = Path("data/processed")

# --- Locked field mapping: NASS short_desc -> tidy column ------------------------------------
TARGET = "HONEY, BEE COLONIES - LOSS, DEADOUT, MEASURED IN PCT OF COLONIES"  # primary target Y
SERIES = {
    "loss_pct":       "HONEY, BEE COLONIES - LOSS, DEADOUT, MEASURED IN PCT OF COLONIES",
    "loss_colonies":  "HONEY, BEE COLONIES - LOSS, DEADOUT, MEASURED IN COLONIES",
    "ccd_colonies":   "HONEY, BEE COLONIES - LOSS, COLONY COLLAPSE DISORDER, MEASURED IN COLONIES",
    "inv_max":        "HONEY, BEE COLONIES - INVENTORY, MAX, MEASURED IN COLONIES",
    "inv":            "HONEY, BEE COLONIES - INVENTORY, MEASURED IN COLONIES",
    "added_replaced": "HONEY, BEE COLONIES - ADDED & REPLACED, MEASURED IN COLONIES",
    "renovated":      "HONEY, BEE COLONIES, RENOVATED - INVENTORY, MEASURED IN COLONIES",
    "renovated_pct":  "HONEY, BEE COLONIES, RENOVATED - INVENTORY, MEASURED IN PCT OF COLONIES",
    "str_varroa":     "HONEY, BEE COLONIES, AFFECTED BY VARROA MITES - INVENTORY, MEASURED IN PCT OF COLONIES",
    "str_disease":    "HONEY, BEE COLONIES, AFFECTED BY DISEASE - INVENTORY, MEASURED IN PCT OF COLONIES",
    "str_pesticides": "HONEY, BEE COLONIES, AFFECTED BY PESTICIDES - INVENTORY, MEASURED IN PCT OF COLONIES",
    "str_other":      "HONEY, BEE COLONIES, AFFECTED BY OTHER CAUSES - INVENTORY, MEASURED IN PCT OF COLONIES",
    "str_unknown":    "HONEY, BEE COLONIES, AFFECTED BY UNKNOWN CAUSES - INVENTORY, MEASURED IN PCT OF COLONIES",
}
# "Pests excl. varroa" appears under TWO NASS spellings (a string change over time); unify both.
PESTS_COL = "str_pests_excl_varroa"
PESTS_VARIANTS = {
    "HONEY, BEE COLONIES, AFFECTED BY PESTS ((EXCL VARROA MITES)) - INVENTORY, MEASURED IN PCT OF COLONIES",
    "HONEY, BEE COLONIES, AFFECTED BY PESTS (EXCL VARROA MITES) - INVENTORY, MEASURED IN PCT OF COLONIES",
}

# reference_period_desc -> quarter. The quarterly "during the quarter" measures use THRU labels.
QUARTER = {"JAN THRU MAR": 1, "APR THRU JUN": 2, "JUL THRU SEP": 3, "OCT THRU DEC": 4}
# --------------------------------------------------------------------------------------------


def load_raw() -> pd.DataFrame:
    frames = []
    for f in sorted(RAW.glob("nass_honey_*.json")):
        data = json.loads(f.read_text()).get("data", [])
        if data:
            frames.append(pd.DataFrame(data))
    if not frames:
        raise SystemExit("No raw NASS files. Run: python -m src.fetch_nass --confirm-prereg-locked")
    return pd.concat(frames, ignore_index=True)


def to_long(df: pd.DataFrame) -> pd.DataFrame:
    keep = df[df["short_desc"].str.contains("BEE COLONIES", case=False, na=False)].copy()
    # suppressed cells like (D)/(Z) -> NaN
    keep["value"] = pd.to_numeric(
        keep["Value"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    keep.loc[keep["short_desc"].isin(PESTS_VARIANTS), "short_desc"] = PESTS_COL
    cols = ["state_alpha", "state_fips_code", "year", "reference_period_desc",
            "short_desc", "value", "unit_desc"]
    return keep[[c for c in cols if c in keep.columns]].reset_index(drop=True)


def to_panel(long: pd.DataFrame) -> pd.DataFrame:
    name = {v: k for k, v in SERIES.items()}
    name[PESTS_COL] = PESTS_COL
    long = long.copy()
    long["var"] = long["short_desc"].map(name)
    long["quarter"] = long["reference_period_desc"].map(QUARTER)

    # honest logging -- no silent scope cuts (master brief §4)
    unmapped = long.loc[long["var"].isna(), "short_desc"].value_counts()
    if len(unmapped):
        print("[log] short_descs not in mapping (excluded from panel):")
        for s, n in unmapped.items():
            print(f"        {n:6d}  {s}")
    dropped_q = long.loc[long["var"].notna() & long["quarter"].isna(),
                         "reference_period_desc"].value_counts()
    if len(dropped_q):
        print("[log] mapped series on non-quarterly periods (excluded from quarterly panel):")
        for p, n in dropped_q.items():
            print(f"        {n:6d}  {p}")

    keep = long.dropna(subset=["var", "quarter"]).copy()
    keep["quarter"] = keep["quarter"].astype(int)
    wide = (keep.pivot_table(index=["state_alpha", "year", "quarter"],
                             columns="var", values="value", aggfunc="first")
                .reset_index()
                .sort_values(["state_alpha", "year", "quarter"]))
    # constructed loss% cross-check vs the published target (validate they agree)
    if {"loss_colonies", "inv_max"}.issubset(wide.columns):
        wide["loss_pct_constructed"] = 100.0 * wide["loss_colonies"] / wide["inv_max"]
    return wide


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    long = to_long(load_raw())
    long.to_csv(PROC / "panel_long.csv", index=False)
    panel = to_panel(long)
    panel.to_csv(PROC / "panel.csv", index=False)
    print(
        f"Wrote {PROC/'panel_long.csv'} ({len(long)} rows) and {PROC/'panel.csv'} "
        f"({len(panel)} state-quarter rows, {panel['state_alpha'].nunique()} states, "
        f"{int(panel['year'].min())}-{int(panel['year'].max())})."
    )


if __name__ == "__main__":
    main()
