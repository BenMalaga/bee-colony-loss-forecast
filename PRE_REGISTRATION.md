# Pre-Registration — Bee Colony-Loss Forecasting Benchmark

**Status:** 🔒 DRAFT — must be reviewed, then **git-committed with a timestamp BEFORE any
outcome (colony-loss) data is fetched or inspected.** Committing this file before peeking is
what makes the out-of-sample / null claim credible rather than p-hacked (master brief §4).

- Drafted: 2026-06-10
- Locked: 2026-06-10 — committed before any outcome data was fetched (see `git log` for the commit hash + timestamp).
- Author: Ben Malaga
- Repo: `bee-colony-loss-forecast`

---

## 1. Research question

Do the stressor-prevalence signals USDA NASS collects have **predictive (leading-indicator)**
value for **future** U.S. honey-bee colony loss out-of-sample, or do they merely **co-occur**
with concurrent loss and fail to beat a trivial seasonal baseline?

## 2. Design (locked)

- **Data:** USDA NASS "Honey Bee Colonies" survey, state × quarter, 2015–present, via Quick
  Stats 2.0 API. Covariate stack (H3 only) from the public Insolia et al. 2022 dataset.
- **Unit of analysis:** state × quarter.
- **Target Y:** colony **loss percentage** in quarter *t*. Denominator definition is frozen
  here BEFORE inspecting outcomes: `loss% = colonies_lost / max_colonies` for the quarter, using
  the NASS-published fields; if NASS already publishes a loss-percent item, that published item
  is the target and the constructed one is a cross-check. (Record the exact NASS `short_desc`
  used once discovered, without inspecting the *values*.)
- **Temporal split (primary):** train on quarters **through 2022**, hold out **2023–2025**.
  No random splits anywhere. Secondary: expanding-window rolling-origin evaluation.
- **Forecast horizon:** h = 1 quarter (primary); h ∈ {1, 2, 4} (secondary).
- **Predictors:** **lagged only** for all forecasting models — stressor prevalences, loss,
  inventory, added, renovated at t−1, t−2, t−4, plus quarter-of-year and state fixed effects.
  Concurrent (same-quarter) predictors are used **only** in the H2 contrast and are explicitly
  not a forecasting model.

## 3. Baselines (the null floor)

1. Seasonal-naive: `Ŷ_t = Y_{t−4}`.
2. Persistence: `Ŷ_t = Y_{t−1}`.
3. Per-state climatological mean (by quarter-of-year, training period only).

## 4. Models

Lagged ridge, lagged lasso, gradient-boosted trees (HistGradientBoosting and/or XGBoost),
panel autoregression, per-state ARIMA (statsmodels). CPU/laptop only; no deep nets. All
hyperparameters tuned **only on training-period data** via time-series CV; the held-out window
is touched **once**, at the end.

## 5. Metrics & uncertainty

- Primary: **MASE** (scaled by seasonal-naive) on the held-out window, pooled across states.
- Secondary: MAE, RMSE; per-state skill; skill by horizon.
- Uncertainty: block bootstrap over time and across states; report 95% CIs.

## 6. Hypotheses & decision rules (locked thresholds)

- **H1 (primary; expected NULL).** Best lagged model does not beat seasonal-naive.
  - **Confirm null:** pooled OOS **MASE ≥ 0.95** and bootstrap 95% CI includes 1.0.
  - **Refute null (signal exists):** pooled OOS **MASE < 0.90**, 95% CI strictly < 1.0, holding
    across a majority of states and the full held-out window.
  - **Ambiguous (0.90 ≤ MASE < 0.95 or CI straddles):** reported as inconclusive, not spun.
- **H2 (leading-vs-coincident).** Concurrent-predictor model OOS MAE is **≥ 20% lower** than
  the best lagged-model OOS MAE ⇒ the field's signal is coincident, not leading.
- **H3 (secondary).** Insolia covariate stack improves OOS skill by **ΔMASE < 0.05** over the
  stressor-only lagged model ⇒ weather/land cover adds no forecasting value.

## 7. What we will report regardless of outcome

- The honest headline number (likely a null), with CIs, per the decision rules above.
- The leading-vs-coincident decomposition (H2) even if H1 is a clean null.
- Every dropped/suppressed state-quarter, logged and tabulated (no silent scope cuts).
- A COVID-in / COVID-out sensitivity analysis.
- Explicit engagement with Insolia 2022 (incl. Supp. Tables S10–S11), Calovi 2021, Underwood 2024.

## 8. Deviations

Any change after this file is committed is logged in a "Deviations" section with date + reason
and the affected analysis is relabeled **exploratory**.

---

### Lock checklist (do all before fetching outcome data)
- [x] Ben has reviewed and approved this plan. (2026-06-10)
- [x] `git init` + first commit includes this file with the timestamp (commit `43ea36b`, 2026-06-10).
- [x] Only AFTER the commit: ran `src/fetch_nass.py` and built the panel (2026-06-10, after the pre-reg lock at `43ea36b`).

---

## Field mapping (recorded 2026-06-10, post-discovery — pre-authorized by §2; names only)

Discovered via NASS `get_param_values` (field NAMES only; no outcome values inspected).
Operationalized in `src/build_panel.py`. This records the §2-anticipated exact identifiers; it is
not a change to the analysis plan.

- **Primary target Y (loss %):** `HONEY, BEE COLONIES - LOSS, DEADOUT, MEASURED IN PCT OF COLONIES`
- **Denominator:** `HONEY, BEE COLONIES - INVENTORY, MAX, MEASURED IN COLONIES`; constructed
  `loss_pct = 100 * loss_colonies / inv_max` is validated against the published loss% above.
- **Stressor predictors (% of colonies):** Varroa mites; pests excl. varroa (two NASS spellings
  unified into one column); disease; pesticides; other causes; unknown causes.
- **Quarters:** `JAN THRU MAR / APR THRU JUN / JUL THRU SEP / OCT THRU DEC` → Q1–Q4.

---

## Deviations log (§8)

All logged after an internal review of the M3 run. None changes the H1/H2/H3
conclusions.

- **D1 (correction).** H2 was first computed against the `lagged_full` model; §6 specifies the
  *best* lagged model. Corrected to use the best lagged model (gap 2.2%, was 5.4%). Still **NOT
  supported** (bar 20%).
- **D2 (correction).** The §3 baseline #3 (per-state × quarter climatological mean) was omitted
  from the first M3 run; now included (MASE 1.003 — ties seasonal-naive).
- **D3 (transparency).** The eval set excludes 2 of 351 test rows lacking a seasonal-naive value
  (t-4 missing at the 2019 gap / series start); they are the low-loss tail (target mean 1.5 vs
  9.05). All methods are scored on the identical filtered set; effect on MASE is immaterial.
- **D4 (exploratory robustness, not a plan change).** Added in response to the audit, labelled
  exploratory: source-of-skill controls (recalibrated-seasonal-naive, seasonal-lag-only);
  continuous constructed-target sensitivity; a regularized/feature-selecting LassoCV; a lean
  (well-populated) stressor set; and a period-block (quarter) bootstrap + minimum-detectable-effect
  (MDE) to characterise power. These sharpen interpretation; the primary pre-registered test
  (H1 on `hgb_lagged_full`, state-block CI) is unchanged.
- **D5 (citation correction; no analysis change).** §7 above and the writeup originally
  attributed the 2024 successor paper (PMC11132132) as "Underwood, Calovi & Grozinger 2024,
  *Scientific Reports*." Verified from the primary source 2026-06-11: the correct citation is
  **Gray, Goslee, Kammerer & Grozinger 2024, *Journal of Insect Science* 24(3):15,
  doi:10.1093/jisesa/ieae043**. The substantive claim (this group used k-fold CV and declined
  temporal/train-past-test-future validation) is unchanged and correctly quoted. The wrong
  attribution is corrected in docs/paper.md; the locked §7
  line is left intact per the no-silent-edit rule and superseded by this entry.

### Verified conclusion (M3 + audit)
The pre-registered **headline null survives**: reported NASS stressor prevalence adds **no
statistically detectable marginal out-of-sample value** for next-quarter colony loss — robust
across model class (HGB, LassoCV), target definition (integer-published, continuous), and
stressor subset; the sign of the tiny effect is not even consistent. **Scope/power caveat:** MDE
≈ 0.09 MASE under the pre-registered PRIMARY state-block bootstrap (≈0.06 period-block, ≈0.02 in the
LassoCV contrast; see `results/robustness.csv` for both columns) with ~10 effective temporal units,
so this is "no *usable* leading signal at
state-quarter resolution," **not** proof of zero relationship, and says nothing about whether
stressors *cause* loss. The only thing beating seasonal-naive is **mean-reversion recalibration
of that naive forecast**, not recent-loss momentum and not stressors. This extends Insolia et al.
2022: strong in-sample associations do **not** translate into out-of-sample forecasting value.
