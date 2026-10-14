# Frozen hypothesis: tercile-position label-confidence loss weighting

Status: **formally rejected after D2-D5 screening (both blanket and per-video-adaptive
variants)** on 2026-09-22.

This is a candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes one
training factor: the per-window weight of the classification loss for drowsy-labelled UTA-RLDD
windows. The cached windows, labels, preprocessing, augmentation, architecture, quality gate,
categorical objective, MRL initialization, optimizer, learning rates, stopping, video pooling,
calibration, and inference remain unchanged. Fold 1 and DROZY are excluded and prohibited.

## Development-only rationale

UTA-RLDD assigns one label to an entire ~10-minute recording. The prior development-only temporal
label audit (`docs/RESEARCH_PROTOCOL.md`) found window-level macro-F1 rises monotonically from the
early to the late third of drowsy clips (0.36634 -> 0.40005 -> 0.44763 on fold 2), and only 5-10 of
12 drowsy videos show the expected paired late-greater-than-early physiological drift. This is
evidence that early windows inside a drowsy-labelled video frequently still look alert, injecting
label noise into every window-level training signal used so far. The video-level MIL candidate
(`docs/RESEARCH_PROTOCOL.md`) attempted to address this by supervising at the video level instead
of the window level; it passed its own fold-2 gate but collapsed on the authorized fold-1
confirmation (test-minus-validation shift -0.18503) and was rejected as not generalizing.

The new hypothesis: rather than relabeling ambiguous early windows (wrong for the videos that are
drowsy throughout) or aggregating to video level (already rejected), down-weight each drowsy-video
window's contribution to the classification loss by its position within the clip, leaving alert and
low-vigilance windows untouched since the audit evidence does not support down-weighting them.

## Exact one-factor intervention

Added `datasets/label_confidence.py::add_label_confidence`, applied once per fold as an offline
manifest transform (`apply-label-confidence` CLI command) producing
`manifest_development_validation{2..5}_label_confidence.csv` alongside the existing development
manifests, referencing the same cached NPZ windows. For a video labelled `drowsy` (class 2), each
window's `label_confidence` is set by its temporal tercile within that video (same tercile split
already used for video-bag window selection in `datasets.sequences.VideoBagDataset`):

```text
progress <= 1/3  -> 0.5
1/3 < progress <= 2/3 -> 0.75
progress > 2/3   -> 1.0
```

Alert and low-vigilance windows keep `label_confidence = 1.0`. `SequenceDataset` reads this column
as `sample_weight`; `MultiTaskLoss.classification_loss` takes an optional per-sample weight and
reduces to the exact unweighted mean when every weight is 1.0 (verified by test). No other loss
term, architecture, optimizer, or schedule changed. D2-D5 candidate configs
(`configs/uta-multifold-d{2..5}-label-confidence.yaml`) are mechanically identical to their
categorical counterparts except for `data.manifest`.

## Matched evaluation

Reused the completed categorical seed-13 D2-D5 runs as frozen matched baselines. Trained the
label-confidence candidate once per D2-D5 rotation with `evaluate_multifold_screen`
(`candidate_directory="label_confidence"`), the same tool and gates used for every prior candidate.

## D2-D5 screening result (2026-09-21)

| Fold | Baseline macro-F1 | Candidate macro-F1 | Difference | Win |
|---|---|---|---|---|
| D2 | 0.58385 | 0.64124 | **+0.05739** | yes |
| D3 | 0.68498 | 0.63875 | -0.04623 | no |
| D4 | 0.66325 | 0.63986 | -0.02339 | no |
| D5 | 0.61031 | 0.61031 | 0.00000 | no |

Pooled (146 out-of-fold videos, 48 subjects): baseline macro-F1 0.64212, candidate macro-F1
0.63623, difference -0.00589. Paired 2,000-resample subject-clustered 95% interval:
[-0.03578, +0.02478].

Gate results, from `runs/uta-multifold-screen/label_confidence_screening_gate_report.json`:

1. Wins at least 3 of 4 folds: **failed** (1/4).
2. Pooled macro-F1 improvement >= 0.020: **failed** (-0.00589).
3. No fold worse than -0.020: **failed** (D3 at -0.04623).
4. Paired subject-bootstrap 95% lower bound > 0: **failed** (-0.03578).

All four gates fail. `screening_passed` and `confirmatory_five_seed_stage_authorized` are false.
D2's large single-fold gain does not generalize: D3 and D4 regress, and D5 is unchanged, so the
pooled effect is a small net loss. Fold 1, five-seed confirmation, and DROZY remain locked. The
candidate is archived; further training requires a new development-only one-factor hypothesis
documented and frozen before implementation.

## Second attempt: per-video drift-gated adaptive weighting (2026-09-22)

The blanket variant applies the tercile down-weight to every drowsy video uniformly, even though
the audit found only 5-10 of 12 drowsy videos actually show the late-greater-than-early drift. A
second, more targeted candidate was implemented to test whether that mismatch explained D3/D4's
regressions: `datasets.label_confidence.compute_drift_flags` loads each drowsy video's own cached
PERCLOS feature (index 2 of the 12-dimensional physiology vector), computes
`mean(late-third PERCLOS) - mean(early-third PERCLOS)`, and only applies tercile weighting to
windows of videos whose measured drift exceeds `minimum_drift = 0.05` (a 5-percentage-point
late-minus-early PERCLOS increase). Across the pooled 48-subject development set this flagged 22 of
50 drowsy videos (44%) as "ramping," close to the audit's original ratio, versus every drowsy video
under the blanket variant.

`configs/uta-multifold-d{2..5}-adaptive-label-confidence.yaml` and manifests
`manifest_development_validation{2..5}_adaptive_label_confidence.csv` were generated via
`helmx-drowsiness apply-label-confidence --adaptive --minimum-drift 0.05`. Results from
`runs/uta-multifold-screen/adaptive_label_confidence_screening_gate_report.json`:

| Fold | Baseline macro-F1 | Candidate macro-F1 | Difference | Win |
|---|---|---|---|---|
| D2 | 0.58385 | 0.63492 | +0.05107 | yes |
| D3 | 0.68498 | 0.62112 | **-0.06386** | no |
| D4 | 0.66325 | 0.62661 | -0.03664 | no |
| D5 | 0.61031 | 0.61031 | 0.00000 | no |

Pooled: baseline 0.64212, candidate 0.63176, difference -0.01036 (worse than the blanket variant's
-0.00589). Paired 95% interval [-0.04697, +0.02511] with lower bound below zero. All four gates
fail again, and D3's regression is larger than under the blanket variant (-0.06386 vs -0.04623),
despite down-weighting fewer than half as many videos there. This rules out "the blanket assumption
mis-targets some videos" as the explanation for D3/D4's losses: even a version that only touches
windows with directly measured physiological evidence for the down-weight still loses on the same
two folds by a similar or larger margin. D2's win is essentially unchanged in size in both variants.

## Interpretation

This is the sixth and seventh one-factor candidates rejected under this protocol (after ordinal,
hybrid, quality-concat fusion, frozen visual backbone, and subject-class-balanced sampling), and the
second and third independently designed attempts to correct for UTA-RLDD's clip-level label noise
after the earlier-rejected video-level MIL candidate. All three now fail to generalize across
held-out subjects. Making the down-weighting evidence-gated per video (rather than blanket) did not
change the outcome or which folds lose, which is a stronger negative signal than a single rejected
variant: it suggests D3 and D4 are not being hurt by *mistargeted* down-weighting, but by *any*
reduction in effective drowsy-class training signal on those particular subject rotations,
regardless of which windows are touched or how the decision to touch them is justified. Combined
with the earlier rejections, this strengthens the case that the low event-level sensitivity
documented for the pilot checkpoint reflects a genuine, hard-to-remove property of clip-level
UTA-RLDD annotation and this fold structure, rather than a fixable modeling or weighting choice, and
should be reported as a documented limitation rather than treated as an open bug.
