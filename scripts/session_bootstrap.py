"""Session-clustered paired bootstrap for the second-detector comparison.

scripts/baseline_simple_detector.py reported 95% CIs for the F1 difference
(baseline - HelmX classifier) by resampling individual test windows
(src/evaluate.py: bootstrap_metric_difference). Windows overlap by 75% and
cluster within sessions, so those intervals are too narrow. This script
resamples the 10 held-out SESSIONS instead, keeping each resampled session's
windows intact, and recomputes the paired F1 difference on every resample.

Held-out predictions are regenerated with the exact code of
baseline_simple_detector.py (same split, frozen HelmX model and thresholds,
same baseline fits and validation thresholds) and saved per window to
results/experiments/heldout_window_predictions.csv, so the bootstrap can be
re-run or audited from that file alone (--from-csv).

Two resampling schemes:
- stratified (primary): the 5 sessions containing crash-like windows and the
  5 all-normal sessions are resampled separately (5 + 5 with replacement),
  so every resample has positives and F1 is always defined;
- unstratified: all 10 sessions resampled together; resamples with no
  positive window are skipped and counted.

The window-level CI is recomputed alongside for direct comparison.

Caveat stated in the output: 10 clusters (5 + 5) is a very small number for
a bootstrap; percentile intervals are approximate and likely still somewhat
optimistic. Output: results/experiments/session_bootstrap.json."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from src import config

PRED_CSV = config.EXPERIMENTS_DIR / "heldout_window_predictions.csv"
DETECTORS = ["helmx_classifier", "helmx_deployed_or_rule", "accel_peak_rule", "gyro_peak_rule", "logreg_7feat"]
BASELINE = "helmx_classifier"
N_BOOT = 10000
SEED = 0


def build_predictions():
    import baseline_simple_detector as b
    from src import io_loaders, preprocess, manifest

    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)
    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    signals = b.score_all(test_ds, b.HelmX(), b.Baselines(train_ds, val_ds))

    df = pd.DataFrame({"session_id": test_ds.session_id, "source": test_ds.source, "y": test_ds.y})
    df.insert(1, "window_in_session", df.groupby("session_id").cumcount())
    for name, (scores, thresh) in signals.items():
        df[f"{name}_score"] = scores
        df[f"{name}_threshold"] = thresh
        df[f"{name}_pred"] = (scores >= thresh).astype(int)
    df.to_csv(PRED_CSV, index=False)
    return df


def f1(y, p):
    return f1_score(y, p, zero_division=0)


def session_bootstrap(df, stratified, rng):
    groups = {sid: g for sid, g in df.groupby("session_id", sort=False)}
    pos_sessions = [s for s, g in groups.items() if g.y.any()]
    neg_sessions = [s for s, g in groups.items() if not g.y.any()]
    all_sessions = list(groups)
    arrays = {s: (g.y.to_numpy(), {d: g[f"{d}_pred"].to_numpy() for d in DETECTORS}) for s, g in groups.items()}

    diffs = {d: [] for d in DETECTORS if d != BASELINE}
    base_f1s = []
    skipped = 0
    for _ in range(N_BOOT):
        if stratified:
            pick = list(rng.choice(pos_sessions, len(pos_sessions))) + list(rng.choice(neg_sessions, len(neg_sessions)))
        else:
            pick = list(rng.choice(all_sessions, len(all_sessions)))
        y = np.concatenate([arrays[s][0] for s in pick])
        if y.sum() == 0:
            skipped += 1
            continue
        preds = {d: np.concatenate([arrays[s][1][d] for s in pick]) for d in DETECTORS}
        fb = f1(y, preds[BASELINE])
        base_f1s.append(fb)
        for d in diffs:
            diffs[d].append(f1(y, preds[d]) - fb)

    out = {}
    for d, v in diffs.items():
        v = np.asarray(v)
        lo, hi = np.percentile(v, [2.5, 97.5])
        out[d] = {
            "point_estimate_diff": float(f1(df.y, df[f"{d}_pred"]) - f1(df.y, df[f"{BASELINE}_pred"])),
            "bootstrap_mean_diff": float(v.mean()),
            "ci_95_low": float(lo), "ci_95_high": float(hi),
            "fraction_of_resamples_baseline_not_worse": float((v >= 0).mean()),
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
        }
    return {
        "scheme": "stratified 5 crash-containing + 5 all-normal sessions" if stratified else "unstratified 10 sessions",
        "n_resamples_requested": N_BOOT, "n_resamples_used": N_BOOT - skipped,
        "n_resamples_skipped_no_positives": skipped,
        "n_crash_containing_sessions": len(pos_sessions), "n_all_normal_sessions": len(neg_sessions),
        "helmx_classifier_f1_ci_95": [float(x) for x in np.percentile(base_f1s, [2.5, 97.5])],
        "paired_f1_difference_vs_helmx_classifier": out,
    }


def window_bootstrap(df, rng):
    y = df.y.to_numpy()
    preds = {d: df[f"{d}_pred"].to_numpy() for d in DETECTORS}
    diffs = {d: np.empty(N_BOOT) for d in DETECTORS if d != BASELINE}
    for i in range(N_BOOT):
        idx = rng.integers(0, len(y), len(y))
        fb = f1(y[idx], preds[BASELINE][idx])
        for d in diffs:
            diffs[d][i] = f1(y[idx], preds[d][idx]) - fb
    return {d: {"ci_95_low": float(np.percentile(v, 2.5)), "ci_95_high": float(np.percentile(v, 97.5))}
            for d, v in diffs.items()}


def per_session_table(df):
    rows = []
    for sid, g in df.groupby("session_id", sort=False):
        r = {"session_id": sid, "source": g.source.iloc[0], "n_windows": int(len(g)), "n_crash_like": int(g.y.sum())}
        for d in DETECTORS:
            p = g[f"{d}_pred"]
            r[f"{d}_tp"] = int(((p == 1) & (g.y == 1)).sum())
            r[f"{d}_fp"] = int(((p == 1) & (g.y == 0)).sum())
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-csv", action="store_true",
                    help="reuse results/experiments/heldout_window_predictions.csv instead of regenerating it")
    args = ap.parse_args()

    df = pd.read_csv(PRED_CSV) if args.from_csv else build_predictions()
    print(f"{len(df)} windows, {df.session_id.nunique()} sessions, {int(df.y.sum())} crash-like")

    report = {
        "description": ("Paired F1 difference (detector minus HelmX classifier) on the held-out test split, "
                        "with session-clustered bootstrap CIs replacing the window-level CIs of "
                        "baseline_simple_detector.py."),
        "predictions_csv": str(PRED_CSV.relative_to(config.ROOT)),
        "n_windows": int(len(df)), "n_sessions": int(df.session_id.nunique()), "n_crash_like": int(df.y.sum()),
        "n_bootstrap": N_BOOT, "seed": SEED,
        "session_bootstrap_stratified": session_bootstrap(df, True, np.random.default_rng(SEED)),
        "session_bootstrap_unstratified": session_bootstrap(df, False, np.random.default_rng(SEED)),
        "window_bootstrap_for_comparison": window_bootstrap(df, np.random.default_rng(SEED)),
        "per_session_counts": per_session_table(df),
        "caveat": ("Only 10 clusters (5 crash-containing, 5 all-normal). Percentile intervals from so few "
                   "clusters are approximate and probably still somewhat narrow; the crash-like windows are "
                   "concentrated in few sessions, which dominates the resampling variance."),
    }
    config.EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.EXPERIMENTS_DIR / "session_bootstrap.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
