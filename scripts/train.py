"""Builds the dataset, trains the hybrid HelmX crash model, calibrates
thresholds on validation data, and saves the model + normalizer + thresholds
to models/. Mirrors what notebooks/crash-detection-model.ipynb runs interactively.

train_one(seed) is reused by scripts/train_multi_seed.py (item 5 -- multiple
seeds, mean +/- std) and scripts/unseen_crash_experiment.py (trains a
separate instance on a non-DaRUS session set). Only the seed controls model
init/shuffling; the data split always stays keyed on config.RANDOM_SEED so
it's identical and reproducible across every run.

train_hybrid_two_stage_warmup() (two-stage training follow-up) is reused by
scripts/two_stage_pretraining_experiment.py."""
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, model as model_lib, evaluate


def _seed_everything(seed):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def _hybrid_fit_targets(X_seq, y):
    return {
        "reconstruction": X_seq,
        "crash_prob": y,
        "recon_error": np.zeros((len(y), 1), dtype="float32"),
    }


def _hybrid_sample_weights(y, recon_w, clf_w):
    return {
        "reconstruction": recon_w,
        "crash_prob": clf_w,
        "recon_error": np.ones(len(y), dtype="float32"),
    }


def calibrate_thresholds(model, X_seq_val, X_aux_val, val_ds):
    """Threshold calibration shared by train_hybrid_from_datasets() and
    train_hybrid_two_stage_warmup() -- factored out so the two-phase warmup
    training loop (which can't just call train_hybrid_from_datasets, since
    its fit() call differs) doesn't duplicate this logic."""
    val_preds = model.predict({"seq": X_seq_val, "aux": X_aux_val}, verbose=0)
    val_crash_prob = val_preds["crash_prob"].ravel()
    val_recon_error = val_preds["recon_error"].ravel()
    val_recon_error_peak = evaluate.peak_reconstruction_error(X_seq_val, val_preds["reconstruction"])

    normal_mask = val_ds.y == 0
    thresholds = {
        "recon_error": float(np.percentile(val_recon_error[normal_mask], 99)),
        "recon_error_peak": float(np.percentile(val_recon_error_peak[normal_mask], 99)),
        "classifier_prob_balanced": evaluate.choose_threshold_by_f1(val_ds.y, val_crash_prob),
        "classifier_prob_moderate_recall": evaluate.choose_threshold_by_recall(val_ds.y, val_crash_prob, target_recall=0.60),
        "classifier_prob_high_recall": evaluate.choose_threshold_by_recall(val_ds.y, val_crash_prob, target_recall=0.90),
    }
    thresholds["classifier_prob"] = thresholds["classifier_prob_balanced"]
    return thresholds


def train_hybrid_from_datasets(seed, train_ds, val_ds, epochs=60, verbose=2,
                                model=None, recon_feature_mode="scalar"):
    """The reusable core of train_one() -- everything from normalization
    onward, parameterized by already-built train_ds/val_ds Dataset objects
    instead of building them from sessions/split_of itself. Factored out so
    scripts/label_scarcity_experiment.py can pass in a *subsampled* train_ds
    (fewer crash-labeled windows, same normal windows) without duplicating
    the training loop.

    `model`: if given, fine-tunes this already-built (and already-compiled)
    model instead of building a fresh one from scratch -- used by
    scripts/two_stage_pretraining_experiment.py's A1 variant (full
    fine-tuning immediately after AE pretraining, no frozen-encoder warmup
    phase). Ignored if None (default: build fresh, exactly as before).

    `recon_feature_mode`: forwarded to model_lib.build_model() when building
    a fresh model (ignored if `model` is given) -- see build_model()'s
    docstring for the ablation this supports.

    Returns (model, normalizer, thresholds, history).
    """
    _seed_everything(seed)

    normalizer = normalize.Normalizer.fit(train_ds.X_seq, train_ds.X_aux, train_ds.y)

    X_seq_train, X_aux_train = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
    X_seq_val, X_aux_val = normalizer.transform(val_ds.X_seq, val_ds.X_aux)

    recon_w_train, clf_w_train = model_lib.compute_sample_weights(train_ds.y)
    recon_w_val, clf_w_val = model_lib.compute_sample_weights(val_ds.y)

    if model is None:
        model = model_lib.build_model(recon_weight=2.0, clf_weight=1.0, recon_feature_mode=recon_feature_mode)

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_crash_prob_auc", mode="max", patience=8, restore_best_weights=True
    )

    history = model.fit(
        {"seq": X_seq_train, "aux": X_aux_train},
        _hybrid_fit_targets(X_seq_train, train_ds.y),
        sample_weight=_hybrid_sample_weights(train_ds.y, recon_w_train, clf_w_train),
        validation_data=(
            {"seq": X_seq_val, "aux": X_aux_val},
            _hybrid_fit_targets(X_seq_val, val_ds.y),
            _hybrid_sample_weights(val_ds.y, recon_w_val, clf_w_val),
        ),
        epochs=epochs,
        batch_size=128,
        shuffle=True,
        callbacks=[early_stop],
        verbose=verbose,
    )

    thresholds = calibrate_thresholds(model, X_seq_val, X_aux_val, val_ds)
    return model, normalizer, thresholds, history


def _staged_finetune(model, loss, metrics, fit_x, fit_y, fit_sw, val_x, val_y, val_sw,
                      loss_weight_schedule, finetune_epochs, finetune_lr, verbose):
    """ExperimentsToPerform.txt (updated) Experiment 3's "staged schedule"
    loss-weighting variant. Keras loss_weights aren't tf.Variables and
    recompiling *during* an active model.fit() call corrupts Keras 3's
    cached train_function (confirmed by a smoke test: recompiling inside an
    on_epoch_begin callback raises "'NoneType' object is not callable" on
    the next training step) -- so instead of a mid-fit callback, this runs
    one *separate* model.fit() call per schedule stage, recompiling only
    *between* calls, exactly like the existing warmup->finetune transition
    already does. `loss_weight_schedule`: list of (epoch, recon_weight)
    pairs, sorted ascending, epoch boundaries relative to the finetune phase.
    Only the final (open-ended) stage gets EarlyStopping, since the earlier
    stages are meant to run their fixed short duration regardless.

    Returns the last stage's Keras History object (for the
    val_crash_prob_auc curve at the end of training)."""
    schedule = sorted(loss_weight_schedule)
    stages = []
    for i, (start, weight) in enumerate(schedule):
        end = schedule[i + 1][0] if i + 1 < len(schedule) else finetune_epochs
        if start >= finetune_epochs:
            break
        stages.append((weight, min(end, finetune_epochs) - start))

    history = None
    for stage_idx, (weight, n_epochs) in enumerate(stages):
        if n_epochs <= 0:
            continue
        is_last_stage = stage_idx == len(stages) - 1
        loss_weights = {"reconstruction": weight, "crash_prob": 1.0, "recon_error": 0.0}
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=finetune_lr),
                      loss=loss, loss_weights=loss_weights, metrics=metrics)
        callbacks = []
        if is_last_stage:
            callbacks.append(tf.keras.callbacks.EarlyStopping(
                monitor="val_crash_prob_auc", mode="max", patience=8, restore_best_weights=True
            ))
        history = model.fit(
            fit_x, fit_y, sample_weight=fit_sw,
            validation_data=(val_x, val_y, val_sw),
            epochs=n_epochs, batch_size=128, shuffle=True, callbacks=callbacks, verbose=verbose,
        )
    return history


def train_hybrid_two_stage_warmup(seed, train_ds, val_ds, pretrained_model,
                                   warmup_epochs=5, finetune_epochs=60, finetune_lr=1e-4,
                                   recon_feature_mode="scalar", recon_weight=2.0,
                                   loss_weight_schedule=None, verbose=2):
    """Two-stage training, "A2" variant: builds a fresh build_model(),
    warm-starts its shared encoder/decoder from `pretrained_model` (a
    build_autoencoder_only_model() instance -- see
    model_lib.transfer_shared_weights), then trains in two phases:
      1. `warmup_epochs` with the encoder/decoder FROZEN, training only the
         classifier head (and its recon-feature extractor, which has no
         weights) on top of the pretrained representation.
      2. Unfreeze everything, recompile at a smaller learning rate
         (`finetune_lr`, vs. Adam's ~1e-3 default), and continue training
         with early stopping -- standard transfer-learning practice, so the
         classifier head's initially-random gradients don't immediately
         destroy the pretrained encoder/decoder weights before it's learned
         anything sensible to backpropagate.

    `recon_weight`: fixed reconstruction loss weight for phase 2 (default 2.0
    matches every prior experiment's hardcoded 2:1 ratio). Ignored if
    `loss_weight_schedule` is given.

    `loss_weight_schedule`: optional list of (epoch, recon_weight) pairs --
    ExperimentsToPerform.txt (updated) Experiment 3's staged-schedule
    variant, applied via LossWeightScheduler during phase 2 only (phase 1's
    frozen encoder/decoder makes the reconstruction weight irrelevant there).

    Returns (model, normalizer, thresholds, history) where history is a dict
    with "warmup" and "finetune" keys, each a Keras History.history dict.
    """
    _seed_everything(seed)

    normalizer = normalize.Normalizer.fit(train_ds.X_seq, train_ds.X_aux, train_ds.y)
    X_seq_train, X_aux_train = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
    X_seq_val, X_aux_val = normalizer.transform(val_ds.X_seq, val_ds.X_aux)
    recon_w_train, clf_w_train = model_lib.compute_sample_weights(train_ds.y)
    recon_w_val, clf_w_val = model_lib.compute_sample_weights(val_ds.y)

    model = model_lib.build_model(recon_weight=2.0, clf_weight=1.0, recon_feature_mode=recon_feature_mode)
    model_lib.transfer_shared_weights(pretrained_model, model)

    loss = {"reconstruction": model_lib._windowed_mse, "crash_prob": "binary_crossentropy", "recon_error": "mse"}
    loss_weights = {"reconstruction": 2.0, "crash_prob": 1.0, "recon_error": 0.0}
    metrics = {"crash_prob": [tf.keras.metrics.AUC(name="auc"), "accuracy"], "reconstruction": [], "recon_error": []}

    fit_x = {"seq": X_seq_train, "aux": X_aux_train}
    fit_y = _hybrid_fit_targets(X_seq_train, train_ds.y)
    fit_sw = _hybrid_sample_weights(train_ds.y, recon_w_train, clf_w_train)
    val_x = {"seq": X_seq_val, "aux": X_aux_val}
    val_y = _hybrid_fit_targets(X_seq_val, val_ds.y)
    val_sw = _hybrid_sample_weights(val_ds.y, recon_w_val, clf_w_val)

    # Phase 1: freeze the pretrained encoder/decoder, train the classifier head only.
    for name in model_lib.SHARED_LAYER_NAMES:
        try:
            model.get_layer(name).trainable = False
        except ValueError:
            pass
    model.compile(optimizer="adam", loss=loss, loss_weights=loss_weights, metrics=metrics)
    warmup_history = model.fit(
        fit_x, fit_y, sample_weight=fit_sw,
        validation_data=(val_x, val_y, val_sw),
        epochs=warmup_epochs, batch_size=128, shuffle=True, verbose=verbose,
    )

    # Phase 2: unfreeze everything, continue at a smaller learning rate.
    for name in model_lib.SHARED_LAYER_NAMES:
        try:
            model.get_layer(name).trainable = True
        except ValueError:
            pass
    if loss_weight_schedule is not None:
        finetune_history = _staged_finetune(
            model, loss, metrics, fit_x, fit_y, fit_sw, val_x, val_y, val_sw,
            loss_weight_schedule, finetune_epochs, finetune_lr, verbose,
        )
    else:
        finetune_loss_weights = {"reconstruction": recon_weight, "crash_prob": 1.0, "recon_error": 0.0}
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=finetune_lr),
                      loss=loss, loss_weights=finetune_loss_weights, metrics=metrics)
        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor="val_crash_prob_auc", mode="max", patience=8, restore_best_weights=True
        )
        finetune_history = model.fit(
            fit_x, fit_y, sample_weight=fit_sw,
            validation_data=(val_x, val_y, val_sw),
            epochs=finetune_epochs, batch_size=128, shuffle=True, callbacks=[early_stop], verbose=verbose,
        )

    thresholds = calibrate_thresholds(model, X_seq_val, X_aux_val, val_ds)
    history = {"warmup": warmup_history.history, "finetune": finetune_history.history if finetune_history else {}}
    return model, normalizer, thresholds, history


def train_one(seed, sessions=None, split_of=None, epochs=60, verbose=2):
    """Runs one full train+calibrate pass. `seed` controls model weight
    initialization and training shuffling; the data split (session ->
    train/val/test) is computed from config.RANDOM_SEED unless `split_of` is
    passed in, so it never varies with `seed`.

    Returns (model, normalizer, thresholds, history, sessions, split_of).
    """
    if sessions is None:
        sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    if split_of is None:
        split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")

    model, normalizer, thresholds, history = train_hybrid_from_datasets(
        seed, train_ds, val_ds, epochs=epochs, verbose=verbose,
    )
    return model, normalizer, thresholds, history, sessions, split_of


def main():
    print("Loading sessions...")
    sessions = io_loaders.load_all_sessions()
    print(f"Loaded {len(sessions)} sessions:")
    for source in sorted(set(s.source for s in sessions)):
        n = sum(1 for s in sessions if s.source == source)
        print(f"  {source}: {n} sessions")

    print("Canonicalizing units / removing gravity / deriving features...")
    sessions = preprocess.canonicalize_all(sessions)
    split_of = manifest.assign_splits(sessions)

    for name in ("train", "val", "test"):
        ds = manifest.build_dataset(sessions, split_of, name)
        n_normal = int((ds.y == 0).sum())
        n_anomaly = int((ds.y == 1).sum())
        print(f"  {name}: {len(ds.y)} windows ({n_normal} normal, {n_anomaly} anomaly)")

    model, normalizer, thresholds, history, sessions, split_of = train_one(
        config.RANDOM_SEED, sessions=sessions, split_of=split_of,
    )
    model.summary()

    config.MODELS_DIR.mkdir(exist_ok=True, parents=True)
    normalizer.save(config.MODELS_DIR / "normalizer.npz")
    model.save(config.MODELS_DIR / "helmx_crash_model.keras")
    with open(config.MODELS_DIR / "training_history.json", "w") as f:
        json.dump({k: [float(v) for v in vals] for k, vals in history.history.items()}, f, indent=2)

    with open(config.MODELS_DIR / "thresholds.json", "w") as f:
        json.dump(thresholds, f, indent=2)
    print("Thresholds:", thresholds)


if __name__ == "__main__":
    main()
