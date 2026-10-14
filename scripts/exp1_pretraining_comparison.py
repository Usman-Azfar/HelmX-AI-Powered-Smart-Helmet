"""ExperimentsToPerform.txt (updated), Experiment 1 -- Pretraining.

    Variant  Description
    B        supervised-only
    A0       current cold-start hybrid
    A1       AE pretrained -> joint fine-tune
    A2       AE pretrained -> frozen encoder classifier warm-up -> joint fine-tune

All four trained fresh here, 5 seeds each (config.SEEDS), same frozen split,
scored with the identical metric set (scripts/experiment_common.evaluate_variant):
ROC-AUC, PR-AUC, F1, recall at 95% specificity, event-level session recall.
This replaces relying on two previously-separate sources for this table
(results/experiments/label_scarcity_session_level_experiment.json for B/A0,
results/experiments/two_stage_pretraining_experiment.json for A1/A2), which didn't share
a metric definition -- see the round's plan for why that wasn't good enough
for this comparison.

Also selects and prints the "winning" variant among A0/A1/A2 (highest mean
PR-AUC, ties broken by event_level_session_recall) for
scripts/exp2_reconstruction_features_pretrained.py to build on. B is not a
candidate winner -- it doesn't have a reconstruction branch to extend."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config, io_loaders, preprocess, manifest, evaluate
from train import train_hybrid_from_datasets, train_hybrid_two_stage_warmup  # noqa: E402
from train_model_b import train_classifier_only_from_datasets  # noqa: E402
from train_model_c import pretrain_autoencoder  # noqa: E402
from experiment_common import evaluate_variant, mean_std, METRIC_NAMES  # noqa: E402

PRETRAIN_EPOCHS = 60
FINETUNE_EPOCHS = 60
WARMUP_EPOCHS = 5
FINETUNE_LR = 1e-4


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Train: {len(train_ds.y)} windows, Val: {len(val_ds.y)}, Test: {len(test_ds.y)}")
    n_crash_sessions = len({sid for sid, y in zip(train_ds.session_id, train_ds.y) if y == 1})
    print(f"Train crash-labeled sessions (window-derived, sanity check): {n_crash_sessions}")

    per_variant = {"B": [], "A0_cold_start": [], "A1_pretrained_full_finetune": [], "A2_pretrained_warmup_finetune": []}

    for seed in config.SEEDS:
        print(f"\n===== seed {seed} =====")

        print("--- B: supervised-only ---")
        model_b, norm_b, thresh_b, _ = train_classifier_only_from_datasets(seed, train_ds, val_ds, verbose=0)
        X_seq_t, X_aux_t = norm_b.transform(test_ds.X_seq, test_ds.X_aux)
        prob_b = model_b.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
        m_b = evaluate_variant(test_ds.y, prob_b, test_ds.session_id, thresh_b)
        print(f"  B: ROC-AUC={m_b['roc_auc']:.3f} PR-AUC={m_b['pr_auc']:.3f} F1={m_b['f1_score']:.3f}")
        per_variant["B"].append({"seed": seed, **m_b})

        print("--- A0: cold-start hybrid (current/deployed architecture) ---")
        model_a0, norm_a0, thresh_a0, _ = train_hybrid_from_datasets(seed, train_ds, val_ds, epochs=FINETUNE_EPOCHS, verbose=0)
        X_seq_t, X_aux_t = norm_a0.transform(test_ds.X_seq, test_ds.X_aux)
        prob_a0 = model_a0.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
        m_a0 = evaluate_variant(test_ds.y, prob_a0, test_ds.session_id, thresh_a0["classifier_prob_balanced"])
        print(f"  A0: ROC-AUC={m_a0['roc_auc']:.3f} PR-AUC={m_a0['pr_auc']:.3f} F1={m_a0['f1_score']:.3f}")
        per_variant["A0_cold_start"].append({"seed": seed, **m_a0})

        print("--- Stage 1 pretraining (autoencoder on normal windows) ---")
        pretrained_model, _, _ = pretrain_autoencoder(seed, train_ds, val_ds, denoising_noise_std=0.0, epochs=PRETRAIN_EPOCHS, verbose=0)

        print("--- A1: pretrained -> full joint fine-tune ---")
        from src import model as model_lib
        fresh_a1 = model_lib.build_model(recon_weight=2.0, clf_weight=1.0)
        model_lib.transfer_shared_weights(pretrained_model, fresh_a1)
        model_a1, norm_a1, thresh_a1, _ = train_hybrid_from_datasets(seed, train_ds, val_ds, epochs=FINETUNE_EPOCHS, verbose=0, model=fresh_a1)
        X_seq_t, X_aux_t = norm_a1.transform(test_ds.X_seq, test_ds.X_aux)
        prob_a1 = model_a1.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
        m_a1 = evaluate_variant(test_ds.y, prob_a1, test_ds.session_id, thresh_a1["classifier_prob_balanced"])
        print(f"  A1: ROC-AUC={m_a1['roc_auc']:.3f} PR-AUC={m_a1['pr_auc']:.3f} F1={m_a1['f1_score']:.3f}")
        per_variant["A1_pretrained_full_finetune"].append({"seed": seed, **m_a1})

        print("--- A2: pretrained -> classifier warmup -> joint fine-tune ---")
        model_a2, norm_a2, thresh_a2, _ = train_hybrid_two_stage_warmup(
            seed, train_ds, val_ds, pretrained_model,
            warmup_epochs=WARMUP_EPOCHS, finetune_epochs=FINETUNE_EPOCHS, finetune_lr=FINETUNE_LR, verbose=0,
        )
        X_seq_t, X_aux_t = norm_a2.transform(test_ds.X_seq, test_ds.X_aux)
        prob_a2 = model_a2.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
        m_a2 = evaluate_variant(test_ds.y, prob_a2, test_ds.session_id, thresh_a2["classifier_prob_balanced"])
        print(f"  A2: ROC-AUC={m_a2['roc_auc']:.3f} PR-AUC={m_a2['pr_auc']:.3f} F1={m_a2['f1_score']:.3f}")
        per_variant["A2_pretrained_warmup_finetune"].append({"seed": seed, **m_a2})

    summary = {variant: mean_std(runs, METRIC_NAMES) for variant, runs in per_variant.items()}

    candidates = ["A0_cold_start", "A1_pretrained_full_finetune", "A2_pretrained_warmup_finetune"]
    winner = max(
        candidates,
        key=lambda v: (summary[v]["pr_auc"]["mean"] or -1, summary[v]["event_level_session_recall"]["mean"] or -1),
    )

    report = {
        "description": (
            "Experiment 1 (updated ExperimentsToPerform.txt): B / A0-cold-start / "
            "A1-pretrained-finetune / A2-pretrained-warmup, all trained fresh with an "
            "identical metric set (ROC-AUC, PR-AUC, F1, precision, recall, recall at 95% "
            "specificity, event-level session recall)."
        ),
        "seeds": config.SEEDS,
        "pretrain_epochs_max": PRETRAIN_EPOCHS,
        "finetune_epochs_max": FINETUNE_EPOCHS,
        "warmup_epochs": WARMUP_EPOCHS,
        "finetune_lr": FINETUNE_LR,
        "n_train_windows": int(len(train_ds.y)),
        "n_val_windows": int(len(val_ds.y)),
        "n_test_windows": int(len(test_ds.y)),
        "summary_mean_std": summary,
        "winning_variant_by_pr_auc": winner,
        "per_seed_runs": per_variant,
    }
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nWinning variant (for Experiment 2): {winner}")
    evaluate.save_metrics(report, "exp1_pretraining_comparison")


if __name__ == "__main__":
    main()
