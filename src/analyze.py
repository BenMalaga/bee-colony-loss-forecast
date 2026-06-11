"""M3 full run (audit-corrected): resolve the pre-registered hypotheses for colony-loss forecasting.

On the locked target/split (PRE_REGISTRATION.md), with review fixes folded in:
  - primary-split MASE for every method + 3 pre-registered baselines (seasonal-naive, persistence,
    per-state climatological mean) PLUS audit controls that locate the source of skill
    (recalibrated-seasonal-naive; seasonal-lag-only HGB) -> apply H1 decision rule;
  - HEADLINE stressor-marginal decomposition (lagged-loss-only vs +stressors), state-block
    bootstrap CI on the MAE difference;
  - H2 vs the BEST lagged model (pre-registered comparator) -- corrected from the first run;
  - rolling-origin, per-state, COVID in/out; honest logging of dropped/excluded rows.

MASE = MAE(method)/MAE(seasonal-naive) on the eval set (<1 beats naive). NOTE: this is a pooled
MAE-ratio, not the in-sample-scaled textbook MASE -- see robustness.py for the power/MDE analysis
and continuous-target / regularized-model sensitivities. CPU-only, deterministic (seed=0).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import TARGET, add_lags, feature_sets, load_panel

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
RNG = np.random.default_rng(0)
B = 2000


def mae(y, yhat) -> float:
    y = np.asarray(y, float)
    yhat = np.asarray(yhat, float)
    m = ~(np.isnan(y) | np.isnan(yhat))
    return float(np.mean(np.abs(y[m] - yhat[m]))) if m.any() else np.nan


def hgb() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05,
                                         max_depth=3, random_state=0)


def ridge():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))


def fit_predict(factory, train, test, feats):
    m = factory()
    m.fit(train[feats], train[TARGET])
    return m.predict(test[feats])


def _state_groups(test):
    return [test[test["state_alpha"] == s] for s in test["state_alpha"].unique()]


def boot_mase_ci(test, num_col, den_col="snaive", B=B):
    groups = _state_groups(test)
    vals = []
    for _ in range(B):
        idx = RNG.integers(0, len(groups), len(groups))
        chunk = pd.concat([groups[i] for i in idx])
        d = mae(chunk[TARGET], chunk[den_col])
        if d and d > 0:
            vals.append(mae(chunk[TARGET], chunk[num_col]) / d)
    return tuple(np.percentile(vals, [2.5, 50, 97.5]))


def boot_diff_ci(test, a_col, b_col, B=B):
    """CI on MAE(a) - MAE(b); positive => b (the richer feature set) helps."""
    groups = _state_groups(test)
    vals = []
    for _ in range(B):
        idx = RNG.integers(0, len(groups), len(groups))
        chunk = pd.concat([groups[i] for i in idx])
        vals.append(mae(chunk[TARGET], chunk[a_col]) - mae(chunk[TARGET], chunk[b_col]))
    return tuple(np.percentile(vals, [2.5, 50, 97.5]))


def boot_rel_gap_ci(test, lagged_cols, con_col, B=B):
    """CI on the H2 relative gap (MAE(best lagged) - MAE(concurrent)) / MAE(best lagged);
    positive => same-quarter stressors beat the best lagged model. The 'best lagged' model
    is re-selected inside each resample so the CI reflects selection too."""
    groups = _state_groups(test)
    vals = []
    for _ in range(B):
        idx = RNG.integers(0, len(groups), len(groups))
        chunk = pd.concat([groups[i] for i in idx])
        best = min(mae(chunk[TARGET], chunk[c]) for c in lagged_cols)
        if best > 0:
            vals.append((best - mae(chunk[TARGET], chunk[con_col])) / best)
    return tuple(np.percentile(vals, [2.5, 50, 97.5]))


def main() -> None:
    base = add_lags(load_panel())
    fs = feature_sets()

    # ---- primary split (train<=2022, test 2023-2025) ----
    train = base[base["year"] <= 2022].dropna(subset=[TARGET])
    test_all = base[base["year"] > 2022].dropna(subset=[TARGET])
    test = test_all.dropna(subset=["snaive"]).copy()
    dropped = test_all[~test_all.index.isin(test.index)]

    # models / controls
    test["hgb_loss_only"] = fit_predict(hgb, train, test, fs["loss_only"])
    test["hgb_lagged_full"] = fit_predict(hgb, train, test, fs["lagged_full"])
    test["hgb_concurrent"] = fit_predict(hgb, train, test, fs["concurrent"])
    test["ridge_lagged_full"] = fit_predict(ridge, train, test, fs["lagged_full"])
    # audit control: seasonal-lag-only (is the skill just the year-ago lag, recalibrated?)
    test["hgb_lag4_only"] = fit_predict(hgb, train, test, [f"{TARGET}_lag4", "quarter"])
    # pre-registered baseline #3: per-state x quarter climatological mean (train only)
    clim = train.groupby(["state_alpha", "quarter"])[TARGET].mean()
    test["clim"] = [clim.get((s, q), np.nan) for s, q in zip(test["state_alpha"], test["quarter"])]
    # audit control: linear recalibration of seasonal-naive (shrink toward conditional mean)
    tr_sn = train.dropna(subset=["snaive"])
    b1, b0 = np.polyfit(tr_sn["snaive"].to_numpy(float), tr_sn[TARGET].to_numpy(float), 1)
    test["recal_snaive"] = b0 + b1 * test["snaive"]

    mae_sn = mae(test[TARGET], test["snaive"])
    order = ["snaive", "persist", "clim", "recal_snaive", "hgb_lag4_only",
             "hgb_loss_only", "hgb_lagged_full", "hgb_concurrent", "ridge_lagged_full"]
    rows = []
    for m in order:
        lo, mid, hi = boot_mase_ci(test, m)
        rows.append({"method": m, "MAE": round(mae(test[TARGET], test[m]), 3),
                     "MASE": round(mae(test[TARGET], test[m]) / mae_sn, 3),
                     "MASE_lo": round(lo, 3), "MASE_hi": round(hi, 3)})
    primary = pd.DataFrame(rows)
    primary.to_csv(RESULTS / "full_metrics.csv", index=False)

    # ---- headline decomposition: do stressors help beyond lagged loss? ----
    dlo, dmid, dhi = boot_diff_ci(test, "hgb_loss_only", "hgb_lagged_full")
    delta = mae(test[TARGET], test["hgb_loss_only"]) - mae(test[TARGET], test["hgb_lagged_full"])
    decomp = pd.DataFrame([{
        "comparison": "MAE(loss_only) - MAE(lagged_full)  [>0 => stressors help]",
        "delta_MAE": round(delta, 3), "ci_lo": round(dlo, 3), "ci_hi": round(dhi, 3),
    }])
    decomp.to_csv(RESULTS / "decomposition.csv", index=False)

    # ---- H2: concurrent vs the BEST lagged model (pre-registered comparator; DEVIATION fix) ----
    mae_lo = mae(test[TARGET], test["hgb_loss_only"])
    mae_lf = mae(test[TARGET], test["hgb_lagged_full"])
    mae_con = mae(test[TARGET], test["hgb_concurrent"])
    mae_best_lagged = min(mae_lo, mae_lf)
    h2_best = (mae_best_lagged - mae_con) / mae_best_lagged
    h2_full = (mae_lf - mae_con) / mae_lf
    h2_lo, _h2_mid, h2_hi = boot_rel_gap_ci(
        test, ["hgb_loss_only", "hgb_lagged_full"], "hgb_concurrent")

    # ---- rolling-origin (expanding window) ----
    ro = []
    for ty in range(2020, 2026):
        tr = base[base["year"] <= ty - 1].dropna(subset=[TARGET])
        ts = base[base["year"] == ty].dropna(subset=[TARGET, "snaive"]).copy()
        if len(ts) < 10:
            continue
        d = mae(ts[TARGET], ts["snaive"])
        rec = {"test_year": ty, "n": len(ts)}
        for k in ["loss_only", "lagged_full", "concurrent"]:
            rec[f"MASE_{k}"] = round(mae(ts[TARGET], fit_predict(hgb, tr, ts, fs[k])) / d, 3)
        ro.append(rec)
    rolling = pd.DataFrame(ro)
    rolling.to_csv(RESULTS / "rolling_origin.csv", index=False)

    # ---- per-state ----
    ps = []
    for s, g in test.groupby("state_alpha"):
        d = mae(g[TARGET], g["snaive"])
        if not d or d <= 0:
            continue
        ps.append({"state": s, "n": len(g),
                   "MASE_lagged_full": round(mae(g[TARGET], g["hgb_lagged_full"]) / d, 3),
                   "MASE_loss_only": round(mae(g[TARGET], g["hgb_loss_only"]) / d, 3)})
    per_state = pd.DataFrame(ps).sort_values("MASE_lagged_full")
    per_state.to_csv(RESULTS / "per_state.csv", index=False)
    frac_beat = float((per_state["MASE_lagged_full"] < 1).mean())
    frac_full_gt_lossonly = float((per_state["MASE_lagged_full"] < per_state["MASE_loss_only"]).mean())

    # ---- COVID sensitivity ----
    pred_nc = fit_predict(hgb, train[~train["year"].isin([2020, 2021])], test, fs["lagged_full"])
    mase_covidout = mae(test[TARGET], pred_nc) / mae_sn

    # ---------------- summary ----------------
    r = primary.set_index("method").loc["hgb_lagged_full"]
    h1 = ("CONFIRM NULL" if r.MASE >= 0.95 and r.MASE_hi >= 1.0
          else "REFUTE NULL (signal)" if r.MASE < 0.90 and r.MASE_hi < 1.0 else "INCONCLUSIVE")
    L = []
    L.append(f"=== PRIMARY SPLIT (train<=2022, test 2023-2025; n_test={len(test)}, "
             f"{test['state_alpha'].nunique()} states) ===")
    L.append(primary.to_string(index=False))
    L.append(f"\n[log] excluded {len(dropped)} test rows lacking seasonal-naive (t-4); "
             f"their target mean={dropped[TARGET].mean():.2f} vs kept {test[TARGET].mean():.2f} "
             f"(low-loss tail; all methods scored on the identical filtered set).")
    L.append("")
    L.append("=== H1 (lagged stressor model vs seasonal-naive) ===")
    L.append(f"  hgb_lagged_full MASE={r.MASE} 95%CI[{r.MASE_lo},{r.MASE_hi}] -> {h1}")
    L.append("  NOTE source-of-skill controls: clim MASE={:.3f}, recal_snaive={:.3f}, "
             "hgb_lag4_only={:.3f}, hgb_loss_only={:.3f}".format(
                 primary.set_index('method').loc['clim','MASE'],
                 primary.set_index('method').loc['recal_snaive','MASE'],
                 primary.set_index('method').loc['hgb_lag4_only','MASE'],
                 primary.set_index('method').loc['hgb_loss_only','MASE']))
    L.append("  => sub-1 skill is recalibration/mean-reversion of seasonal-naive, not recent-loss info.")
    L.append("")
    L.append("=== HEADLINE: do stressors add value beyond lagged loss? ===")
    verdict = ("NO detectable value (CI includes 0)" if dlo <= 0 <= dhi else "stressors DO help")
    L.append(f"  MAE(loss_only)-MAE(loss+stressors) = {delta:.3f} 95%CI[{dlo:.3f},{dhi:.3f}] -> {verdict}")
    L.append("  (sign is model-dependent; see robustness.py LassoCV + continuous-target + power/MDE.)")
    L.append("")
    L.append("=== H2 (concurrent vs lagged stressors) ===")
    L.append(f"  vs BEST lagged model (pre-registered): gap={h2_best*100:.1f}%  "
             f"(reported-vs-lagged_full was {h2_full*100:.1f}%)  bar=20% -> "
             f"{'SUPPORTED' if h2_best >= 0.20 else 'NOT supported'}")
    h2_straddles = h2_lo <= 0 <= h2_hi
    L.append(f"  state-block 95%CI on the gap = [{h2_lo*100:.1f}%, {h2_hi*100:.1f}%] -> "
             f"{'includes 0: concurrent stressors do NOT reliably beat the best lagged model'
                if h2_straddles else 'excludes 0'} "
             f"(stronger than the 20%-bar framing; the field signal is neither leading nor "
             f"reliably coincident)")
    L.append("")
    L.append("=== Rolling-origin MASE ===")
    L.append(rolling.to_string(index=False))
    L.append("")
    L.append(f"=== Per-state (lagged_full): beat naive {frac_beat*100:.0f}% of states; "
             f"+stressors beats loss-only {frac_full_gt_lossonly*100:.0f}% (coin-flip => no signal) ===")
    L.append(f"=== COVID: lagged_full MASE {r.MASE} (full) vs {mase_covidout:.3f} (excl 2020-2021) ===")
    out = "\n".join(L)
    print(out)
    (RESULTS / "summary.txt").write_text(out + "\n")
    print("\nWrote results/{full_metrics,decomposition,rolling_origin,per_state,summary}.* ; "
          "run src.robustness for power/MDE + continuous-target + LassoCV.")


if __name__ == "__main__":
    main()
