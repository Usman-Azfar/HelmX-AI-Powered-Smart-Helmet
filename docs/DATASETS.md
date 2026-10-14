# Dataset strategy

HelmX does not redistribute third-party data. Raw data belongs under `data/raw/`, which is
ignored by Git. Every experiment must retain the provider's original labels and subject/session
identifiers in the canonical manifest.

## Primary temporal datasets

| Dataset | Intended role | Important protocol |
|---|---|---|
| [UTA-RLDD](https://sites.google.com/view/utarldd/home) | Main three-stage benchmark: alert, low vigilance, drowsy | Use the official five subject folds; never split frames or clips randomly. The storage-bounded preprocessor uses sparse windows and resumable records. |
| [NTHU-DDD](https://cv.cs.nthu.edu.tw/php/callforpaper/datasets/DDD/) | Day/night, glasses, sunglasses, pose, simulated drowsy-behavior robustness | Academic access is required. Keep subjects disjoint and report scenario-specific results. |
| [DROZY](https://www.drozy.uliege.be/) | Frozen primary independent confirmation: NIR with KSS/PVT/PSG | Follow `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`; research/evaluation only, never redistributed, trained on, or target-calibrated. |
| [DMD](https://dmd.vicomtech.org/) | Real-car, multi-view external validation | The 2026 public revision is RGB-only and has a reduced subject set. Use only the currently licensed material. |

## Auxiliary behavior datasets

| Dataset | Intended role | Restriction |
|---|---|---|
| [MRL Eye](https://mrl.cs.vsb.cz/eyedataset.html) | Eye-state auxiliary pretraining under IR, reflections, glasses, and poor illumination | Split by the 37 subject IDs, not by images. It is not a drowsiness benchmark. |
| [YawDD](https://qualinet.github.io/databases/video/yawdd_a_yawning_detection_dataset/) | Yawn/talking auxiliary pretraining | Split by participant/video. It is not a drowsiness benchmark. |

Auxiliary behavior data may supervise the eye/yawn heads, but its labels must never be relabeled
as clip-level drowsiness. This distinction prevents an easy eye-state classifier from being
misreported as a driver-state detector.

## Frame-mirror pilot restriction

`configs/pilot.yaml` exists only to exercise the complete download-to-export pipeline on a
third-party frame mirror. Inspection of the downloaded archive found 11,787 JPG files with only
`active` and `fatigue` labels; this is not the official three-stage label schema. The mirror also
lacks provider-verifiable subject/session identities and temporal continuity. Its split metrics
cannot support a paper, cannot be compared with the official UTA-RLDD five-fold protocol, and must
always be labeled as binary engineering-pilot results.

## HelmX motorcycle data required for publication

Public datasets predominantly use car/simulator camera geometry. A publication claiming
motorcycle or in-helmet robustness needs a prospectively designed HelmX dataset with:

- informed consent and institutional ethics review where required;
- subject-independent rider IDs and immutable session IDs;
- RGB and IR/night sessions from the actual helmet camera position;
- clear metadata for glasses, visor state, illumination, skin tone, head pose, and occlusion;
- alertness ground truth stronger than acted eye closure—ideally repeated KSS plus PVT or an
  appropriate physiological reference;
- safe stationary/simulator collection for drowsy states; never induce drowsiness during road use;
- timestamped failure/obstruction labels and hard negatives such as bumps, talking, checking
  mirrors, and deliberate long blinks.

## Evaluation partitions

1. In-dataset subject-disjoint cross-validation using each dataset's official protocol.
2. Leave-one-dataset-out evaluation without threshold tuning on the target dataset.
3. HelmX external test set frozen before final model selection.
4. Separate RGB-day, RGB-night, IR, glasses, visor, pose, and detection-failure slices.
5. No test-set use for augmentation choice, calibration fitting, early stopping, or thresholds.

UTA-RLDD fold 1 was consumed by the preregistered MIL confirmation on 2026-09-06 and is no longer
an untouched selection resource. New hypotheses use four-fold development over UTA folds 2-5 and,
only after passing that protocol, one locked evaluation on DROZY. See
`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md` for the frozen rotations, gates, KSS mapping, license
constraints, and external endpoints.
