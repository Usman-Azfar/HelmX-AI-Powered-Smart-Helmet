
 — Saved capture verification
Status: PASS
UTC: 2026-10-06T20:48:49.592605+00:00
Evidence: piResults/final_pi_review_closure/14_fifo_drdy/smoke_20261007_verification
{
  "label": "14_fifo_drdy/smoke_20261007",
  "checks": {
    "frozen_artifacts_unchanged": true,
    "full_duration": true,
    "no_exception": true,
    "no_i2c_errors": true,
    "raw_rows_match": true,
    "window_rows_match": true,
    "nonempty": true,
    "indices_contiguous": true,
    "times_nondecreasing": true,
    "registers_restored": true,
    "replay_endpoints_exact": true,
    "replay_scores_exact": true,
    "replay_policy_exact": true,
    "gap_count_matches": true,
    "no_overflow": true,
    "no_edge_timeout": true,
    "edge_rows_match": true,
    "fifo_packet_accounting": true,
    "fifo_raw_decode_exact": true,
    "fifo_host_times_exact": true,
    "fifo_configuration_correct": true
  },
  "metrics": {
    "mode": "fifo-drdy",
    "elapsed_s": 30.009964914000193,
    "sample_rate_hz": 50.61652035758826,
    "n_samples": 1519,
    "n_windows": 98,
    "gap_count": 0,
    "C_D": 1.0,
    "V_T_scored_over_scored_plus_resets": 1.0,
    "p_valid_90_sample_position": 1.0,
    "timing": {
      "n": 1518,
      "mean_ms": 19.767169488800818,
      "median_ms": 19.774679500642378,
      "std_ms": 2.086701238048698,
      "rms_error_from_20ms": 2.0996504718212603,
      "p90_ms": 21.68534800021007,
      "p95_ms": 22.947704100033658,
      "p99_ms": 25.931334960150703,
      "p99.9_ms": 30.584121497366553,
      "max_ms": 32.0065309997517,
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
        5,
        24,
        1464,
        23,
        2,
        0,
        0,
        0
      ],
      "deviation_counts": {
        "2": 290,
        "5": 54,
        "8": 16
      }
    },
    "processing_ms": {
      "0": 1.6367679991162731,
      "50": 2.6307010007258214,
      "95": 9.2047430994171,
      "99": 11.929510989884877,
      "99.9": 13.440004398677058,
      "100": 13.607836999653955
    },
    "i2c_failures": 0,
    "confirmed_alert_events": 0,
    "score_distributions": {
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
    "physical_axes": {
      "ax": {
        "mean": -5.842153099179597,
        "std": 0.008525828096664297,
        "min": -5.869385369873046,
        "max": -5.816712933349609,
        "rms": 5.842159320319714
      },
      "ay": {
        "mean": -0.7776750001406338,
        "std": 0.01014457681832138,
        "min": -0.8224082702636718,
        "max": -0.7254431030273437,
        "rms": 0.7777411640658849
      },
      "az": {
        "mean": -7.789021664063062,
        "std": 0.01388503393972455,
        "min": -7.831433630371094,
        "max": -7.740453967285156,
        "rms": 7.789034040072698
      },
      "gx": {
        "mean": -0.2097955163350738,
        "std": 0.03295099421906862,
        "min": -0.3129770992366412,
        "max": -0.09923664122137404,
        "rms": 0.21236743322441248
      },
      "gy": {
        "mean": 2.0959047987577204,
        "std": 0.12435385230773838,
        "min": 1.4809160305343512,
        "max": 2.6564885496183206,
        "rms": 2.099590628203368
      },
      "gz": {
        "mean": 1.0609782450286196,
        "std": 0.0341798748504972,
        "min": 0.8091603053435115,
        "max": 1.1908396946564885,
        "rms": 1.0615286620100304
      }
    },
    "resources": {
      "cpu_pct": {
        "min": 6.0,
        "max": 28.9,
        "mean": 9.149999999999999
      },
      "rss_bytes": {
        "min": 50262016,
        "max": 51179520,
        "mean": 50975539.2
      },
      "cpu_temp_c": {
        "min": 47.225,
        "max": 51.121,
        "mean": 49.156766666666655
      }
    }
  },
  "source_hashes": {
    "raw_sensor.csv": "c23cfa6972e556fd9976e10db2063a1f62bc6d4b13ed5228f1f98276f348905e",
    "README.txt": "4fff897c823539049b30378973ae16aa579c05a7d2a8118edc8e06ceccf0e6bc",
    "window_scores.csv": "0dc69f41cb53b83bc42fd4d28e7c82e5f2cbe5fccabbeff5ff57f3b4f29a691d",
    "metadata.json": "8a8ba12ee290bfc26d1d0ead8c35f7a83cf0b2202ee1800abec910db88cb6b38",
    "fifo_batches.json": "eb88661ecb10a7d6ef2e44c5008460649686026a92f96d7921b64baf46d2bd6f",
    "registers_during.json": "7b1cdbbe859f551d0495ea71fbb12fb9596d46dc39e62c91759016bae65a51b6",
    "registers_restored.json": "1c82b166dd54a26a4d5a4115dfd6d614a1e3933621cbea008db05e313ec65d71",
    "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
    "summary.json": "5c1ccec2e153ff30993e406d9f0cec329b39327d7165655bc8551a2f1676e5a9",
    "resources.json": "3b113c541144907e9c5ff574b853fe98d9bb00bee80bf197c5a897cec1a6f251",
    "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
    "gc_events.json": "ad94345ec1f7f1c84e2a85cc14c679b79124b4208a4c49860245c7af1c96abd0",
    "gpio_edges.csv": "50aff5cf3898573a9d5abe97f4cef9136634146baa947d54bc816fde653f8289"
  },
  "scope": "Offline replay and byte integrity. FIFO shared host times are not physical sample jitter. Physical conditions require operator attestation."
}
