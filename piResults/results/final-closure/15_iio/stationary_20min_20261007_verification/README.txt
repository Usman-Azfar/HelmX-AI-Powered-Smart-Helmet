
 — Saved capture verification
Status: PASS
UTC: 2026-10-07T04:51:25.454903+00:00
Evidence: piResults/final_pi_review_closure/15_iio/stationary_20min_20261007_verification
{
  "label": "15_iio/stationary_20min_20261007",
  "checks": {
    "frozen_artifacts_unchanged": true,
    "full_duration": true,
    "no_exception": true,
    "raw_rows_match": true,
    "window_rows_match": true,
    "nonempty": true,
    "indices_contiguous": true,
    "times_nondecreasing": true,
    "registers_restored": true,
    "cleanup_success": true,
    "replay_endpoints_exact": true,
    "replay_scores_exact": true,
    "replay_policy_exact": true,
    "gap_count_matches": true,
    "iio_complete_records": true,
    "iio_record_count": true,
    "iio_raw_decode_exact": true,
    "iio_timestamp_decode_exact": true,
    "iio_rate_configured": true
  },
  "metrics": {
    "mode": "iio",
    "elapsed_s": 1200.0044833249995,
    "sample_rate_hz": 50.035646394946376,
    "n_samples": 60043,
    "n_windows": 3999,
    "gap_count": 0,
    "C_D": 1.0,
    "V_T_scored_over_scored_plus_resets": 1.0,
    "p_valid_90_sample_position": 1.0,
    "timing": {
      "n": 60042,
      "mean_ms": 19.985975860564274,
      "median_ms": 19.98594000178855,
      "std_ms": 0.020706682714117228,
      "rms_error_from_20ms": 0.02500886234789154,
      "p90_ms": 19.986639999842737,
      "p95_ms": 19.997739997052122,
      "p99_ms": 20.00026000016078,
      "p99.9_ms": 20.01967294119823,
      "max_ms": 20.400000001245644,
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
        60042,
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
    "processing_ms": {
      "50": 2.4061570074991323,
      "95": 8.263435695698718,
      "99": 15.278337101044599,
      "100": 36.291153002821375
    },
    "i2c_failures": null,
    "confirmed_alert_events": 0,
    "score_distributions": {
      "classifier": {
        "0": 0.0,
        "50": 0.0,
        "95": 0.0,
        "99": 0.0,
        "100": 0.0
      },
      "reconstruction": {
        "0": 0.0,
        "50": 0.0,
        "95": 0.0,
        "99": 0.0,
        "100": 0.0
      }
    },
    "physical_axes": {
      "ax": {
        "mean": -5.829150722848625,
        "std": 0.008204900823988335,
        "min": -5.862792,
        "max": -5.7916300000000005
      },
      "ay": {
        "mean": -0.8133848638808853,
        "std": 0.008251144043613262,
        "min": -0.883246,
        "max": -0.749294
      },
      "az": {
        "mean": -7.771637261096215,
        "std": 0.013222072701205357,
        "min": -7.826026,
        "max": -7.709416
      },
      "gx": {
        "mean": -2.506909232735851,
        "std": 0.03175428658944441,
        "min": -2.7146763251610206,
        "max": -2.379154532163591
      },
      "gy": {
        "mean": 0.12601060172823664,
        "std": 0.1312469701896051,
        "min": -0.907433940152139,
        "max": 1.1743262754910033
      },
      "gz": {
        "mean": 2.22632737882886,
        "std": 0.032756312177184464,
        "min": 2.081760215643142,
        "max": 2.371529036868195
      }
    },
    "resources": {
      "cpu_pct": {
        "min": 2.0,
        "max": 7.9,
        "mean": 4.468331922099915
      },
      "rss_bytes": {
        "min": 49754112,
        "max": 52252672,
        "mean": 51514857.889923796
      },
      "cpu_temp_c": {
        "min": 45.764,
        "max": 52.095,
        "mean": 47.96354106689246
      }
    }
  },
  "source_hashes": {
    "raw_sensor.csv": "c5feee0f69767b788131d672d35ed6aae4ce46e417627affb742710ffe77861d",
    "README.txt": "ef67443319f34b94a9c7909ad550a520ad73c1d773f899c132aeab3614b659ce",
    "window_scores.csv": "2f95fde1ff41fa1179f310acc06ec3aa695d784c3725eb3d3552db7a5d6d2a09",
    "metadata.json": "c9de5471fbcf8b7ce57cb3e3ca0530bbc3b0b80abd801b7d78cc89c333608c5c",
    "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "iio_configuration.json": "fcbf2ea159cecd41b8d8c1f6f3183ab78d168013d8ed9797c0520babcef0d4f9",
    "iio_buffer.bin": "1c529a6ade0a3bc475bbb2a3cb8db7b7c7ea7402e151360baa71c04afa7f0660",
    "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
    "summary.json": "1101871998c0cf4082bd01b9171a53e12c06b7486b5381c7b7588fa60b9d5d64",
    "resources.json": "636935851edfe81e454e4f9be850862406d4f73a75b8672d49396a11d264d565"
  },
  "scope": "Offline replay and byte integrity. FIFO shared host times are not physical sample jitter. Physical conditions require operator attestation."
}
