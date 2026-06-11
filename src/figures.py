"""Generate paper figures from the committed results CSVs (no re-analysis needed).

  results/figures/fig1_source_of_skill.png  -- MASE +/- 95% CI per method (the bar is naive=1.0)
  results/figures/fig2_decomposition.png    -- stressor delta_MAE +/- CI across target x model (spans 0)
  results/figures/fig3_rolling_origin.png   -- MASE by test year for loss-only / +stressors / concurrent
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

R = Path("results")
FIG = R / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def _parse_ci(s: str):
    a, b = str(s).strip("[]").split(",")
    return float(a), float(b)


def fig1_source_of_skill():
    df = pd.read_csv(R / "full_metrics.csv").iloc[::-1].reset_index(drop=True)
    y = range(len(df))
    lo = (df["MASE"] - df["MASE_lo"]).clip(lower=0)
    hi = (df["MASE_hi"] - df["MASE"]).clip(lower=0)
    colors = ["#cc3311" if m == "snaive" else
              ("#0077bb" if v < 1 and df["MASE_hi"][i] < 1 else "#777777")
              for i, (m, v) in enumerate(zip(df["method"], df["MASE"]))]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(df["MASE"], list(y), xerr=[lo, hi], fmt="o", ecolor="#bbbbbb",
                elinewidth=1.4, capsize=3, ms=6, mfc="white", mec="black", zorder=3)
    for i, c in enumerate(colors):
        ax.plot(df["MASE"][i], i, "o", color=c, ms=6, zorder=4)
    ax.axvline(1.0, ls="--", color="#cc3311", lw=1)
    ax.set_yticks(list(y)); ax.set_yticklabels(df["method"], fontsize=9)
    ax.set_xlabel("MASE vs seasonal-naive  (< 1 beats naive)")
    ax.set_title("Source of skill: only recalibration of the naive forecast beats it", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "fig1_source_of_skill.png", dpi=150); plt.close(fig)


def fig2_decomposition():
    df = pd.read_csv(R / "robustness.csv")
    labels = [f"{t}\n{m}" for t, m in zip(df["target"], df["model"])]
    ci = [_parse_ci(s) for s in df["period_CI"]]
    delta = df["delta_MAE(>0=stressors help)"]
    lo = [delta[i] - ci[i][0] for i in range(len(df))]
    hi = [ci[i][1] - delta[i] for i in range(len(df))]
    y = range(len(df))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.errorbar(delta, list(y), xerr=[lo, hi], fmt="s", color="#0077bb",
                ecolor="#88aabb", elinewidth=1.4, capsize=3, ms=6, zorder=3)
    ax.axvline(0.0, ls="--", color="#cc3311", lw=1)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("ΔMAE = MAE(loss-only) − MAE(loss+stressors)   ( >0 ⇒ stressors help )")
    ax.set_title("Stressors add no detectable value: every CI spans 0, sign flips", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "fig2_decomposition.png", dpi=150); plt.close(fig)


def fig3_rolling_origin():
    df = pd.read_csv(R / "rolling_origin.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for col, lab, c in [("MASE_loss_only", "loss-only", "#0077bb"),
                        ("MASE_lagged_full", "loss + stressors", "#ee7733"),
                        ("MASE_concurrent", "concurrent stressors", "#009988")]:
        ax.plot(df["test_year"], df[col], "o-", label=lab, color=c)
    ax.axhline(1.0, ls="--", color="#cc3311", lw=1, label="seasonal-naive")
    ax.set_xlabel("held-out test year (expanding-window origin)")
    ax.set_ylabel("MASE vs seasonal-naive")
    ax.set_title("Rolling-origin: stressors never reliably help", fontsize=11)
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG / "fig3_rolling_origin.png", dpi=150); plt.close(fig)


def main():
    fig1_source_of_skill()
    fig2_decomposition()
    fig3_rolling_origin()
    print("Wrote results/figures/fig1_source_of_skill.png, fig2_decomposition.png, fig3_rolling_origin.png")


if __name__ == "__main__":
    main()
