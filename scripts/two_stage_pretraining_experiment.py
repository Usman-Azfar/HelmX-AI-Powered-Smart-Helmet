"""Follow-up to changesToMake2.txt item 3 (Model A vs. Model B): tests
whether joint training's failure to beat plain supervised training so far
(Round 2's Model A/B comparison, both label-scarcity ablations) was caused by
optimization interference from training both objectives jointly from a cold,
random encoder init -- rather than the reconstruction objective itself being
useless to the classifier.

Two variants, both warm-starting a fresh build_model() instance's shared
encoder/decoder from a build_autoencoder_only_model() pretrained on all
normal training windows (model_lib.transfer_shared_weights):

  A1 (train_hybrid_from_datasets(model=...)): everything trainable
     immediately, fine-tune jointly like a normal training run.
  A2 (train_hybrid_two_stage_warmup): freeze the pretrained encoder/decoder
     for a few epochs while only the classifier head trains on top of the
     pretrained representation, THEN unfreeze everything and continue at a
     smaller learning rate -- standard transfer-learning practice, avoiding
     the freshly-random classifier head's early gradients from immediately
     wrecking the pretrained weights.

Compared against the already-computed from-scratch baselines at 100% labels,
25 sessions (results/experiments/label_scarcity_session_level_experiment.json's "100pct"
entries, and results/metrics/seed_variance.json) -- same frozen split, same 5 seeds,
so this is a fair apples-to-apples ablation:

    Model              | Encoder init      | Reconstruction objective
    B                  | random             | no
    A (current/deployed)| random            | joint from scratch
    A1 (this script)    | AE-pretrained     | joint fine-tune immediately
    A2 (this script)    | AE-pretrained     | classifier warmup, then joint fine-tune

If A1/A2 consistently beat both B and from-scratch A, that's evidence the
reconstruction objective DOES help the classifier once optimization
interference is removed -- a much stronger argument for the hybrid
architecture than anything found so far."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from src import config, io_loaders, preprocess, manifest, evaluate
from src import model as model_lib
from train import train_hybrid_from_datasets, train_hybrid_two_stage_warmup  # noqa: E402
from train_model_c import pretrain_autoencoder  # noqa: E402

PRETRAIN_EPOCHS = 60
FINETUNE_EPOCHS = 60
WARMUP_EPOCHS = 5
FINETUNE_LR = 1e-4


def evaluate_on_test(model, normalizer, thresholds, test_ds):
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    crash_prob = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)["crash_prob"].ravel()
    m = evaluate.full_classification_metrics(test_ds.y, crash_prob, thresholds["classifier_prob_balanced"])
    return {k: m[k] for k in ["roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity"]}


def _mean_std(values):
    arr = np.array(values, dtype=np.float64)
    return {"mean": float(arr.mean()), "std": float(arr.std())}


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Train: {len(train_ds.y)} windows, Val: {len(val_ds.y)}, Test: {len(test_ds.y)}")

    per_variant = {"A1_pretrained_full_finetune": [], "A2_pretrained_warmup_finetune": []}

    for seed in config.SEEDS:
        print(f"\n=== seed {seed}: Stage 1 pretraining (autoencoder on normal windows) ===")
        pretrained_model, _, _ = pretrain_autoencoder(
            seed, train_ds, val_ds, denoising_noise_std=0.0, epochs=PRETRAIN_EPOCHS, verbose=0,
        )

        print(f"=== seed {seed}: A1 (pretrained -> full joint fine-tune) ===")
        fresh_a1 = model_lib.build_model(recon_weight=2.0, clf_weight=1.0)
        transferred = model_lib.transfer_shared_weights(pretrained_model, fresh_a1)
        print(f"  transferred layers: {transferred}")
        model_a1, norm_a1, thresh_a1, _ = train_hybrid_from_datasets(
            seed, train_ds, val_ds, epochs=FINETUNE_EPOCHS, verbose=0, model=fresh_a1,
        )
        m1 = evaluate_on_test(model_a1, norm_a1, thresh_a1, test_ds)
        print(f"  A1: ROC-AUC={m1['roc_auc']:.3f} F1={m1['f1_score']:.3f}")
        per_variant["A1_pretrained_full_finetune"].append({"seed": seed, **m1})

        print(f"=== seed {seed}: A2 (pretrained -> classifier warmup -> joint fine-tune) ===")
        model_a2, norm_a2, thresh_a2, _ = train_hybrid_two_stage_warmup(
            seed, train_ds, val_ds, pretrained_model,
            warmup_epochs=WARMUP_EPOCHS, finetune_epochs=FINETUNE_EPOCHS, finetune_lr=FINETUNE_LR,
            verbose=0,
        )
        m2 = evaluate_on_test(model_a2, norm_a2, thresh_a2, test_ds)
        print(f"  A2: ROC-AUC={m2['roc_auc']:.3f} F1={m2['f1_score']:.3f}")
        per_variant["A2_pretrained_warmup_finetune"].append({"seed": seed, **m2})

    metric_names = ["roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity"]
    summary = {
        variant: {name: _mean_std([r[name] for r in runs]) for name in metric_names}
        for variant, runs in per_variant.items()
    }

    baselines = {}
    baseline_path = config.EXPERIMENTS_DIR / "label_scarcity_session_level_experiment.json"
    if baseline_path.exists():
        with open(baseline_path) as f:
            existing = json.load(f)
        p100 = existing["summary_mean_std"]["100pct"]
        baselines = {
            "B_random_no_reconstruction": {
                "roc_auc": p100["model_b_roc_auc"], "f1_score": p100["model_b_f1"],
            },
            "A_current_random_joint_from_scratch": {
                "roc_auc": p100["model_a_classifier_roc_auc"], "f1_score": p100["model_a_classifier_f1"],
            },
        }

    report = {
        "description": (
            "Two-stage AE pretraining -> joint fine-tuning, tested against the already-computed "
            "from-scratch Model A/Model B baselines at 100% labels (same frozen split, same 5 "
            "seeds). Tests whether cold-start multi-task optimization interference, not the "
            "reconstruction objective itself, explains why joint training hasn't beaten "
            "supervised-only so far."
        ),
        "seeds": config.SEEDS,
        "pretrain_epochs_max": PRETRAIN_EPOCHS,
        "finetune_epochs_max": FINETUNE_EPOCHS,
        "warmup_epochs": WARMUP_EPOCHS,
        "finetune_lr": FINETUNE_LR,
        "summary_mean_std": summary,
        "baselines_from_label_scarcity_100pct": baselines,
        "per_seed_runs": per_variant,
    }
    print("\n" + json.dumps(summary, indent=2))
    print("\nBaselines:\n" + json.dumps(baselines, indent=2))
    evaluate.save_metrics(report, "two_stage_pretraining_experiment")


if __name__ == "__main__":
    main()
