# Colony-loss forecasting benchmark: leaderboard

**Task.** Forecast next-quarter state-level honey-bee colony **loss %** (USDA NASS) out-of-sample.
**Frozen split (pre-registered).** Train on quarters ≤ 2022; evaluate on the held-out 2023–2025
window (n=349 state-quarters, 45 states). No random splits. Predictors must be **lagged** (no
same-quarter leakage). **Metric:** MASE = MAE / MAE(seasonal-naive); **< 1 beats the baseline.**
Report a state-block bootstrap 95% CI.

**Reference floor.** The bar is the *recalibrated* seasonal-naive, not the raw naive. Anything above
that line is the real target to beat. Note the minimum detectable effect is ≈0.09 MASE under the
pre-registered primary (state-block) bootstrap (≈0.06 period-block), so the ~0.025 MASE edge of
the best lagged model (0.903) over the recalibrated naive (0.928) is itself within the noise floor.

| rank | method | features | MASE | 95% CI | notes |
|---|---|---|---|---|---|
| n/a | seasonal-naive | loss_{t−4} | 1.000 | n/a | baseline (denominator) |
| n/a | persistence | loss_{t−1} | 1.230 | [1.12, 1.35] | worse; loss is seasonal |
| n/a | climatological mean | state×qtr train mean | 1.003 | [0.90, 1.13] | ties naive |
| 3 | recalibrated naive | OLS on loss_{t−4} | 0.928 | [0.86, 1.02] | mean-reversion |
| 2 | HGB, seasonal-lag only | loss_{t−4}, qtr | 0.908 | [0.84, 0.99] | ≈ loss-only |
| **1** | **HGB, loss-only** | loss lags + qtr | **0.903** | **[0.83, 0.99]** | best lagged model |
| n/a | HGB, loss + **stressors** | + 6 stressor lags | 0.934 | [0.84, 1.04] | stressors add nothing |
| n/a | Ridge, loss + stressors | + 6 stressor lags | 0.945 | [0.88, 1.03] | (same story) |
| (oracle*) | HGB, concurrent stressors | same-quarter str | 0.883 | [0.80, 0.97] | *not a forecast (peeks)* |

\* `concurrent` uses same-quarter stressor values and is **not** a valid forecaster; shown only for
the leading-vs-coincident (H2) contrast.

**Submit.** Add a forecaster that consumes only lagged features, score it with `src/analyze.py`'s
`boot_mase_ci` on the frozen test set, and open a PR appending your row (method, feature set, MASE,
CI, seed, code link). The standing challenge: **beat 0.903 using information the loss lags don't
already contain.** In particular, show me any stressor or covariate set that adds detectable value.

Reproduce the floor: `python -m src.analyze` (writes `results/full_metrics.csv`).
