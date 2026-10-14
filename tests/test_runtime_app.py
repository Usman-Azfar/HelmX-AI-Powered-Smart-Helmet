import numpy as np

from helmx_drowsiness.runtime.app import prepare_face


def test_prepare_face_contract() -> None:
    face = np.full((30, 20, 3), 127, dtype=np.uint8)
    prepared = prepare_face(face, 64)
    assert prepared.shape == (3, 64, 64)
    assert prepared.dtype == np.float32


def test_prepare_face_packs_dual_eye_input_at_double_width() -> None:
    face = np.zeros((100, 100, 3), dtype=np.uint8)
    prepared = prepare_face(face, 64, visual_region="dual_eye")

    assert prepared.shape == (3, 64, 128)
    assert prepared.dtype == np.float32
    assert np.isfinite(prepared).all()
