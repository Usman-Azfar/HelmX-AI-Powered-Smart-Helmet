"""changesToMake.txt item 3: "Model C" -- a pure autoencoder/anomaly-only
experiment, no classifier head, no aux stats, no labeled-data advantage at
all. Trained only on normal windows; anomaly score is the reconstruction
error (both the mean-over-window and peak-over-window variants, see
src/evaluate.py: peak_reconstruction_error) thresholded at the 99th
percentile of normal validation windows. This isolates how much detection
power the unsupervised branch alone carries, for direct comparison against
the hybrid model's classifier head and reconstruction branch.

changesToMake2.txt item 5 ("I would not describe this as reconstruction
performance being 'significantly improved' ... improve reconstruction
performance more"): trains a SECOND variant, a denoising autoencoder
(src/model.py: build_autoencoder_only_model(denoising_noise_std=...)), and
reports both plain and denoising side by side so the paper can cite whichever
genuinely wins rather than assume denoising helps."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, evaluate
from src import model as model_lib
from train import _seed_everything  # noqa: E402

DENOISING_NOISE_STD = 0.25


def pretrain_autoencoder(seed, train_ds, val_ds, denoising_noise_std=0.0, epochs=60, verbose=2):
    """Stage 1 of two-stage training (ExperimentsToPerform follow-up):
    trains build_autoencoder_only_model() on normal-only windows from
    scratch, exactly like train_model_c.py's own variants, but as a reusable
    function returning the trained model + normalizer instead of also
    evaluating/saving it -- scripts/two_stage_pretraining_experiment.py
    transfers this model's encoder/decoder weights into a fresh
    build_model() instance (model_lib.transfer_shared_weights) rather than
    using this autoencoder standalone.

    Returns (model, normalizer, history).
    """
    _seed_everything(seed)

    normalizer = normalize.Normalizer.fit(train_ds.X_seq, train_ds.X_aux, train_ds.y)
    X_seq_train, _ = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
    X_seq_val, _ = normalizer.transform(val_ds.X_seq, val_ds.X_aux)
    normal_train = train_ds.y == 0
    normal_val = val_ds.y == 0

    model = model_lib.build_autoencoder_only_model(denoising_noise_std=denoising_noise_std)
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", mode="min", patience=8, restore_best_weights=True
    )
    history = model.fit(
        X_seq_train[normal_train], X_seq_train[normal_train],
        validation_data=(X_seq_val[normal_val], X_seq_val[normal_val]),
        epochs=epochs, batch_size=128, shuffle=True, callbacks=[early_stop], verbose=verbose,
    )
    return model, normalizer, history


def _train_variant(name, denoising_noise_std, X_seq_train, normal_train, X_seq_val, normal_val,
                    X_seq_test, test_y):
    print(f"\n=== Model C variant: {name} (denoising_noise_std={denoising_noise_std}) ===")
    model = model_lib.build_autoencoder_only_model(denoising_noise_std=denoising_noise_std)

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", mode="min", patience=8, restore_best_weights=True
    )
    model.fit(
        X_seq_train[normal_train], X_seq_train[normal_train],
        validation_data=(X_seq_val[normal_val], X_seq_val[normal_val]),
        epochs=60, batch_size=128, shuffle=True, callbacks=[early_stop], verbose=2,
    )

    config.MODELS_DIR.mkdir(exist_ok=True, parents=True)
    model_filename = "helmx_autoencoder_only.keras" if name == "plain" else f"helmx_autoencoder_only_{name}.keras"
    model.save(config.MODELS_DIR / model_filename)

    recon_val = model.predict(X_seq_val, verbose=0)
    recon_error_mean_val = np.mean(np.square(X_seq_val - recon_val), axis=(1, 2))
    recon_error_peak_val = evaluate.peak_reconstruction_error(X_seq_val, recon_val)

    thresholds = {
        "recon_error_mean": float(np.percentile(recon_error_mean_val[normal_val], 99)),
        "recon_error_peak": float(np.percentile(recon_error_peak_val[normal_val], 99)),
    }

    recon_test = model.predict(X_seq_test, verbose=0)
    recon_error_mean_test = np.mean(np.square(X_seq_test - recon_test), axis=(1, 2))
    recon_error_peak_test = evaluate.peak_reconstruction_error(X_seq_test, recon_test)

    return {
        "model_file": model_filename,
        "thresholds": thresholds,
        "test": {
            "mean_error": evaluate.full_classification_metrics(test_y, recon_error_mean_test, thresholds["recon_error_mean"]),
            "peak_error": evaluate.full_classification_metrics(test_y, recon_error_peak_test, thresholds["recon_error_peak"]),
        },
    }


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")

    normalizer = normalize.Normalizer.fit(train_ds.X_seq, train_ds.X_aux, train_ds.y)
    X_seq_train, _ = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
    X_seq_val, _ = normalizer.transform(val_ds.X_seq, val_ds.X_aux)
    X_seq_test, _ = normalizer.transform(test_ds.X_seq, test_ds.X_aux)

    normal_train = train_ds.y == 0
    normal_val = val_ds.y == 0

    variants = {
        "plain": _train_variant("plain", 0.0, X_seq_train, normal_train, X_seq_val, normal_val,
                                 X_seq_test, test_ds.y),
        "denoising": _train_variant("denoising", DENOISING_NOISE_STD, X_seq_train, normal_train,
                                     X_seq_val, normal_val, X_seq_test, test_ds.y),
    }

    best_variant = max(
        variants,
        key=lambda k: max(variants[k]["test"]["mean_error"]["roc_auc"],
                           variants[k]["test"]["peak_error"]["roc_auc"]),
    )
    report = {
        "description": (
            "Model C: pure autoencoder, no classifier head, no aux input, trained only on "
            "normal windows. 'plain' = original architecture; 'denoising' = same architecture "
            "with GaussianNoise-corrupted input during training only (changesToMake2.txt item 5)."
        ),
        "n_train_normal_windows": int(normal_train.sum()),
        "n_val_windows": int(len(val_ds.y)),
        "n_test_windows": int(len(test_ds.y)),
        "denoising_noise_std": DENOISING_NOISE_STD,
        "variants": variants,
        "best_variant_by_test_roc_auc": best_variant,
    }
    print(json.dumps(report, indent=2))
    evaluate.save_metrics(report, "model_c_metrics")


if __name__ == "__main__":
    main()
