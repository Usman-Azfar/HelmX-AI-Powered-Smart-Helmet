import unittest

from scripts.check_public_release import violations


class PublicReleaseCheckTests(unittest.TestCase):
    def test_rejects_private_archives_and_raw_data(self):
        problems = violations([
            "Final Results/process_snapshot.txt",
            "data/fall/example.csv",
            "models/model.tflite",
        ])
        self.assertEqual(len(problems), 3)

    def test_rejects_internal_working_notes(self):
        self.assertEqual(
            violations(["ExperimentsToPerform.txt"]),
            ["private or superseded path is tracked: ExperimentsToPerform.txt"],
        )

    def test_allows_public_documentation(self):
        self.assertEqual(
            violations(["data/README.md", "models/MODEL_CARD.md", "src/config.py"]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
