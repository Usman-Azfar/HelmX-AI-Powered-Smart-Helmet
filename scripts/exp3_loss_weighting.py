"""ExperimentsToPerform.txt (updated), Experiment 3 -- Task interaction.

For the winning architecture from Experiments 1-2 (results/
exp2_reconstruction_features_pretrained.json's base architecture + winning
feature mode), compares three loss-weighting variants, 5 seeds each:

  fixed_2to1        recon_weight=2.0 (every prior experiment's default ratio)
  fixed_1to1        recon_weight=1.0, static throughout fine-tuning
  staged_schedule   lambda_rec: epochs 0-9 -> 1.0, 10-19 -> 0.5, 20+ -> 0.2
                     (concrete values from the advisor's own example),
                     applied only during the fine-tune phase via
                     train.LossWeightScheduler

Per the user's scope decision, uncertainty/GradNorm/PCGrad weighting is
skipped (explicitly flagged by the advisor as heavier, optional follow-up
work) in favor of the advisor's cheap suggested diagnostic: gradient cosine
similarity between the classification-loss gradient and the
reconstruction-loss gradient on the shared bottleneck layer, computed once
(seed 42, fixed_2to1 model, one training batch) as supporting evidence for
whichever weighting variant wins -- a negative cosine similarity is direct
evidence the two objectives are pulling the shared encoder in different
directions."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, evaluate
from src import model as model_lib
from train import train_hybrid_from_datasets, train_hybrid_two_stage_warmup  # noqa: E402
from train_model_c import pretrain_autoencoder  # noqa: E402
from experiment_common import evaluate_variant, mean_std, METRIC_NAMES  # noqa: E402

PRETRAIN_EPOCHS = 60
FINETUNE_EPOCHS = 60
WARMUP_EPOCHS = 5
FINETUNE_LR = 1e-4
STAGED_SCHEDULE = [(0, 1.0), (10, 0.5), (20, 0.2)]


def _load_exp2_winner():
    path = config.EXPERIMENTS_DIR / "exp2_reconstruction_features_pretrained.json"
    if not path.exists():
        print("exp2_reconstruction_features_pretrained.json not found -- defaulting to "
              "base_architecture=A2 warmup, feature_mode=scalar.")
        return "A2_pretrained_warmup_finetune", "scalar"
    with open(path) as f:
        data = json.load(f)
    return data["base_architecture"], data["winning_feature_mode_by_pr_auc"]


def _finetune(architecture, seed, train_ds, val_ds, pretrained_model, feature_mode, recon_weight, loss_weight_schedule):
    # A1's path (train_hybrid_from_datasets) has no recon_weight/schedule hook --
    # it always builds with the fixed 2:1 default. Experiment 3's premise (varying
    # task weighting mid- and post-training) only applies cleanly to A2's two-phase
    # path, so this always uses A2's warmup procedure for the weighting ablation,
    # even if Experiment 1/2 picked A1 as the overall winner.
    return train_hybrid_two_stage_warmup(
        seed, train_ds, val_ds, pretrained_model,
        warmup_epochs=WARMUP_EPOCHS, finetune_epochs=FINETUNE_EPOCHS, finetune_lr=FINETUNE_LR,
        recon_feature_mode=feature_mode, recon_weight=recon_weight, loss_weight_schedule=loss_weight_schedule,
        verbose=0,
    )


def _gradient_conflict_diagnostic(model, X_seq_batch, X_aux_batch, y_batch):
    """Cosine similarity between d(classification_loss)/d(bottleneck) and
    d(reconstruction_loss)/d(bottleneck) on one batch -- a negative value
    means the two objectives are pulling the shared representation in
    different directions at this point in training."""
    bottleneck_vars = model.get_layer("bottleneck").trainable_variables
    inputs = {"seq": X_seq_batch, "aux": X_aux_batch}

    y_batch_col = tf.reshape(tf.cast(y_batch, "float32"), (-1, 1))
    with tf.GradientTape() as tape_clf:
        preds = model(inputs, training=False)
        clf_loss = tf.reduce_mean(tf.keras.losses.binary_crossentropy(y_batch_col, preds["crash_prob"]))
    grads_clf = tape_clf.gradient(clf_loss, bottleneck_vars)

    with tf.GradientTape() as tape_rec:
        preds = model(inputs, training=False)
        rec_loss = tf.reduce_mean(model_lib._windowed_mse(X_seq_batch, preds["reconstruction"]))
    grads_rec = tape_rec.gradient(rec_loss, bottleneck_vars)

    sims = []
    for g_clf, g_rec in zip(grads_clf, grads_rec):
        if g_clf is None or g_rec is None:
            continue
        f_clf, f_rec = tf.reshape(g_clf, [-1]), tf.reshape(g_rec, [-1])
        denom = tf.norm(f_clf) * tf.norm(f_rec)
        if denom == 0:
            continue
        sims.append(float(tf.reduce_sum(f_clf * f_rec) / denom))
    return {"per_variable_cosine_similarity": sims, "mean_cosine_similarity": float(np.mean(sims)) if sims else None}


def main():
    architecture, feature_mode = _load_exp2_winner()
    print(f"Building Experiment 3 on top of: architecture={architecture}, feature_mode={feature_mode}")

    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")

    variants = {
        "fixed_2to1": dict(recon_weight=2.0, loss_weight_schedule=None),
        "fixed_1to1": dict(recon_weight=1.0, loss_weight_schedule=None),
        "staged_schedule": dict(recon_weight=1.0, loss_weight_schedule=STAGED_SCHEDULE),
    }
    per_variant = {name: [] for name in variants}
    gradient_diagnostic = None

    for seed in config.SEEDS:
        print(f"\n===== seed {seed}: pretraining =====")
        pretrained_model, _, _ = pretrain_autoencoder(seed, train_ds, val_ds, denoising_noise_std=0.0, epochs=PRETRAIN_EPOCHS, verbose=0)

        for name, kwargs in variants.items():
            print(f"--- seed {seed}, variant={name} ---")
            model, normalizer, thresholds, _ = _finetune(
                architecture, seed, train_ds, val_ds, pretrained_model, feature_mode, **kwargs,
            )
            X_seq_t, X_aux_t = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
            prob = model.predict({"seq": X_seq_t, "aux": X_aux_t}, verbose=0)["crash_prob"].ravel()
            m = evaluate_variant(test_ds.y, prob, test_ds.session_id, thresholds["classifier_prob_balanced"])
            print(f"  ROC-AUC={m['roc_auc']:.3f} PR-AUC={m['pr_auc']:.3f} F1={m['f1_score']:.3f}")
            per_variant[name].append({"seed": seed, **m})

            if name == "fixed_2to1" and seed == 42:
                X_seq_tr, X_aux_tr = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
                batch_idx = np.arange(min(128, len(train_ds.y)))
                y_batch = train_ds.y[batch_idx].astype("float32")
                gradient_diagnostic = _gradient_conflict_diagnostic(
                    model, X_seq_tr[batch_idx], X_aux_tr[batch_idx], y_batch,
                )
                print(f"  Gradient-conflict diagnostic (bottleneck): {gradient_diagnostic}")

    summary = {name: mean_std(runs, METRIC_NAMES) for name, runs in per_variant.items()}
    best_variant = max(variants, key=lambda v: (summary[v]["pr_auc"]["mean"] or -1))

    report = {
        "description": (
            "Experiment 3 (updated ExperimentsToPerform.txt): loss-weighting variants "
            "(fixed 2:1 / fixed 1:1 / staged schedule) on top of Experiments 1-2's winning "
            f"architecture ({architecture}, feature_mode={feature_mode}), 5 seeds each, "
            "plus a one-shot gradient-cosine-similarity conflict diagnostic."
        ),
        "base_architecture": architecture,
        "base_feature_mode": feature_mode,
        "staged_schedule": STAGED_SCHEDULE,
        "seeds": config.SEEDS,
        "summary_mean_std": summary,
        "winning_variant_by_pr_auc": best_variant,
        "gradient_conflict_diagnostic": {
            "description": (
                "Cosine similarity between classification-loss and reconstruction-loss "
                "gradients w.r.t. the shared bottleneck layer, seed 42, fixed_2to1 variant, "
                "one 128-window training batch. Negative = objectives pulling the shared "
                "encoder in different directions at this point in training."
            ),
            **(gradient_diagnostic or {}),
        },
        "per_seed_runs": per_variant,
    }
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nWinning loss-weighting variant: {best_variant}")
    evaluate.save_metrics(report, "exp3_loss_weighting")


if __name__ == "__main__":
    main()
