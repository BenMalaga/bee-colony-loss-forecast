"""Per-column missingness for the released panel (the table referenced by the paper).

NASS suppresses cells as (D)/(Z); those become NaN in the panel. Stressor columns carry the most.
Writes results/missingness.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .features import resolve_panel

R = Path("results")


def main() -> None:
    df = pd.read_csv(resolve_panel())
    keys = {"state_alpha", "year", "quarter"}
    rows = [{"column": c, "n": len(df), "n_missing": int(df[c].isna().sum()),
             "pct_missing": round(100 * df[c].isna().mean(), 1)}
            for c in df.columns if c not in keys]
    out = pd.DataFrame(rows).sort_values("pct_missing", ascending=False)
    out.to_csv(R / "missingness.csv", index=False)
    print(out.to_string(index=False))
    print("\nWrote results/missingness.csv")


if __name__ == "__main__":
    main()
