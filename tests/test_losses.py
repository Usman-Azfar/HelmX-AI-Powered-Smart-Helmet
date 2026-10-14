import torch

from helmx_drowsiness.training.losses import (
    MultiTaskLoss,
    cumulative_ordinal_logits,
    cumulative_ordinal_loss,
    cumulative_ordinal_targets,
)


def test_missing_auxiliary_labels_contribute_zero() -> None:
    loss = MultiTaskLoss()
    outputs = {
        "logits": torch.tensor([[2.0, 0.0, -1.0]], requires_grad=True),
        "eye_closure_logits": torch.tensor([0.0], requires_grad=True),
        "yawn_logits": torch.tensor([0.0], requires_grad=True),
        "quality_logits": torch.tensor([0.0], requires_grad=True),
        "head_pose": torch.zeros((1, 3), requires_grad=True),
    }
    targets = {
        "label": torch.tensor([0]),
        "eye_closure": torch.tensor([0.0]),
        "eye_closure_mask": torch.tensor([False]),
        "yawn": torch.tensor([0.0]),
        "yawn_mask": torch.tensor([False]),
        "quality_target": torch.tensor([0.0]),
        "quality_target_mask": torch.tensor([False]),
        "head_pose": torch.zeros((1, 3)),
        "head_pose_mask": torch.tensor([False]),
    }
    losses = loss(outputs, targets)
    assert losses["eye_closure"].item() == 0.0
    assert losses["yawn"].item() == 0.0
    assert losses["head_pose"].item() == 0.0
    losses["total"].backward()


def test_cumulative_ordinal_logits_match_softmax_boundary_odds() -> None:
    logits = torch.tensor([[1.2, -0.4, 0.8], [-1.0, 0.5, 2.0]])
    probabilities = logits.softmax(dim=1)
    expected = torch.stack(
        (
            torch.log((probabilities[:, 1] + probabilities[:, 2]) / probabilities[:, 0]),
            torch.log(probabilities[:, 2] / (probabilities[:, 0] + probabilities[:, 1])),
        ),
        dim=1,
    )
    torch.testing.assert_close(cumulative_ordinal_logits(logits), expected)


def test_cumulative_ordinal_targets_use_frozen_boundary_smoothing() -> None:
    labels = torch.tensor([0, 1, 2])
    expected = torch.tensor([[0.025, 0.025], [0.975, 0.025], [0.975, 0.975]])
    torch.testing.assert_close(cumulative_ordinal_targets(labels, label_smoothing=0.05), expected)


def test_extreme_ordered_mistake_crosses_more_boundaries_with_finite_gradients() -> None:
    adjacent = torch.tensor([[-2.0, 2.0, 0.0]], requires_grad=True)
    extreme = torch.tensor([[-2.0, 0.0, 2.0]], requires_grad=True)
    label = torch.tensor([0])
    adjacent_loss = cumulative_ordinal_loss(adjacent, label)
    extreme_loss = cumulative_ordinal_loss(extreme, label)
    assert extreme_loss > adjacent_loss
    extreme_loss.backward()
    assert extreme.grad is not None
    assert torch.isfinite(extreme.grad).all()


def test_uniform_sample_weight_matches_unweighted_categorical_loss() -> None:
    logits = torch.tensor([[2.0, 0.0, -1.0], [0.1, 1.5, -0.2], [-1.0, 0.3, 2.0]])
    labels = torch.tensor([0, 1, 2])
    loss = MultiTaskLoss()
    unweighted = loss.classification_loss(logits, labels)
    weighted = loss.classification_loss(logits, labels, torch.ones(3))
    torch.testing.assert_close(unweighted, weighted)


def test_zero_sample_weight_excludes_window_from_categorical_loss() -> None:
    logits = torch.tensor([[2.0, 0.0, -1.0], [0.1, 1.5, -0.2]])
    labels = torch.tensor([0, 1])
    loss = MultiTaskLoss()
    only_first = loss.classification_loss(logits[:1], labels[:1])
    weighted = loss.classification_loss(logits, labels, torch.tensor([1.0, 0.0]))
    torch.testing.assert_close(weighted, only_first)


def test_uniform_sample_weight_matches_unweighted_ordinal_loss() -> None:
    logits = torch.tensor([[1.2, -0.4, 0.8], [-1.0, 0.5, 2.0]])
    labels = torch.tensor([0, 2])
    unweighted = cumulative_ordinal_loss(logits, labels)
    weighted = cumulative_ordinal_loss(logits, labels, sample_weight=torch.ones(2))
    torch.testing.assert_close(unweighted, weighted)


def test_forward_reads_sample_weight_from_targets() -> None:
    loss = MultiTaskLoss()
    outputs = {
        "logits": torch.tensor([[2.0, 0.0, -1.0], [0.1, 1.5, -0.2]], requires_grad=True),
        "eye_closure_logits": torch.zeros(2, requires_grad=True),
        "yawn_logits": torch.zeros(2, requires_grad=True),
        "quality_logits": torch.zeros(2, requires_grad=True),
        "head_pose": torch.zeros((2, 3), requires_grad=True),
    }
    targets = {
        "label": torch.tensor([0, 1]),
        "sample_weight": torch.tensor([1.0, 0.0]),
        "eye_closure": torch.zeros(2),
        "eye_closure_mask": torch.tensor([False, False]),
        "yawn": torch.zeros(2),
        "yawn_mask": torch.tensor([False, False]),
        "quality_target": torch.zeros(2),
        "quality_target_mask": torch.tensor([False, False]),
        "head_pose": torch.zeros((2, 3)),
        "head_pose_mask": torch.tensor([False, False]),
    }
    expected = loss.classification_loss(outputs["logits"][:1], targets["label"][:1])
    losses = loss(outputs, targets)
    torch.testing.assert_close(losses["classification"], expected)


def test_hybrid_objective_is_exact_frozen_sum_with_finite_three_logit_gradients() -> None:
    logits = torch.tensor(
        [[1.2, -0.4, 0.8], [-1.0, 0.5, 2.0], [0.2, 1.1, -0.3]], requires_grad=True
    )
    labels = torch.tensor([0, 2, 1])
    smoothing = 0.05
    categorical = torch.nn.functional.cross_entropy(logits, labels, label_smoothing=smoothing)
    ordinal = cumulative_ordinal_loss(logits, labels, label_smoothing=smoothing)
    hybrid = MultiTaskLoss(
        label_smoothing=smoothing,
        classification_objective="categorical_with_ordinal_regularization",
    ).classification_loss(logits, labels)

    torch.testing.assert_close(hybrid, categorical + 0.5 * ordinal)
    hybrid.backward()
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()
    assert (logits.grad.abs().sum(dim=0) > 0).all()
