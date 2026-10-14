import unittest

import numpy as np

from src.resampling import resample_two_streams, resample_uniform


class ResamplingTests(unittest.TestCase):
    def test_uniform_grid_and_linear_interpolation(self):
        frame = resample_uniform(
            np.array([0.0, 0.5, 1.0]),
            {"x": np.array([0.0, 1.0, 2.0])},
            rate_hz=2.0,
        )
        np.testing.assert_allclose(frame["t"], [0.0, 0.5, 1.0])
        np.testing.assert_allclose(frame["x"], [0.0, 1.0, 2.0])

    def test_duplicate_timestamps_are_made_safe(self):
        frame = resample_uniform(
            np.array([0.0, 0.0, 1.0]),
            {"x": np.array([0.0, 1.0, 2.0])},
            rate_hz=2.0,
        )
        self.assertTrue(np.all(np.diff(frame["t"]) > 0))
        self.assertTrue(np.isfinite(frame["x"]).all())

    def test_two_streams_use_only_shared_time_range(self):
        frame = resample_two_streams(
            np.array([0.0, 1.0, 2.0]), {"a": np.array([0.0, 1.0, 2.0])},
            np.array([1.0, 2.0, 3.0]), {"b": np.array([10.0, 20.0, 30.0])},
            rate_hz=1.0,
        )
        self.assertIsNotNone(frame)
        np.testing.assert_allclose(frame["t"], [1.0, 2.0])

    def test_disjoint_streams_return_none(self):
        frame = resample_two_streams(
            np.array([0.0, 1.0]), {"a": np.array([0.0, 1.0])},
            np.array([2.0, 3.0]), {"b": np.array([2.0, 3.0])},
        )
        self.assertIsNone(frame)


if __name__ == "__main__":
    unittest.main()
