"""changesToMake2.txt item 3: "We still need the pure supervised CNN with no
reconstruction auxiliary objective. That is the major missing ablation if we
want to prove that joint training itself helps."

Model B: src/model.py: build_classifier_only_model() -- the identical
encoder/bottleneck/pooling architecture as the hybrid model's classification
path, but with no decoder/reconstruction branch at all, so there is no
auxiliary objective competing for the shared encoder's gradient. Trained on
the same frozen train/val/test split as every other experiment (DaRUS
included, same as the deployed model). Comparing this against the hybrid
model's classifier head (results/experiments/hybrid_ablation.json: "classifier_only")
directly tests whether joint multi-task training helps the classifier, or
whether a plain single-task CNN does just as well.

train_classifier_only_from_datasets() is reused by
scripts/label_scarcity_experiment.py, which passes in a *subsampled* train_ds
(fewer crash-labeled windows) to compare Model B's degradation against
Model A's as labeled crash data shrinks."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, evaluate
from src import model as model_lib
from train import _seed_everything  # noqa: E402


def train_classifier_only_from_datasets(seed, train_ds, val_ds, epochs=60, verbose=2):
    """Returns (model, normalizer, threshold_balanced, history)."""
    _seed_everything(seed)

    normalizer = normalize.Normalizer.fit(train_ds.X_seq, train_ds.X_aux, train_ds.y)
    X_seq_train, X_aux_train = normalizer.transform(train_ds.X_seq, train_ds.X_aux)
    X_seq_val, X_aux_val = normalizer.transform(val_ds.X_seq, val_ds.X_aux)

    _, clf_w_train = model_lib.compute_sample_weights(train_ds.y)
    _, clf_w_val = model_lib.compute_sample_weights(val_ds.y)

    model = model_lib.build_classifier_only_model()

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_auc", mode="max", patience=8, restore_best_weights=True
    )
    history = model.fit(
        {"seq": X_seq_train, "aux": X_aux_train},
        {"crash_prob": train_ds.y},
        sample_weight={"crash_prob": clf_w_train},
        validation_data=(
            {"seq": X_seq_val, "aux": X_aux_val},
            {"crash_prob": val_ds.y},
            {"crash_prob": clf_w_val},
        ),
        epochs=epochs, batch_size=128, shuffle=True, callbacks=[early_stop], verbose=verbose,
    )

    val_crash_prob = model.predict({"seq": X_seq_val, "aux": X_aux_val}, verbose=0)["crash_prob"].ravel()
    threshold = evaluate.choose_threshold_by_f1(val_ds.y, val_crash_prob)

    return model, normalizer, threshold, history


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")

    model, normalizer, threshold, history = train_classifier_only_from_datasets(
        config.RANDOM_SEED, train_ds, val_ds,
    )
    model.summary()

    config.MODELS_DIR.mkdir(exist_ok=True, parents=True)
    model.save(config.MODELS_DIR / "helmx_classifier_only.keras")
    with open(config.MODELS_DIR / "model_b_training_history.json", "w") as f:
        json.dump({k: [float(v) for v in vals] for k, vals in history.history.items()}, f, indent=2)

    X_seq_val, X_aux_val = normalizer.transform(val_ds.X_seq, val_ds.X_aux)
    val_crash_prob = model.predict({"seq": X_seq_val, "aux": X_aux_val}, verbose=0)["crash_prob"].ravel()

    X_seq_test, X_aux_test = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    test_crash_prob = model.predict({"seq": X_seq_test, "aux": X_aux_test}, verbose=0)["crash_prob"].ravel()

    report = {
        "description": (
            "Model B: pure supervised CNN classifier, no reconstruction/decoder branch, "
            "no auxiliary unsupervised objective -- isolates whether joint multi-task "
            "training (Model A / the hybrid model) helps the classifier itself."
        ),
        "threshold_balanced": threshold,
        "val": evaluate.full_classification_metrics(val_ds.y, val_crash_prob, threshold),
        "test": evaluate.full_classification_metrics(test_ds.y, test_crash_prob, threshold),
    }
    print(json.dumps(report, indent=2))
    evaluate.save_metrics(report, "model_b_metrics")


if __name__ == "__main__":
    main()
