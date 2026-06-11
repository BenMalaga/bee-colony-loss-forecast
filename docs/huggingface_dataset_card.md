---
license: cc0-1.0
language:
  - en
pretty_name: U.S. Honey-Bee Colony Loss & Stressor Panel (2015–2025)
tags:
  - honey-bees
  - colony-loss
  - forecasting
  - usda-nass
  - time-series
size_categories:
  - 1K<n<10K
---

# U.S. Honey-Bee Colony Loss & Stressor Panel (2015–2025)

A reproducible state × quarter panel from the USDA NASS *Honey Bee Colonies* survey (Quick Stats
2.0 API; public domain), built for a pre-registered out-of-sample forecasting benchmark.

- **Rows:** 1,776 (unit × year × quarter); **reporting units:** 46 (45 states + a NASS "Other States" aggregate, coded OT); **period:** 2015–2025 (quarters
  JAN–MAR=1 … OCT–DEC=4).
- **Target:** `loss_pct` — quarterly colonies lost ("deadout"), % of max colonies (NASS-published,
  integer-rounded). `loss_pct_constructed` is the continuous cross-check.
- **Predictors:** six stressor prevalences (`str_varroa`, `str_pests_excl_varroa`, `str_disease`,
  `str_pesticides`, `str_other`, `str_unknown`), plus `inv_max`, `added_replaced`, `renovated*`.

See the repository's `results/DATA_DICTIONARY.md` for full column definitions and the
`results/LEADERBOARD.md` for the frozen forecasting benchmark and baseline floor.

**Headline finding from the accompanying benchmark:** reported stressor prevalence adds **no
statistically detectable marginal value** for forecasting next-quarter colony loss; the only skill
over a seasonal-naive baseline is recalibration of that baseline. This concerns the marginal
*forecasting value of a noisy survey measure* and does **not** speak to whether these stressors
*cause* colony loss.

**Provenance / caveats.** Suppressed NASS cells `(D)/(Z)` are missing (stressor columns carry
non-trivial missingness). Non-quarterly NASS rows are excluded by design. Reproduce from source via
the repository's `src/fetch_nass.py` + `src/build_panel.py`.

**License:** CC0-1.0 (source is a U.S. Government work / public domain).

**Citation:** see `CITATION.cff` in the code repository.
