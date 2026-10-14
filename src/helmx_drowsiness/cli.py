"""Small command-line surface for validation and reproducible automation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rich.console import Console

from helmx_drowsiness import __version__
from helmx_drowsiness.assets import download_face_landmarker
from helmx_drowsiness.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helmx-drowsiness")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-config", help="validate a YAML configuration")
    validate.add_argument("path", type=Path)

    manifest = commands.add_parser("validate-manifest", help="validate subject-disjoint data")
    manifest.add_argument("path", type=Path)
    manifest.add_argument("--skip-path-check", action="store_true")

    assets = commands.add_parser("download-assets", help="download official runtime assets")
    assets.add_argument(
        "--face-landmarker",
        type=Path,
        default=Path("artifacts/models/face_landmarker.task"),
    )

    live = commands.add_parser("run", help="run calibrated real-time ONNX inference")
    live.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    live.add_argument("--model", type=Path, required=True)
    live.add_argument(
        "--face-landmarker",
        type=Path,
        default=Path("artifacts/models/face_landmarker.task"),
    )
    live.add_argument("--alarm", type=Path, default=Path("alarm.wav"))
    live.add_argument("--camera", type=int, default=0)

    train = commands.add_parser("train", help="run one reproducible training seed")
    train.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    train.add_argument("--output", type=Path, default=Path("runs"))
    train.add_argument("--seed", type=int)

    train_all = commands.add_parser("train-all", help="train and aggregate every configured seed")
    train_all.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    train_all.add_argument("--output", type=Path, default=Path("runs"))

    predict_split = commands.add_parser(
        "predict-split", help="audit an existing checkpoint on one manifest split"
    )
    predict_split.add_argument("checkpoint", type=Path)
    predict_split.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    predict_split.add_argument("--split", choices=("train", "validation", "test"), required=True)
    predict_split.add_argument("--output", type=Path, required=True)
    predict_split.add_argument(
        "--fusion-mode",
        choices=("quality_gated", "quality_concat", "equal", "visual_only", "physiology_only"),
        default=None,
    )

    export = commands.add_parser("export", help="export a trained checkpoint to ONNX")
    export.add_argument("checkpoint", type=Path)
    export.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    export.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/models/helmx_drowsiness.onnx"),
    )

    mrl = commands.add_parser("index-mrl", help="build a subject-fold MRL Eye index")
    mrl.add_argument("root", type=Path)
    mrl.add_argument("output", type=Path)
    mrl.add_argument("--folds", type=int, default=5)

    eye = commands.add_parser("pretrain-eye", help="pretrain the visual backbone on MRL Eye")
    eye.add_argument("index", type=Path)
    eye.add_argument("root", type=Path)
    eye.add_argument("--output", type=Path, default=Path("runs/mrl-eye"))
    eye.add_argument("--epochs", type=int, default=20)
    eye.add_argument("--batch-size", type=int, default=128)

    uta = commands.add_parser("preprocess-uta", help="preprocess official UTA-RLDD folds")
    uta.add_argument("root", type=Path)
    uta.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    uta.add_argument("--output", type=Path, default=Path("data/processed/uta-rldd"))
    uta.add_argument("--test-fold", type=int, required=True)
    uta.add_argument("--validation-fold", type=int, required=True)
    uta.add_argument(
        "--face-landmarker",
        type=Path,
        default=Path("artifacts/models/face_landmarker.task"),
    )

    eye_region = commands.add_parser(
        "derive-eye-region", help="derive resumable grayscale eye-band NPZ windows"
    )
    eye_region.add_argument("manifest", type=Path)
    eye_region.add_argument("output", type=Path)

    dual_eye = commands.add_parser(
        "derive-dual-eye", help="derive resumable packed dual-single-eye NPZ windows"
    )
    dual_eye.add_argument("manifest", type=Path)
    dual_eye.add_argument("output", type=Path)

    label_confidence = commands.add_parser(
        "apply-label-confidence",
        help="add a tercile-position label_confidence column for one clip-level class",
    )
    label_confidence.add_argument("manifest", type=Path)
    label_confidence.add_argument("output", type=Path)
    label_confidence.add_argument("--down-weighted-label", type=int, required=True)
    label_confidence.add_argument(
        "--adaptive",
        action="store_true",
        help="only down-weight videos whose cached PERCLOS shows late>early drift",
    )
    label_confidence.add_argument("--minimum-drift", type=float, default=0.0)

    temporal_audit = commands.add_parser(
        "temporal-label-audit",
        help="audit train/validation clip labels against within-video evidence",
    )
    temporal_audit.add_argument("manifest", type=Path)
    temporal_audit.add_argument("train_predictions", type=Path)
    temporal_audit.add_argument("validation_predictions", type=Path)
    temporal_audit.add_argument("output", type=Path)

    multifold = commands.add_parser(
        "evaluate-multifold-screen",
        help="evaluate frozen paired gates across D2-D5 validation-video predictions",
    )
    multifold.add_argument("root", type=Path)
    multifold.add_argument("--output", type=Path, required=True)
    multifold.add_argument("--candidate", default="ordinal")
    multifold.add_argument("--resamples", type=int, default=2000)
    multifold.add_argument("--seed", type=int, default=2026)

    multifold_audit = commands.add_parser(
        "audit-multifold-screen",
        help="audit paired D2-D5 screening failures without held-out data",
    )
    multifold_audit.add_argument("root", type=Path)
    multifold_audit.add_argument("--output", type=Path, required=True)
    multifold_audit.add_argument("--candidate", default="ordinal")

    baseline_audit = commands.add_parser(
        "audit-multifold-baseline",
        help="audit retained D2-D5 categorical errors without model inference",
    )
    baseline_audit.add_argument("root", type=Path)
    baseline_audit.add_argument("--manifests", type=Path, required=True)
    baseline_audit.add_argument("--output", type=Path, required=True)

    uta_events = commands.add_parser(
        "index-uta-events", help="index raw UTA test videos with neutral calibration paths"
    )
    uta_events.add_argument("root", type=Path)
    uta_events.add_argument("output", type=Path)
    uta_events.add_argument("--test-fold", type=int, required=True)

    extract = commands.add_parser("extract-zip", help="safely extract a downloaded ZIP archive")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)

    pilot = commands.add_parser("convert-frame-pilot", help="convert a frame-only mirror to NPZ")
    pilot.add_argument("root", type=Path)
    pilot.add_argument("--output", type=Path, default=Path("data/processed/uta-rldd-frame-pilot"))

    quality_report = commands.add_parser(
        "data-quality-report",
        help="class-balance and physiology-feature sanity checks for a manifest",
    )
    quality_report.add_argument("manifest", type=Path)
    quality_report.add_argument(
        "--output", type=Path, default=Path("runs/data_quality_report.json")
    )
    quality_report.add_argument("--early-seconds", type=float, default=60.0)

    uta_diagnostics = commands.add_parser(
        "uta-pilot-diagnostics",
        help="inspect five-second blink behavior and physiology outliers without test subjects",
    )
    uta_diagnostics.add_argument("root", type=Path, help="extracted official UTA-RLDD root")
    uta_diagnostics.add_argument("manifest", type=Path, help="preprocessed pilot manifest")
    uta_diagnostics.add_argument(
        "--face-landmarker",
        type=Path,
        default=Path("artifacts/models/face_landmarker.task"),
    )
    uta_diagnostics.add_argument(
        "--output", type=Path, default=Path("runs/uta-rldd-pilot/diagnostics.json")
    )
    uta_diagnostics.add_argument("--sample-fps", type=float, default=8.0)
    uta_diagnostics.add_argument("--diagnostic-seconds", type=float, default=10.0)

    events = commands.add_parser(
        "evaluate-events", help="causally replay full test videos through the alert controller"
    )
    events.add_argument(
        "videos",
        type=Path,
        help="CSV with dataset,subject_id,session_id,path,label columns; path must point at"
        " an original continuous recording, not a preprocessed NPZ window",
    )
    events.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    events.add_argument("--model", type=Path, required=True)
    events.add_argument(
        "--face-landmarker",
        type=Path,
        default=Path("artifacts/models/face_landmarker.task"),
    )
    events.add_argument("--output", type=Path, default=Path("runs/event_study.json"))
    events.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="optional reusable causal inference-trace cache directory",
    )
    events.add_argument("--alert-label", type=int, default=0)
    events.add_argument("--drowsy-label", type=int, default=2)
    events.add_argument("--low-vigilance-label", type=int, default=1)
    events.add_argument("--minimum-quality", type=float, default=0.35)

    tune_events = commands.add_parser(
        "tune-event-thresholds",
        help="select alert thresholds from cached validation-video traces only",
    )
    tune_events.add_argument("cache", type=Path)
    tune_events.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    tune_events.add_argument("--output", type=Path, default=Path("runs/event_threshold_fit.json"))
    tune_events.add_argument("--alert-label", type=int, default=0)
    tune_events.add_argument("--drowsy-label", type=int, default=2)
    tune_events.add_argument("--minimum-quality", type=float, default=0.35)
    tune_events.add_argument("--minimum-warning", type=float, default=0.40)
    tune_events.add_argument("--maximum-warning", type=float, default=0.72)
    tune_events.add_argument("--warning-step", type=float, default=0.02)
    tune_events.add_argument(
        "--warning-durations", type=float, nargs="+", default=None, metavar="SECONDS"
    )

    quantize = commands.add_parser("quantize", help="static-quantize ONNX using training samples")
    quantize.add_argument("model", type=Path)
    quantize.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    quantize.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/models/helmx_drowsiness_int8.onnx"),
    )
    quantize.add_argument("--calibration-samples", type=int, default=256)
    return parser


def run(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    console = Console()
    if args.command == "validate-config":
        config = load_config(args.path)
        payload: dict[str, Any] = {
            "schema_version": config.schema_version,
            "labels": config.data.label_names,
            "backbone": config.model.backbone,
            "fusion_mode": config.model.fusion_mode,
            "seeds": config.training.seeds,
        }
        console.print_json(json.dumps(payload))
        return 0
    if args.command == "validate-manifest":
        from helmx_drowsiness.datasets.manifest import read_manifest, summarize_manifest

        frame = read_manifest(args.path, check_paths=not args.skip_path_check)
        summary = summarize_manifest(frame, root=args.path.parent)
        console.print_json(json.dumps(asdict(summary)))
        return 0
    if args.command == "download-assets":
        path, sha256 = download_face_landmarker(args.face_landmarker)
        console.print_json(json.dumps({"path": str(path), "sha256": sha256}))
        return 0
    if args.command == "run":
        from helmx_drowsiness.runtime.app import run_camera

        run_camera(
            load_config(args.config),
            onnx_model=args.model,
            face_landmarker=args.face_landmarker,
            alarm_path=args.alarm,
            camera=args.camera,
        )
        return 0
    if args.command == "train":
        from helmx_drowsiness.training.run import run_training

        config = load_config(args.config)
        seed = args.seed if args.seed is not None else config.seed
        checkpoint = run_training(
            config,
            config_path=args.config,
            output_dir=args.output,
            seed=seed,
        )
        console.print_json(json.dumps({"best_checkpoint": str(checkpoint)}))
        return 0
    if args.command == "train-all":
        from helmx_drowsiness.training.run import run_all_seeds

        config = load_config(args.config)
        checkpoints = run_all_seeds(
            config,
            config_path=args.config,
            output_dir=args.output,
        )
        console.print_json(json.dumps({"checkpoints": [str(path) for path in checkpoints]}))
        return 0
    if args.command == "predict-split":
        from helmx_drowsiness.training.run import predict_checkpoint_split

        probabilities = predict_checkpoint_split(
            args.checkpoint,
            load_config(args.config),
            args.output,
            split=args.split,
            fusion_mode=args.fusion_mode,
        )
        console.print_json(
            json.dumps(
                {
                    "output": str(args.output),
                    "samples": len(probabilities),
                    "fusion_mode": args.fusion_mode or "configured",
                }
            )
        )
        return 0
    if args.command == "export":
        from helmx_drowsiness.export import export_checkpoint
        from helmx_drowsiness.training.provenance import sha256_file

        destination = export_checkpoint(args.checkpoint, args.output, load_config(args.config))
        console.print_json(
            json.dumps({"onnx_model": str(destination), "sha256": sha256_file(destination)})
        )
        return 0
    if args.command == "index-mrl":
        from helmx_drowsiness.datasets.mrl_eye import build_mrl_index

        frame = build_mrl_index(args.root, args.output, folds=args.folds)
        console.print_json(
            json.dumps(
                {
                    "rows": len(frame),
                    "subjects": int(frame["subject_id"].nunique()),
                    "folds": int(frame["fold"].nunique()),
                    "output": str(args.output),
                }
            )
        )
        return 0
    if args.command == "pretrain-eye":
        from helmx_drowsiness.training.pretrain_eye import pretrain_mrl_eye

        checkpoint = pretrain_mrl_eye(
            args.index,
            args.root,
            args.output,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
        console.print_json(json.dumps({"eye_backbone_checkpoint": str(checkpoint)}))
        return 0
    if args.command == "preprocess-uta":
        from helmx_drowsiness.datasets.uta_rldd import preprocess_uta_rldd

        config = load_config(args.config)
        manifest = preprocess_uta_rldd(
            args.root,
            args.output,
            args.face_landmarker,
            config.data,
            test_fold=args.test_fold,
            validation_fold=args.validation_fold,
        )
        console.print_json(json.dumps({"manifest": str(manifest)}))
        return 0
    if args.command == "derive-eye-region":
        from helmx_drowsiness.datasets.eye_region import derive_eye_region_dataset

        manifest = derive_eye_region_dataset(args.manifest, args.output)
        console.print_json(json.dumps({"manifest": str(manifest)}))
        return 0
    if args.command == "derive-dual-eye":
        from helmx_drowsiness.datasets.eye_region import derive_dual_eye_dataset

        manifest = derive_dual_eye_dataset(args.manifest, args.output)
        console.print_json(json.dumps({"manifest": str(manifest)}))
        return 0
    if args.command == "apply-label-confidence":
        from helmx_drowsiness.datasets.label_confidence import (
            add_adaptive_label_confidence,
            add_label_confidence,
        )
        from helmx_drowsiness.datasets.manifest import read_manifest

        frame = read_manifest(args.manifest, check_paths=False)
        if args.adaptive:
            weighted = add_adaptive_label_confidence(
                frame,
                args.manifest.parent,
                down_weighted_label=args.down_weighted_label,
                minimum_drift=args.minimum_drift,
            )
        else:
            weighted = add_label_confidence(frame, down_weighted_label=args.down_weighted_label)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        weighted.to_csv(args.output, index=False)
        console.print_json(json.dumps({"manifest": str(args.output), "rows": len(weighted)}))
        return 0
    if args.command == "temporal-label-audit":
        from helmx_drowsiness.evaluation.temporal_label_audit import run_temporal_label_audit

        report = run_temporal_label_audit(
            args.manifest,
            args.train_predictions,
            args.validation_predictions,
            args.output,
        )
        console.print_json(json.dumps(report))
        return 0
    if args.command == "evaluate-multifold-screen":
        from helmx_drowsiness.evaluation.multifold_screen import evaluate_multifold_screen

        report = evaluate_multifold_screen(
            args.root,
            args.output,
            candidate_directory=args.candidate,
            resamples=args.resamples,
            seed=args.seed,
        )
        console.print_json(
            json.dumps(
                {
                    "output": str(args.output),
                    "screening_passed": report["screening_passed"],
                    "confirmatory_five_seed_stage_authorized": report[
                        "confirmatory_five_seed_stage_authorized"
                    ],
                }
            )
        )
        return 0
    if args.command == "audit-multifold-screen":
        from helmx_drowsiness.evaluation.multifold_failure_audit import (
            run_multifold_failure_audit,
        )

        report = run_multifold_failure_audit(
            args.root, args.output, candidate_directory=args.candidate
        )
        console.print_json(
            json.dumps(
                {
                    "output": str(args.output),
                    "subjects": report["scope"]["subjects"],
                    "videos": report["scope"]["videos"],
                    "screening_outcome": report["findings"]["screening_outcome"],
                }
            )
        )
        return 0
    if args.command == "audit-multifold-baseline":
        from helmx_drowsiness.evaluation.baseline_failure_audit import (
            run_baseline_failure_audit,
        )

        report = run_baseline_failure_audit(
            args.root,
            args.manifests,
            args.output,
        )
        console.print_json(
            json.dumps(
                {
                    "output": str(args.output),
                    "subjects": report["scope"]["subjects"],
                    "videos": report["scope"]["videos"],
                    "weakest_recall_class": report["findings"]["weakest_recall_class"],
                }
            )
        )
        return 0
    if args.command == "index-uta-events":
        from helmx_drowsiness.datasets.uta_rldd import build_uta_event_index

        index = build_uta_event_index(args.root, args.output, test_fold=args.test_fold)
        console.print_json(json.dumps({"index": str(index)}))
        return 0
    if args.command == "extract-zip":
        from helmx_drowsiness.datasets.archive import safe_extract_zip

        files = safe_extract_zip(args.archive, args.destination)
        console.print_json(json.dumps({"files": len(files), "destination": str(args.destination)}))
        return 0
    if args.command == "convert-frame-pilot":
        from helmx_drowsiness.datasets.image_pilot import convert_frame_pilot

        manifest = convert_frame_pilot(args.root, args.output)
        console.print_json(json.dumps({"manifest": str(manifest)}))
        return 0
    if args.command == "data-quality-report":
        from helmx_drowsiness.datasets.manifest import read_manifest
        from helmx_drowsiness.evaluation.data_quality import (
            manifest_class_balance,
            physiology_feature_report,
        )
        from helmx_drowsiness.training.provenance import write_json

        frame = read_manifest(args.manifest)
        physiology = physiology_feature_report(
            frame, args.manifest.parent, early_seconds=args.early_seconds
        )
        write_json(
            args.output,
            {
                "class_balance": manifest_class_balance(frame),
                "physiology_features": physiology.to_dict(orient="records"),
            },
        )
        console.print_json(json.dumps({"output": str(args.output), "rows": len(frame)}))
        return 0
    if args.command == "uta-pilot-diagnostics":
        from helmx_drowsiness.evaluation.uta_pilot import run_uta_pilot_diagnostics

        report = run_uta_pilot_diagnostics(
            args.root,
            args.manifest,
            args.face_landmarker,
            args.output,
            sample_fps=args.sample_fps,
            diagnostic_seconds=args.diagnostic_seconds,
        )
        console.print_json(
            json.dumps(
                {
                    "output": str(args.output),
                    "subjects": report["scope"]["subjects"],
                    "videos": report["scope"]["videos"],
                    "samples": report["scope"]["samples"],
                }
            )
        )
        return 0
    if args.command == "evaluate-events":
        import pandas as pd

        from helmx_drowsiness.evaluation.causal_harness import run_event_study
        from helmx_drowsiness.training.provenance import write_json

        study = run_event_study(
            pd.read_csv(args.videos),
            config=load_config(args.config),
            onnx_model=args.model,
            face_landmarker=args.face_landmarker,
            alert_label=args.alert_label,
            drowsy_label=args.drowsy_label,
            low_vigilance_label=args.low_vigilance_label,
            minimum_quality=args.minimum_quality,
            cache_dir=(
                args.cache_dir
                if args.cache_dir is not None
                else args.output.parent / f"{args.output.stem}_cache"
            ),
        )
        write_json(args.output, asdict(study))
        console.print_json(
            json.dumps(
                {
                    "videos": study.videos,
                    "event_sensitivity": study.event_sensitivity,
                    "false_alerts_per_hour": study.false_alerts_per_hour,
                    "median_detection_delay_seconds": study.median_detection_delay_seconds,
                    "output": str(args.output),
                }
            )
        )
        return 0
    if args.command == "tune-event-thresholds":
        from helmx_drowsiness.evaluation.causal_harness import (
            load_replay_caches,
            tune_event_thresholds,
        )
        from helmx_drowsiness.training.provenance import write_json

        if args.warning_step <= 0 or args.maximum_warning < args.minimum_warning:
            raise ValueError("warning range requires a positive step and maximum >= minimum")
        count = round((args.maximum_warning - args.minimum_warning) / args.warning_step) + 1
        warning_candidates = [
            round(args.minimum_warning + index * args.warning_step, 10) for index in range(count)
        ]
        config = load_config(args.config)
        fit = tune_event_thresholds(
            load_replay_caches(args.cache),
            config.alert,
            alert_label=args.alert_label,
            drowsy_label=args.drowsy_label,
            warning_candidates=warning_candidates,
            warning_durations=args.warning_durations,
            minimum_quality=args.minimum_quality,
        )
        write_json(args.output, asdict(fit))
        console.print_json(
            json.dumps(
                {
                    "feasible": fit.feasible,
                    "selected": asdict(fit.selected) if fit.selected is not None else None,
                    "criterion": fit.criterion,
                    "output": str(args.output),
                }
            )
        )
        return 0
    if args.command == "quantize":
        from helmx_drowsiness.quantize import quantize_checkpoint_onnx

        destination = quantize_checkpoint_onnx(
            args.model,
            args.output,
            load_config(args.config),
            calibration_samples=args.calibration_samples,
        )
        console.print_json(json.dumps({"quantized_model": str(destination)}))
        return 0
    raise RuntimeError(f"unhandled command: {args.command}")


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
