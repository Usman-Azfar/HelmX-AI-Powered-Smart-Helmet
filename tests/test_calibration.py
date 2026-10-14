import torch

from helmx_drowsiness.evaluation.calibration import fit_temperature


def test_temperature_scaling_reduces_overconfident_nll() -> None:
    logits = torch.tensor([[8.0, -8.0], [8.0, -8.0], [-8.0, 8.0], [-8.0, 8.0]])
    labels = torch.tensor([0, 1, 1, 0])
    result = fit_temperature(logits, labels)
    assert result.temperature > 1.0
    assert result.nll_after < result.nll_before


def test_temperature_rejects_empty_data() -> None:
    try:
        fit_temperature(torch.empty(0, 2), torch.empty(0, dtype=torch.long))
    except ValueError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("empty calibration should fail")
