from __future__ import annotations

import torch
from torch import Tensor, nn

from helmx_drowsiness.training.engine import (
    collect_video_bag_logits,
    evaluate,
    evaluate_video_bags,
    train_epoch,
    train_video_bag_epoch,
)
from helmx_drowsiness.training.losses import MultiTaskLoss


class ToyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.tensor(0.25))

    def forward(self, frames: Tensor, physiology: Tensor, quality: Tensor) -> dict[str, Tensor]:
        del physiology, quality
        score = frames[:, 0, 0, 0, 0] * self.weight
        zero = score * 0
        return {
            "logits": torch.stack((-score, score), dim=-1),
            "eye_closure_logits": zero,
            "yawn_logits": zero,
            "head_pose": zero[:, None].expand(-1, 3),
            "quality_logits": zero,
            "modality_weights": torch.full((len(score), 1, 2), 0.5),
        }


def _batch() -> dict[str, Tensor]:
    false = torch.tensor([False])
    return {
        "frames": torch.ones(1, 1, 3, 1, 1),
        "physiology": torch.zeros(1, 1, 12),
        "quality": torch.ones(1, 1, 2),
        "label": torch.tensor([1]),
        "eye_closure": torch.zeros(1),
        "eye_closure_mask": false,
        "yawn": torch.zeros(1),
        "yawn_mask": false,
        "head_pose": torch.zeros(1, 3),
        "head_pose_mask": false,
        "quality_target": torch.zeros(1),
        "quality_target_mask": false,
    }


def test_partial_accumulation_group_is_not_underweighted() -> None:
    reference = ToyModel()
    accumulated = ToyModel()
    objective = MultiTaskLoss()
    reference_optimizer = torch.optim.SGD(reference.parameters(), lr=0.1)
    accumulated_optimizer = torch.optim.SGD(accumulated.parameters(), lr=0.1)

    train_epoch(
        reference,
        [_batch()],
        objective,
        reference_optimizer,
        device=torch.device("cpu"),
        accumulation_steps=1,
        mixed_precision=False,
    )
    train_epoch(
        accumulated,
        [_batch()],
        objective,
        accumulated_optimizer,
        device=torch.device("cpu"),
        accumulation_steps=4,
        mixed_precision=False,
    )

    torch.testing.assert_close(accumulated.weight, reference.weight)


def test_evaluate_rejects_empty_loader() -> None:
    model = ToyModel()
    try:
        evaluate(model, [], MultiTaskLoss(), device=torch.device("cpu"))
    except ValueError as error:
        assert "no samples" in str(error)
    else:
        raise AssertionError("empty evaluation loader should fail")


def test_epoch_results_expose_zero_masked_auxiliary_losses() -> None:
    model = ToyModel()
    objective = MultiTaskLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    train_result = train_epoch(
        model,
        [_batch()],
        objective,
        optimizer,
        device=torch.device("cpu"),
        mixed_precision=False,
    )
    other_class = _batch()
    other_class["label"] = torch.tensor([0])
    validation_result = evaluate(
        model, [_batch(), other_class], objective, device=torch.device("cpu")
    )

    for result in (train_result, validation_result):
        assert result.component_losses["eye_closure"] == 0.0
        assert result.component_losses["yawn"] == 0.0
        assert result.component_losses["head_pose"] == 0.0
        assert result.component_losses["quality"] == 0.0


def test_video_bag_training_and_evaluation_pool_instance_logits() -> None:
    model = ToyModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    bag = {
        "frames": torch.tensor([1.0, 2.0, 3.0]).reshape(1, 3, 1, 1, 1, 1),
        "physiology": torch.zeros(1, 3, 1, 12),
        "quality": torch.ones(1, 3, 1, 2),
        "label": torch.tensor([1]),
    }
    before = model.weight.detach().clone()
    result = train_video_bag_epoch(
        model,
        [bag],
        optimizer,
        device=torch.device("cpu"),
        label_smoothing=0.05,
        mixed_precision=False,
    )
    assert result.loss > 0
    assert not torch.equal(model.weight, before)
    logits, labels = collect_video_bag_logits(model, [bag], device=torch.device("cpu"))
    reversed_bag = {**bag, "frames": bag["frames"].flip(1)}
    reversed_logits, _ = collect_video_bag_logits(model, [reversed_bag], device=torch.device("cpu"))
    torch.testing.assert_close(logits, reversed_logits)
    assert labels.tolist() == [1]
    evaluation = evaluate_video_bags(
        model,
        [bag, {**bag, "label": torch.tensor([0])}],
        device=torch.device("cpu"),
        label_smoothing=0.05,
    )
    assert evaluation.metrics.samples == 2
