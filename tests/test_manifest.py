import unittest
from types import SimpleNamespace

from src.manifest import assign_splits


def make_sessions(count, source="source", label=0):
    return [
        SimpleNamespace(session_id=f"{source}_{label}_{index}", source=source, label=label)
        for index in range(count)
    ]


class ManifestTests(unittest.TestCase):
    def test_split_is_deterministic(self):
        sessions = make_sessions(20)
        self.assertEqual(assign_splits(sessions, seed=42), assign_splits(sessions, seed=42))

    def test_every_session_has_exactly_one_split(self):
        sessions = make_sessions(12, "road", 0) + make_sessions(8, "fall", 1)
        split = assign_splits(sessions, seed=42)
        self.assertEqual(set(split), {session.session_id for session in sessions})
        self.assertTrue(set(split.values()) <= {"train", "val", "test"})

    def test_groups_with_enough_sessions_cover_all_partitions(self):
        split = assign_splits(make_sessions(10), seed=42)
        self.assertEqual(set(split.values()), {"train", "val", "test"})

    def test_tiny_groups_remain_in_training(self):
        split = assign_splits(make_sessions(2), seed=42)
        self.assertEqual(set(split.values()), {"train"})


if __name__ == "__main__":
    unittest.main()
