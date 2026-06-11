"""M2 pilot: does lagged NASS stressor data forecast next-quarter colony loss out-of-sample?

Smallest end-to-end slice of the pre-registered design (PRE_REGISTRATION.md):
  - target: loss_pct at quarter t (published NASS LOSS, DEADOUT, PCT OF COLONIES)
  - temporal split: train year<=2022, test year>=2023 (NO random splits)
  - baselines: seasonal-naive (loss_{t-4}), persistence (loss_{t-1})
  - lagged model: HistGradientBoosting on t-1 & t-4 features (handles NaN natively)
  - H2 preview: a CONCURRENT-stressor model (same-quarter str_*) vs the lagged model,
    both scored out-of-sample -- quantifies leading-vs-coincident.

Primary readout: MASE = MAE(model) / MAE(seasonal-naive) on the held-out set. <1 beats naive.
This is a PILOT (signal/pipeline check), not the full rigorous run (rolling-origin, bootstrap
CIs, all models, per-state) -- that comes after the pilot review gate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

PANEL = "data/processed/panel.csv"
TARGET = "loss_pct"
STRESSORS = ["str_varroa", "str_pests_excl_varroa", "str_disease",
             "str_pesticides", "str_other", "str_unknown"]
LEVELS = [TARGET, "inv_max", "added_replaced", "renovated_pct"] + STRESSORS
LAGS = [1, 4]
SEED = 0


def mae(y, yhat) -> float:
    m = ~(pd.isna(y) | pd.isna(yhat))
    return float(np.mean(np.abs(np.asarray(y)[m] - np.asarray(yhat)[m])))


def build() -> pd.DataFrame:
    df = pd.read_csv(PANEL)
    df["t"] = df["year"] * 4 + (df["quarter"] - 1)          # gap-aware quarter index
    df = df.sort_values(["state_alpha", "t"]).reset_index(drop=True)
    base = df.copy()
    for lag in LAGS:                                          # lag via (state, t-lag) merge -> gap-safe
        src = df[["state_alpha", "t"] + LEVELS].copy()
        src["t"] = src["t"] + lag
        src = src.rename(columns={c: f"{c}_lag{lag}" for c in LEVELS})
        base = base.merge(src, on=["state_alpha", "t"], how="left")
    base["snaive"] = base[f"{TARGET}_lag4"]
    base["persist"] = base[f"{TARGET}_lag1"]
    return base


def main() -> None:
    base = build()
    lagged_feats = [f"{c}_lag{l}" for l in LAGS for c in LEVELS] + ["quarter"]
    concurrent_feats = STRESSORS + [f"{TARGET}_lag1", f"{TARGET}_lag4", "quarter"]  # same-quarter stressors

    train = base[base["year"] <= 2022].dropna(subset=[TARGET])
    test = base[(base["year"] >= 2023)].dropna(subset=[TARGET, "snaive"]).copy()   # MASE needs snaive

    def fit_predict(feats):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05,
                                          max_depth=3, random_state=SEED)
        m.fit(train[feats], train[TARGET])
        return m.predict(test[feats])

    test["lagged_model"] = fit_predict(lagged_feats)
    test["concurrent_model"] = fit_predict(concurrent_feats)

    methods = {
        "seasonal_naive (loss t-4)": test["snaive"],
        "persistence   (loss t-1)": test["persist"],
        "lagged_model  (HGB t-1,t-4)": test["lagged_model"],
        "concurrent_model (HGB, same-qtr stressors)": test["concurrent_model"],
    }
    mae_sn = mae(test[TARGET], test["snaive"])

    rows = []
    print(f"\nTrain: {len(train)} rows (<=2022)   Test: {len(test)} rows (>=2023, snaive available)")
    print(f"Test years: {sorted(test['year'].unique().tolist())}   "
          f"target mean={test[TARGET].mean():.1f}%  sd={test[TARGET].std():.1f}\n")
    print(f"{'method':<44}{'MAE':>8}{'MASE':>8}")
    print("-" * 60)
    for name, pred in methods.items():
        m = mae(test[TARGET], pred)
        rows.append({"method": name, "MAE": round(m, 3), "MASE_vs_snaive": round(m / mae_sn, 3)})
        print(f"{name:<44}{m:>8.2f}{m/mae_sn:>8.3f}")
    print("-" * 60)
    print("MASE < 1.0 beats seasonal-naive. H1 (pre-registered) expects the lagged model NOT to.")
    print("H2 preview: concurrent_model MAE vs lagged_model MAE -> leading-vs-coincident gap.")

    out = pd.DataFrame(rows)
    out.to_csv("results/pilot_metrics.csv", index=False)
    print("\nWrote results/pilot_metrics.csv")


if __name__ == "__main__":
    main()
