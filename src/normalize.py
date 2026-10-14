from dataclasses import dataclass

import numpy as np


@dataclass
class Normalizer:
    seq_mean: np.ndarray
    seq_std: np.ndarray
    aux_mean: np.ndarray
    aux_std: np.ndarray

    @classmethod
    def fit(cls, X_seq, X_aux, y):
        """Fit only on normal-labeled windows: the autoencoder's job is to
        model what 'normal' looks like, so normalization should be anchored
        to that distribution, not the crash-like windows too."""
        normal = y == 0
        seq_mean = X_seq[normal].mean(axis=(0, 1))
        seq_std = X_seq[normal].std(axis=(0, 1)) + 1e-8
        aux_mean = X_aux[normal].mean(axis=0)
        aux_std = X_aux[normal].std(axis=0) + 1e-8
        return cls(seq_mean, seq_std, aux_mean, aux_std)

    def transform(self, X_seq, X_aux):
        return (X_seq - self.seq_mean) / self.seq_std, (X_aux - self.aux_mean) / self.aux_std

    def save(self, path):
        np.savez(path, seq_mean=self.seq_mean, seq_std=self.seq_std,
                  aux_mean=self.aux_mean, aux_std=self.aux_std)

    @classmethod
    def load(cls, path):
        data = np.load(path)
        return cls(data["seq_mean"], data["seq_std"], data["aux_mean"], data["aux_std"])
