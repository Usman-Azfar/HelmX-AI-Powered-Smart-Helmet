import numpy as np

from helmx_drowsiness.evaluation.report import detailed_classification_report


def test_detailed_report_uses_declared_class_order() -> None:
    report = detailed_classification_report(
        np.array([0, 1, 2]),
        np.eye(3),
        ("alert", "low", "drowsy"),
    )
    assert report["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert report["per_class"]["drowsy"]["recall"] == 1.0
