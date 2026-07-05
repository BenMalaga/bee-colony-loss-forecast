# Released dataset: U.S. honey-bee colony loss & stressor panel (2015–2025)

**File:** `bee_colony_panel.csv`, one row per (state, year, quarter).
**Source:** USDA NASS *Honey Bee Colonies* survey, via the Quick Stats 2.0 API (public domain,
U.S. Government work). Built reproducibly by `src/fetch_nass.py` + `src/build_panel.py`.
**Coverage:** 1776 rows, 46 reporting units (45 states + a NASS "Other States" aggregate, coded OT), 2015–2025. Quarters: JAN–MAR=1 … OCT–DEC=4.

## Columns
| column | unit | meaning |
|---|---|---|
| state_alpha | n/a | USPS state code |
| year, quarter | n/a | calendar year; quarter 1–4 (the "… THRU …" reporting period) |
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
