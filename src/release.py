"""Package the released dataset: copy the cleaned panel to results/ (committed) + a data dictionary.

USDA NASS data is a U.S. Government work (public domain), so the derived panel can be redistributed.
The release file is small (state x quarter); the DOI mint (Zenodo/HF) is a separate manual step.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

R = Path("results")
SRC = Path("data/processed/panel.csv")

DICT = """# Released dataset: U.S. honey-bee colony loss & stressor panel (2015-2025)

**File:** `bee_colony_panel.csv`, one row per (state, year, quarter).
**Source:** USDA NASS *Honey Bee Colonies* survey, via the Quick Stats 2.0 API (public domain,
U.S. Government work). Built reproducibly by `src/fetch_nass.py` + `src/build_panel.py`.
**Coverage:** {nrows} rows, {nstates} states, {ymin}-{ymax}. Quarters: JAN-MAR=1 ... OCT-DEC=4.

## Columns
| column | unit | meaning |
|---|---|---|
| state_alpha | n/a | USPS state code |
| year, quarter | n/a | calendar year; quarter 1-4 (the "... THRU ..." reporting period) |
| loss_pct | % of colonies | **target**: colonies lost ("deadout") that quarter (NASS-published, integer-rounded) |
| loss_pct_constructed | % | continuous cross-check = 100 × loss_colonies / inv_max |
| loss_colonies | colonies | colonies lost that quarter |
| inv_max | colonies | maximum colonies during the quarter (the loss denominator) |
| added_replaced | colonies | colonies added & replaced |
| renovated, renovated_pct | colonies, % | colonies renovated |
| str_varroa | % of colonies | affected by Varroa mites |
| str_pests_excl_varroa | % | affected by pests excl. Varroa (two NASS spellings unified) |
| str_disease | % | affected by disease |
| str_pesticides | % | affected by pesticides |
| str_other | % | affected by other causes |
| str_unknown | % | affected by unknown causes |

## Notes
- Suppressed NASS cells `(D)/(Z)` are NaN. Stressor columns have non-trivial missingness
  (disease/pesticides/unknown most affected); the full table is in `results/missingness.csv`.
- Non-quarterly NASS rows (FIRST-OF-quarter inventory, marketing-year) are excluded by design.
- License: public domain (source); released under CC0 to match.
"""


def main():
    df = pd.read_csv(SRC)
    df.to_csv(R / "bee_colony_panel.csv", index=False)
    (R / "DATA_DICTIONARY.md").write_text(DICT.format(
        nrows=len(df), nstates=df["state_alpha"].nunique(),
        ymin=int(df["year"].min()), ymax=int(df["year"].max())))
    print(f"Released {len(df)} rows -> results/bee_colony_panel.csv + results/DATA_DICTIONARY.md")


if __name__ == "__main__":
    main()
