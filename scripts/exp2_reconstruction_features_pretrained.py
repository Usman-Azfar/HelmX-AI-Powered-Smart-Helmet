"""ExperimentsToPerform.txt (updated), Experiment 2 -- Reconstruction
information.

"Take the best pretrained variant and compare: no recon-error input / mean
recon error / mean + peak / compact per-channel/temporal reconstruction
features." Unlike the prior round's scripts/recon_feature_ablation.py (which
trained from scratch specifically to isolate feature-richness from
pretraining), this reuses whichever of A1/A2 won Experiment 1
(results/experiments/exp1_pretraining_comparison.json's "winning_variant_by_pr_auc"),
reading that file rather than hardcoding the choice.

Pretraining is feature-mode-independent (the autoencoder pretrain doesn't
know about the classifier's recon_feature_mode), so only 5 pretrain runs are
needed, reused across all 4 feature-mode finetunes per seed."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config, io_loaders, preprocess, manifest, evaluate
from src import model as model_lib
from train import train_hybrid_from_datasets, train_hybrid_two_stage_warmup  # noqa: E402
from train_model_c import pretrain_autoencoder  # noqa: E402
from experiment_common import evaluate_variant, mean_std, METRIC_NAMES  # noqa: E402

PRETRAIN_EPOCHS = 60
FINETUNE_EPOCHS = 60
WARMUP_EPOCHS = 5
FINETUNE_LR = 1e-4
FEATURE_MODES = ["none", "scalar", "mean_peak", "rich"]


def _load_exp1_winner():
    path = config.EXPERIMENTS_DIR / "exp1_pretraining_comparison.json"
    if not path.exists():
        print("exp1_pretraining_comparison.json not found -- defaulting to A2 (warmup), "
              "matching the prior round's result.")
        return "A2_pretrained_warmup_finetune"
    with open(path) as f:
        data = json.load(f)
    winner = data["winning_variant_by_pr_auc"]
    if winner == "A0_cold_start":
        print("Experiment 1's winner was A0 (no pretraining) -- Experiment 2 still needs a "
              "pretrained base per the file's instructions, defaulting to A2 (warmup).")
        return "A2_pretrained_warmup_finetune"
    return winner


def _finetune(winner, seed, train_ds, val_ds, pretrained_model, feature_mode):
    if winner == "A1_pretrained_full_finetune":
        fresh = model_lib.build_model(recon_weight=2.0, clf_weight=1.0, recon_feature_mode=feature_mode)
        model_lib.transfer_shared_weights(pretrained_model, fresh)
        return train_hybrid_from_datasets(seed, train_ds, val_ds, epochs=FINETUNE_EPOCHS, verbose=0, model=fresh)
    return train_hybrid_two_stage_warmup(
        seed, train_ds, val_ds, pretrained_model,
        warmup_epochs=WARMUP_EPOCHS, finetune_epochs=FINETUNE_EPOCHS, finetune_lr=FINETUNE_LR,
        recon_feature_mode=feature_mode, verbose=0,
    )


def main():
    winner = _load_exp1_winner()
    print(f"Building Experiment 2 on top of Experiment 1's winning variant: {winner}")

    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")

    per_mode = {mode: [] for mode in FEATURE_MODES}

    for seed in config.SEEDS:
        print(f"\n===== seed {seed}: pretraining =====")
        pretrained_model, _, _ = pretrain_autoencoder(seed, train_ds, val_ds, denoising_noise_std=0.0, epochs=PRETRAIN_EPOCHS, verbose=0)

        for mode in FEATURE_MODES:
            print(f"--- seed {seed}, recon_feature_mode={mode!r} ---")
            model, normalizer, thresholds, _ = _finetune(winner, seed, train_ds, val_ds, pretrained_model, mode)
            X_seq_t, X_aux_t = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
            prob = model.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
            m = evaluate_variant(test_ds.y, prob, test_ds.session_id, thresholds["classifier_prob_balanced"])
            print(f"  ROC-AUC={m['roc_auc']:.3f} PR-AUC={m['pr_auc']:.3f} F1={m['f1_score']:.3f}")
            per_mode[mode].append({"seed": seed, **m})

    summary = {mode: mean_std(runs, METRIC_NAMES) for mode, runs in per_mode.items()}
    best_mode = max(FEATURE_MODES, key=lambda m: (summary[m]["pr_auc"]["mean"] or -1))

    report = {
        "description": (
            "Experiment 2 (updated ExperimentsToPerform.txt): reconstruction-feature "
            "richness (none/mean/mean+peak/rich) on top of Experiment 1's winning "
            f"pretrained architecture ({winner}), 5 seeds each, identical metric set to "
            "Experiment 1."
        ),
        "base_architecture": winner,
        "feature_modes": FEATURE_MODES,
        "feature_counts": {"none": 0, "scalar": 1, "mean_peak": 2, "rich": 12},
        "seeds": config.SEEDS,
        "summary_mean_std": summary,
        "winning_feature_mode_by_pr_auc": best_mode,
        "per_seed_runs": per_mode,
    }
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nWinning feature mode (for Experiment 3): {best_mode}")
    evaluate.save_metrics(report, "exp2_reconstruction_features_pretrained")


if __name__ == "__main__":
    main()
