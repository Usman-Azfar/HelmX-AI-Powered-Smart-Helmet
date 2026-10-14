from helmx_drowsiness.datasets.mrl_eye import parse_mrl_filename


def test_mrl_filename_schema() -> None:
    record = parse_mrl_filename("s001_00042_0_1_0_2_1_01.png")
    assert record.subject_id == "001"
    assert record.image_id == "00042"
    assert record.glasses == 1
    assert record.eye_state == 0
    assert record.reflections == 2
    assert record.lighting == 1
    assert 0 <= record.fold < 5


def test_subject_fold_is_stable_across_images() -> None:
    first = parse_mrl_filename("s001_00001_0_0_0_0_0_01.png")
    second = parse_mrl_filename("s001_99999_0_1_1_2_1_03.png")
    assert first.fold == second.fold
