
J1 — DATA_RDY stationary capture verification and historical polling comparison
Status: COMPLETE (VERIFIED; HISTORICAL COMPARATOR)
UTC: 2026-10-06T15:23:37.724840+00:00
Evidence: piResults/final_pi_review_closure/13_optional_drdy/verification_comparison_20261006
{
  "checks": {
    "frozen_artifacts_unchanged": true,
    "full_twenty_minutes": true,
    "no_capture_exception": true,
    "no_i2c_errors": true,
    "no_edge_timeout": true,
    "raw_rows_match": true,
    "window_rows_match": true,
    "accepted_edges_match": true,
    "edge_counts_match": true,
    "discard_count_matches": true,
    "sample_indices_contiguous": true,
    "sample_times_increasing": true,
    "edge_times_increasing": true,
    "edge_to_sample_alignment": true,
    "registers_restored": true,
    "configuration_correct": true,
    "replay_endpoints_exact": true,
    "replay_scores_exact": true,
    "policy_replay_exact": true
  },
  "comparisons": [
    {
      "label": "DATA_RDY current",
      "source": "piResults/final_pi_review_closure/13_optional_drdy/stationary_20min_20261006",
      "sample_rate_hz": 50.572673315189746,
      "dt_std_ms": 0.7687511158601625,
      "dt_p99_ms": 22.274308879968885,
      "dt_max_ms": 48.763186999849495,
      "V_T": 1.0,
      "C_D": 1.0,
      "survival_90_samples": 1.0,
      "gaps": 0,
      "i2c_errors": 0,
      "processing_p99_ms": 8.485830749889391,
      "cpu_percent_mean": 4.671740958788897,
      "rss_peak_bytes": 53055488,
      "scores": {
        "classifier": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        },
        "reconstruction": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        }
      },
      "events": 0,
      "summary_sha256": "b5e766a75dcd78497c7d35a76f04570c5ca858b96f2ae35174e503d8f43e6e95"
    },
    {
      "label": "A1 polling historical",
      "source": "piResults/final_pi_review_closure/05_corrected_aba/A1_polling",
      "sample_rate_hz": 49.863608091661646,
      "dt_std_ms": 3.1105903414593543,
      "dt_p99_ms": 29.019639049329275,
      "dt_max_ms": 57.648023997899145,
      "V_T": 1.0,
      "C_D": 1.0,
      "survival_90_samples": 1.0,
      "gaps": 0,
      "i2c_errors": 0,
      "processing_p99_ms": 13.268392601457894,
      "cpu_percent_mean": 8.031929233361417,
      "rss_peak_bytes": 52793344,
      "scores": {
        "classifier": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        },
        "reconstruction": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        }
      },
      "events": 0,
      "summary_sha256": "d972bc04f1a6160f1aea7433f11ee34f7dacfc80c40256d55cbce5034304234b"
    },
    {
      "label": "A2 polling historical",
      "source": "piResults/final_pi_review_closure/05_corrected_aba/A2_polling",
      "sample_rate_hz": 49.96325772068787,
      "dt_std_ms": 1.937559030604141,
      "dt_p99_ms": 26.09647359931841,
      "dt_max_ms": 57.912195999961114,
      "V_T": 1.0,
      "C_D": 1.0,
      "survival_90_samples": 1.0,
      "gaps": 0,
      "i2c_errors": 0,
      "processing_p99_ms": 8.963803950573496,
      "cpu_percent_mean": 4.677759056444819,
      "rss_peak_bytes": 53252096,
      "scores": {
        "classifier": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        },
        "reconstruction": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.0,
          "100": 0.0
        }
      },
      "events": 0,
      "summary_sha256": "d33e529d49ae3f2b1b231d22519b60a50a21a774796981502bd5c28a0a0066c4"
    }
  ],
  "kernel_edge_intervals": {
    "n": 60688,
    "mean_ms": 19.773448399370547,
    "median_ms": 19.774477999817464,
    "std_ms": 0.06589132442953746,
    "rms_error_from_20ms": 0.23593917517624058,
    "p90_ms": 19.781366999950478,
    "p95_ms": 19.784127000093576,
    "p99_ms": 19.977443239988585,
    "p99.9_ms": 20.391724812997175,
    "max_ms": 20.84077599988632,
    "histogram_edges_ms": [
      0,
      10,
      15,
      25,
      30,
      40,
      60,
      100,
      "inf"
    ],
    "counts_left_closed_right_open": [
      0,
      0,
      60688,
      0,
      0,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 0,
      "5": 0,
      "8": 0
    }
  },
  "edge_to_host_wake_ms": {
    "50": 0.0889079999524256,
    "95": 0.5245463999926868,
    "99": 2.091129760028713,
    "100": 15.367474999948172
  },
  "stale_edges_discarded": 1,
  "source_hashes": {
    "raw_sensor.csv": "855146b6201c826fe36be37cc9410ae3e75a0ff972b1cd49e925e264f6b8d8a3",
    "README.txt": "10c7e1fa62d478be46b3d2587029ce068b2b36197755e1f85b5c2ecc803c92d6",
    "operator_attestation.json": "cc1f2f8ce5fae966a3b59594fe73460814d79b5be822765a96b165a60300b539",
    "window_scores.csv": "afccfdb9368b0de8dbe1284a734b4d944dad9a4cfaad01965bcaa4fc2568c91e",
    "metadata.json": "a041948f6c750cb63d938dbd1f0025c80d50a41215766153b8e94838d91cdd3a",
    "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
    "registers_during.json": "34ba583ca18f98d656bf750bdfe5d5997dedae71bea4a4ed839410407d85702d",
    "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
    "summary.json": "b5e766a75dcd78497c7d35a76f04570c5ca858b96f2ae35174e503d8f43e6e95",
    "resources.json": "8f6bd8805b4f0627c05960fd369b28c08e1aa27908bc697f60f0859170d826e0",
    "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
    "gc_events.json": "3d5f98bc79484737f803ac3e90885b903f269a4fadffdbe5e990d4aadca55999",
    "gpio_edges.csv": "a941e1f1ef1dabd9c1d2626ea49a02da098f2958419b5ef80d5f9f20865079a0"
  },
  "limitations": "Historical polling has matching filter/range/divider and power configuration, but different boot, physical placement, workload and separate-read acquisition. This is a descriptive comparison, not a paired causal estimate of interrupt benefit. GPIO kernel timestamps are not oscilloscope measurements. libgpiod v1 provides no exact overflow count. Host sample coverage denominators use received samples. Physical stationarity is operator-reported. J3 FIFO+DATA_RDY and J2 IIO have not been performed."
}
