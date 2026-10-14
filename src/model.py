import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model

from . import config

# Layer names shared verbatim across build_model / build_classifier_only_model /
# build_autoencoder_only_model, so weights can be transferred between
# independently-built models by name (transfer_shared_weights below) rather
# than relying on Keras's auto-generated names, which depend on build order
# within a process and are not a safe way to line up two separately
# constructed models. Only layers with trainable weights need a shared name
# (MaxPooling1D/UpSampling1D/Dropout have none).
ENCODER_LAYER_NAMES = ["enc_conv1", "enc_bn1", "enc_conv2", "enc_bn2", "bottleneck"]
DECODER_LAYER_NAMES = ["dec_conv1", "dec_conv2", "reconstruction"]
SHARED_LAYER_NAMES = ENCODER_LAYER_NAMES + DECODER_LAYER_NAMES


@tf.keras.utils.register_keras_serializable(package="helmx")
def _windowed_mse(y_true, y_pred):
    """Per-sample MSE reduced to shape (batch,), unlike Keras's built-in 'mse'
    which only reduces the last axis and leaves a (batch, time) tensor that
    can't be scaled by a (batch,) sample_weight."""
    return tf.reduce_mean(tf.square(y_true - y_pred), axis=[1, 2])


@tf.keras.utils.register_keras_serializable(package="helmx")
class ReconstructionError(layers.Layer):
    """A plain Layer subclass instead of a Lambda: Keras 3 refuses to
    deserialize a saved Lambda backed by a raw Python closure (arbitrary code
    execution risk), which would otherwise break loading the saved model."""

    def call(self, inputs):
        seq, decoded = inputs
        return tf.expand_dims(tf.reduce_mean(tf.square(seq - decoded), axis=[1, 2]), axis=-1)


@tf.keras.utils.register_keras_serializable(package="helmx")
class ReconstructionFeatures(layers.Layer):
    """Richer reconstruction-error feature vector than ReconstructionError's
    single scalar mean, computed inside the graph (so it trains end-to-end
    and the classifier head can learn how to use it, unlike a post-hoc numpy
    stacking feature -- already tried in the hybrid-fusion ablation and found
    to overfit the small validation set).

    `feature_set="mean_peak"` (2 features): [mean-over-window error,
    peak-over-timestep error].

    `feature_set="rich"` (12 features): per-channel mean error (6) + the peak
    of those per-channel means (1) + the peak single-timestep error (1) +
    first-half/second-half-of-window mean error (2) + std of per-timestep
    error (1) + mean of the top-k highest-error timesteps (1). Motivation: a
    crash can hit one axis much harder than others, affect only a few
    timesteps, or show distinct onset/offset structure -- all of which the
    single scalar mean averages away."""

    def __init__(self, feature_set="rich", top_k=5, **kwargs):
        super().__init__(**kwargs)
        if feature_set not in ("mean_peak", "rich"):
            raise ValueError(f"unknown feature_set: {feature_set!r}")
        self.feature_set = feature_set
        self.top_k = top_k

    def call(self, inputs):
        seq, decoded = inputs
        sq_err = tf.square(seq - decoded)  # (batch, window, channels)
        per_timestep_mean = tf.reduce_mean(sq_err, axis=2)  # (batch, window)
        window_mean = tf.reduce_mean(per_timestep_mean, axis=1, keepdims=True)
        peak_timestep = tf.reduce_max(per_timestep_mean, axis=1, keepdims=True)

        if self.feature_set == "mean_peak":
            return tf.concat([window_mean, peak_timestep], axis=1)  # (batch, 2)

        per_channel_mean = tf.reduce_mean(sq_err, axis=1)  # (batch, channels)
        peak_channel = tf.reduce_max(per_channel_mean, axis=1, keepdims=True)

        window_len = seq.shape[1]  # static (fixed window size), not dynamic
        half = window_len // 2
        first_half_mean = tf.reduce_mean(per_timestep_mean[:, :half], axis=1, keepdims=True)
        second_half_mean = tf.reduce_mean(per_timestep_mean[:, half:], axis=1, keepdims=True)

        std_timestep = tf.math.reduce_std(per_timestep_mean, axis=1, keepdims=True)
        top_k_vals = tf.math.top_k(per_timestep_mean, k=self.top_k).values
        top_k_mean = tf.reduce_mean(top_k_vals, axis=1, keepdims=True)

        return tf.concat([
            per_channel_mean, peak_channel, peak_timestep,
            first_half_mean, second_half_mean, std_timestep, top_k_mean,
        ], axis=1)  # (batch, 12)

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"feature_set": self.feature_set, "top_k": self.top_k})
        return cfg


def build_model(window=config.WINDOW_SAMPLES,
                 n_channels=len(config.RAW_SENSOR_COLUMNS),
                 n_aux=len(config.AUX_FEATURE_COLUMNS),
                 recon_weight=1.0,
                 clf_weight=2.0,
                 recon_feature_mode="scalar"):
    """Shared Conv1D encoder with two heads:
      - reconstruction (decoder): unsupervised, trained on normal windows only
        via sample_weight, so the model keeps generalizing to crash patterns
        it never saw labeled examples of.
      - crash_prob (classifier): supervised, trained on all labeled windows,
        fed the pooled embedding + reconstruction signal + engineered aux
        stats, so it sharpens the decision boundary using the labeled
        fall/near-fall data the reconstruction-only approach left unused.

    `recon_feature_mode` controls what the classifier head sees from the
    reconstruction branch (an ablation -- see changes.md for results):
      - "scalar" (default, original behavior): the single ReconstructionError
        mean, unchanged from every model already trained/deployed with this
        default.
      - "none": no reconstruction signal at all (pooled embedding + aux only)
        -- isolates whether the reconstruction branch helps the classifier
        via this fused-feature path at all, independent of shared-encoder
        representation effects.
      - "mean_peak" / "rich": ReconstructionFeatures (2 or 12 features).
    The `recon_error` model OUTPUT (used by the deployed OR-fusion rule and
    threshold calibration, independent of the classifier) is always present
    regardless of this setting.
    """
    seq_in = layers.Input(shape=(window, n_channels), name="seq")

    x = layers.Conv1D(32, 5, padding="same", activation="relu", name="enc_conv1")(seq_in)
    x = layers.BatchNormalization(name="enc_bn1")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    x = layers.Conv1D(64, 5, padding="same", activation="relu", name="enc_conv2")(x)
    x = layers.BatchNormalization(name="enc_bn2")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    bottleneck = layers.Conv1D(64, 3, padding="same", activation="relu", name="bottleneck")(x)

    d = layers.UpSampling1D(2)(bottleneck)
    d = layers.Conv1D(64, 5, padding="same", activation="relu", name="dec_conv1")(d)
    d = layers.UpSampling1D(2)(d)
    d = layers.Conv1D(32, 5, padding="same", activation="relu", name="dec_conv2")(d)
    decoded = layers.Conv1D(n_channels, 5, padding="same", name="reconstruction")(d)

    recon_error = ReconstructionError(name="recon_error")([seq_in, decoded])

    pooled = layers.GlobalAveragePooling1D()(bottleneck)
    aux_in = layers.Input(shape=(n_aux,), name="aux")

    if recon_feature_mode == "scalar":
        clf_features = layers.Concatenate()([pooled, recon_error, aux_in])
    elif recon_feature_mode == "none":
        clf_features = layers.Concatenate()([pooled, aux_in])
    elif recon_feature_mode in ("mean_peak", "rich"):
        recon_features = ReconstructionFeatures(feature_set=recon_feature_mode, name="recon_features")(
            [seq_in, decoded]
        )
        clf_features = layers.Concatenate()([pooled, recon_features, aux_in])
    else:
        raise ValueError(f"unknown recon_feature_mode: {recon_feature_mode!r}")

    c = layers.Dense(32, activation="relu")(clf_features)
    c = layers.Dropout(0.3)(c)
    crash_prob = layers.Dense(1, activation="sigmoid", name="crash_prob")(c)

    model = Model(
        inputs={"seq": seq_in, "aux": aux_in},
        outputs={"reconstruction": decoded, "crash_prob": crash_prob, "recon_error": recon_error},
    )
    model.compile(
        optimizer="adam",
        # recon_error is a convenience output (duplicates info already in
        # `reconstruction`'s MSE) - Keras 3 requires every named output to
        # appear in the loss dict, so give it a real loss function pointed at
        # a dummy all-zero target and zero it out via loss_weights instead of
        # `loss: None`, which trips a structural-matching bug against dict y.
        loss={"reconstruction": _windowed_mse, "crash_prob": "binary_crossentropy", "recon_error": "mse"},
        loss_weights={"reconstruction": recon_weight, "crash_prob": clf_weight, "recon_error": 0.0},
        metrics={
            "crash_prob": [tf.keras.metrics.AUC(name="auc"), "accuracy"],
            "reconstruction": [],
            "recon_error": [],
        },
    )
    return model


def transfer_shared_weights(source_model, target_model, layer_names=SHARED_LAYER_NAMES):
    """Copies weights layer-by-layer, by name, from source_model into
    target_model for every name in layer_names present in both -- used to
    warm-start build_model()'s encoder/decoder from a build_autoencoder_only_model()
    pretraining run (two-stage training, see scripts/two_stage_pretraining_experiment.py).
    Silently skips any name missing from either model (e.g. build_classifier_only_model
    has no decoder layers) rather than erroring, so the same call works
    regardless of which two model types are involved."""
    transferred = []
    for name in layer_names:
        try:
            source_layer = source_model.get_layer(name)
            target_layer = target_model.get_layer(name)
        except ValueError:
            continue
        target_layer.set_weights(source_layer.get_weights())
        transferred.append(name)
    return transferred


def build_classifier_only_model(window=config.WINDOW_SAMPLES,
                                 n_channels=len(config.RAW_SENSOR_COLUMNS),
                                 n_aux=len(config.AUX_FEATURE_COLUMNS)):
    """Model B: a pure supervised CNN classifier -- the same encoder/
    bottleneck/pooling architecture as build_model()'s classification path,
    but with NO reconstruction/decoder branch at all (not just ignored at
    eval time: no decoder layers exist, so there is no auxiliary objective
    competing for the shared encoder's gradient during training). Isolates
    whether build_model()'s joint multi-task training helps the classifier
    itself, versus training the identical classification architecture alone
    (changesToMake2.txt item 3). The only structural difference from
    build_model()'s classifier head is the absence of the recon_error input
    feature, since there is no reconstruction branch to compute it from."""
    seq_in = layers.Input(shape=(window, n_channels), name="seq")

    x = layers.Conv1D(32, 5, padding="same", activation="relu", name="enc_conv1")(seq_in)
    x = layers.BatchNormalization(name="enc_bn1")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    x = layers.Conv1D(64, 5, padding="same", activation="relu", name="enc_conv2")(x)
    x = layers.BatchNormalization(name="enc_bn2")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    bottleneck = layers.Conv1D(64, 3, padding="same", activation="relu", name="bottleneck")(x)
    pooled = layers.GlobalAveragePooling1D()(bottleneck)

    aux_in = layers.Input(shape=(n_aux,), name="aux")
    clf_features = layers.Concatenate()([pooled, aux_in])
    c = layers.Dense(32, activation="relu")(clf_features)
    c = layers.Dropout(0.3)(c)
    crash_prob = layers.Dense(1, activation="sigmoid", name="crash_prob")(c)

    model = Model(inputs={"seq": seq_in, "aux": aux_in}, outputs={"crash_prob": crash_prob})
    model.compile(
        optimizer="adam",
        loss={"crash_prob": "binary_crossentropy"},
        metrics={"crash_prob": [tf.keras.metrics.AUC(name="auc"), "accuracy"]},
    )
    return model


def build_autoencoder_only_model(window=config.WINDOW_SAMPLES,
                                  n_channels=len(config.RAW_SENSOR_COLUMNS),
                                  denoising_noise_std=0.0):
    """Model C: a pure unsupervised autoencoder -- same Conv1D encoder/decoder
    as build_model()'s reconstruction branch, but no classifier head, no aux
    input, trained only on normal windows. Isolates how much detection power
    the reconstruction branch alone carries without the supervised
    classifier's labeled-data advantage (changesToMake.txt item 3). Also
    doubles as Stage 1 of two-stage training (see transfer_shared_weights):
    its encoder/decoder layers share names with build_model()'s, so a model
    trained here can warm-start a fresh build_model() instance.

    `denoising_noise_std > 0` turns this into a denoising autoencoder
    (changesToMake2.txt item 5: "improve reconstruction performance more"):
    `layers.GaussianNoise` corrupts the input only while `training=True`
    (automatically inert at inference/predict time), while the reconstruction
    target stays the clean input. Forcing the decoder to reconstruct clean
    normal riding from a corrupted view is a standard anomaly-detection
    technique for pushing an autoencoder past trivially learning
    near-identity mappings, which otherwise caps how separable normal vs.
    anomalous reconstruction error can become."""
    seq_in = layers.Input(shape=(window, n_channels), name="seq")

    x = seq_in
    if denoising_noise_std > 0:
        x = layers.GaussianNoise(denoising_noise_std)(x)

    x = layers.Conv1D(32, 5, padding="same", activation="relu", name="enc_conv1")(x)
    x = layers.BatchNormalization(name="enc_bn1")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    x = layers.Conv1D(64, 5, padding="same", activation="relu", name="enc_conv2")(x)
    x = layers.BatchNormalization(name="enc_bn2")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.2)(x)

    bottleneck = layers.Conv1D(64, 3, padding="same", activation="relu", name="bottleneck")(x)

    d = layers.UpSampling1D(2)(bottleneck)
    d = layers.Conv1D(64, 5, padding="same", activation="relu", name="dec_conv1")(d)
    d = layers.UpSampling1D(2)(d)
    d = layers.Conv1D(32, 5, padding="same", activation="relu", name="dec_conv2")(d)
    decoded = layers.Conv1D(n_channels, 5, padding="same", name="reconstruction")(d)

    model = Model(inputs=seq_in, outputs=decoded)
    model.compile(optimizer="adam", loss=_windowed_mse)
    return model


def compute_sample_weights(y):
    """recon head only learns from normal windows; the classifier head is
    class-balanced so the (typically much rarer) crash windows aren't
    drowned out."""
    recon_w = (y == 0).astype("float32")

    n_pos = max(1, (y == 1).sum())
    n_neg = max(1, (y == 0).sum())
    total = n_pos + n_neg
    w_pos = total / (2.0 * n_pos)
    w_neg = total / (2.0 * n_neg)
    clf_w = np.where(y == 1, w_pos, w_neg).astype("float32")

    return recon_w, clf_w
