import torch

from helmx_drowsiness.models import QualityAwareTemporalNet


def test_model_output_contract() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=2,
        pretrained=False,
    ).eval()
    frames = torch.rand(2, 4, 3, 64, 64)
    physiology = torch.rand(2, 4, 12)
    quality = torch.rand(2, 4, 2)
    with torch.inference_mode():
        output = model(frames, physiology, quality)
    assert output["logits"].shape == (2, 3)
    assert output["modality_weights"].shape == (2, 4, 2)
    torch.testing.assert_close(output["modality_weights"].sum(dim=-1), torch.ones(2, 4))


def test_dual_eye_shared_encoding_is_invariant_to_eye_order() -> None:
    torch.manual_seed(11)
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        dropout=0.0,
        pretrained=False,
        fusion_mode="visual_only",
    ).eval()
    frames = torch.rand(1, 4, 3, 64, 128)
    swapped = torch.cat((frames[..., 64:], frames[..., :64]), dim=-1)
    physiology = torch.rand(1, 4, 12)
    quality = torch.rand(1, 4, 2)

    with torch.inference_mode():
        original = model(frames, physiology, quality)
        reversed_eyes = model(swapped, physiology, quality)

    torch.testing.assert_close(original["logits"], reversed_eyes["logits"])


def test_controlled_fusion_ablation_modes() -> None:
    frames = torch.rand(1, 2, 3, 64, 64)
    physiology = torch.rand(1, 2, 12)
    quality = torch.rand(1, 2, 2)
    expected = {
        "equal": torch.tensor([0.5, 0.5]),
        "visual_only": torch.tensor([1.0, 0.0]),
        "physiology_only": torch.tensor([0.0, 1.0]),
    }
    for mode, target in expected.items():
        model = QualityAwareTemporalNet(
            physiology_features=12,
            hidden_size=32,
            temporal_blocks=1,
            pretrained=False,
            fusion_mode=mode,
        ).eval()
        with torch.inference_mode():
            weights = model(frames, physiology, quality)["modality_weights"]
        torch.testing.assert_close(weights[0, 0], target)


def test_modality_dropout_is_training_only_and_temporally_consistent() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        pretrained=False,
        fusion_mode="quality_gated",
        modality_dropout_probability=1.0,
    )
    visual = torch.rand(64, 4, 32)
    physical = torch.rand(64, 4, 32)
    quality = torch.ones(64, 4, 2)

    torch.manual_seed(13)
    model.train()
    training_weights = model._modality_weights(visual, physical, quality)
    assert torch.all((training_weights == 0.0) | (training_weights == 1.0))
    torch.testing.assert_close(
        training_weights,
        training_weights[:, :1].expand_as(training_weights),
    )
    assert set(training_weights[:, 0, 0].tolist()) == {0.0, 1.0}

    model.eval()
    inference_weights = model._modality_weights(visual, physical, quality)
    assert torch.all((inference_weights > 0.0) & (inference_weights < 1.0))


def test_quality_concat_uses_exact_normalized_quality_and_separate_channels() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        pretrained=False,
        fusion_mode="quality_concat",
    ).eval()
    model.fusion_projection = torch.nn.Identity()
    visual = torch.randn(2, 3, 32)
    physical = torch.randn(2, 3, 32)
    quality = torch.tensor([[[0.8, 0.2]], [[0.0, 0.0]]]).expand(2, 3, 2)

    fused, weights = model._fuse_modalities(visual, physical, quality)

    expected_weights = quality.clamp_min(1e-4)
    expected_weights = expected_weights / expected_weights.sum(dim=-1, keepdim=True)
    expected_fused = torch.cat(
        (
            expected_weights[..., :1] * visual,
            expected_weights[..., 1:] * physical,
            quality,
        ),
        dim=-1,
    )
    torch.testing.assert_close(weights, expected_weights)
    torch.testing.assert_close(fused, expected_fused)
    assert torch.isfinite(fused).all()


def test_quality_concat_gradients_reach_both_modalities_and_fusion() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        dropout=0.0,
        pretrained=False,
        fusion_mode="quality_concat",
    ).train()
    frames = torch.rand(1, 4, 3, 64, 64)
    physiology = torch.rand(1, 4, 12)
    quality = torch.rand(1, 4, 2)

    model(frames, physiology, quality)["logits"].sum().backward()

    modules = (model.visual_projection, model.physiology_projection, model.fusion_projection)
    for module in modules:
        gradients = [parameter.grad for parameter in module.parameters()]
        assert gradients
        assert all(
            gradient is not None and torch.isfinite(gradient).all() for gradient in gradients
        )


def test_quality_gated_fusion_keeps_historical_weighted_sum_and_state_keys() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        pretrained=False,
        fusion_mode="quality_gated",
    ).eval()
    visual = torch.randn(2, 3, 32)
    physical = torch.randn(2, 3, 32)
    quality = torch.rand(2, 3, 2)

    fused, weights = model._fuse_modalities(visual, physical, quality)

    torch.testing.assert_close(fused, weights[..., :1] * visual + weights[..., 1:] * physical)
    assert not any(key.startswith("fusion_projection.") for key in model.state_dict())


def test_freeze_visual_backbone_keeps_parameters_and_batchnorm_fixed() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        dropout=0.0,
        pretrained=False,
    )
    state_keys = tuple(model.state_dict())
    model.freeze_visual_backbone()
    model.train()

    assert not model.visual_backbone.training
    assert model.visual_projection.training
    assert all(not parameter.requires_grad for parameter in model.visual_backbone.parameters())
    assert tuple(model.state_dict()) == state_keys

    batchnorm = next(
        module
        for module in model.visual_backbone.modules()
        if isinstance(module, torch.nn.BatchNorm2d)
    )
    running_mean = batchnorm.running_mean.clone()
    backbone_parameters = {
        name: parameter.detach().clone()
        for name, parameter in model.visual_backbone.named_parameters()
    }
    frames = torch.rand(2, 4, 3, 64, 64)
    physiology = torch.rand(2, 4, 12)
    quality = torch.rand(2, 4, 2)

    model(frames, physiology, quality)["logits"].sum().backward()

    torch.testing.assert_close(batchnorm.running_mean, running_mean)
    for name, parameter in model.visual_backbone.named_parameters():
        assert parameter.grad is None
        torch.testing.assert_close(parameter, backbone_parameters[name])
    projection_gradients = [parameter.grad for parameter in model.visual_projection.parameters()]
    classifier_gradients = [parameter.grad for parameter in model.classifier.parameters()]
    assert all(
        gradient is not None and torch.isfinite(gradient).all()
        for gradient in projection_gradients + classifier_gradients
    )
