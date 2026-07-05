# bee-colony-loss-forecast

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20649336.svg)](https://doi.org/10.5281/zenodo.20649336)
&nbsp;[![License: CC0-1.0](https://img.shields.io/badge/data-CC0--1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
&nbsp;[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)

**Does bee-colony monitoring *forecast* loss, or does it only *explain* it?**

This is a pre-registered, out-of-sample forecasting benchmark for U.S. honey-bee colony loss, built
entirely on public USDA NASS data. The existing literature models colony loss explanatorily: it fits
in-sample regressions with same-quarter "stressor" predictors and reports strong associations
(Insolia et al. 2022, R²≈0.60). I wanted to know something the explanatory fit can't tell you, which
is whether those same stressor signals let you predict *next* quarter's loss before it happens. They
don't.

## Headline result

> Reported NASS stressor prevalence (Varroa, disease, pesticides, and so on) adds no
> statistically detectable value when you use it to forecast next-quarter colony loss. That holds
> across gradient-boosting and LASSO, across the integer and continuous versions of the target, and
> across the full and lean stressor sets: the change in skill from adding stressors has a 95% CI that
> spans zero, and the sign isn't even stable. The one thing that does beat the seasonal-naive
> baseline is a recalibration of that baseline, not recent loss and not the stressors.

So this is a clean "explains but does not predict" result. A strong in-sample R² simply doesn't
survive an honest out-of-sample test.

![source of skill](results/figures/fig1_source_of_skill.png)

| model (test 2023-25, n=349) | MASE vs seasonal-naive | 95% CI |
|---|---|---|
| loss-only (HGB) | **0.903** | [0.83, 0.99] |
| loss **+ all stressors** | 0.934 | [0.84, 1.04] |
| seasonal-naive | 1.000 | reference |

A couple of honest caveats, both spelled out in the paper. The test is underpowered for small
effects (pre-registered primary state-block MDE ≈ 0.09 MASE, ≈0.06 period-block, on the order of ten
effective temporal units), so read this as "no *usable* signal" rather than proof of exactly zero.
And it's about the marginal forecasting value of a noisy survey measure, not about whether the
stressors *cause* colony loss. Those are different questions and this design only speaks to the first.

> One thing worth stating plainly, because the headlines get it wrong: globally, *managed*
> honey-bee colonies are rising, not collapsing. The real problem is the high annual U.S.
> colony loss and turnover, and that is what this targets.

## Artifacts
- **Released dataset:** [`results/bee_colony_panel.csv`](results/bee_colony_panel.csv) (state×quarter, 2015-2025) plus a [data dictionary](results/DATA_DICTIONARY.md). CC0, since NASS is public domain. Archived at Zenodo: [doi:10.5281/zenodo.20649336](https://doi.org/10.5281/zenodo.20649336).
- **Benchmark + leaderboard:** [`results/LEADERBOARD.md`](results/LEADERBOARD.md), with the frozen splits, the baseline floor, and submission rules.
- **Paper draft:** [`docs/paper.md`](docs/paper.md). Pre-registration: [`PRE_REGISTRATION.md`](PRE_REGISTRATION.md), with the deviations logged.
- **Figures:** [`results/figures/`](results/figures).

## Reproduce
```bash
pip install -r requirements.txt
export QUICKSTATS_API_KEY=...           # free: https://quickstats.nass.usda.gov/api
python -m src.fetch_nass --confirm-prereg-locked   # pull 2015-2025 NASS data
python -m src.build_panel                          # build the state×quarter panel
python -m src.analyze                              # primary results + bootstrap CIs
python -m src.robustness                           # continuous target, LassoCV, power/MDE
python -m src.figures                              # regenerate figures
```

For the locked analysis plan see [`PRE_REGISTRATION.md`](PRE_REGISTRATION.md); for fetch details see
[`data/README.md`](data/README.md); and [`docs/paper.md`](docs/paper.md) has the full writeup and
references.

## Status
The result is verified and reproducible. The derived dataset is archived at Zenodo
([doi:10.5281/zenodo.20649336](https://doi.org/10.5281/zenodo.20649336)).
