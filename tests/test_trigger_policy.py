import unittest

from deploy.crash_monitor import TriggerPolicy


class TriggerPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = TriggerPolicy(
            classifier_threshold=0.8,
            recon_threshold=5.0,
            consecutive_windows=3,
            cooldown_seconds=10.0,
        )

    def test_requires_consecutive_anomalies(self):
        self.assertEqual(self.policy.update(0.9, 0.0, now=0.0), (True, False))
        self.assertEqual(self.policy.update(0.9, 0.0, now=1.0), (True, False))
        self.assertEqual(self.policy.update(0.9, 0.0, now=2.0), (True, True))

    def test_normal_window_resets_streak(self):
        self.policy.update(0.9, 0.0, now=0.0)
        self.policy.update(0.1, 0.0, now=1.0)
        self.assertEqual(self.policy.update(0.9, 0.0, now=2.0), (True, False))

    def test_reconstruction_branch_can_trigger(self):
        outcomes = [self.policy.update(0.1, 6.0, now=float(i)) for i in range(3)]
        self.assertEqual(outcomes[-1], (True, True))

    def test_cooldown_suppresses_retrigger(self):
        for timestamp in (0.0, 1.0, 2.0):
            self.policy.update(0.9, 0.0, now=timestamp)
        outcomes = [self.policy.update(0.9, 0.0, now=t) for t in (3.0, 4.0, 5.0)]
        self.assertFalse(any(triggered for _, triggered in outcomes))
        self.assertEqual(self.policy.update(0.9, 0.0, now=12.0), (True, True))


if __name__ == "__main__":
    unittest.main()
