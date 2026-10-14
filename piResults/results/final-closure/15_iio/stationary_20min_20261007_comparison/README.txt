
J2 — J2 acquisition extension comparison
Status: COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED)
UTC: 2026-10-07T04:56:28.082044+00:00
Evidence: piResults/final_pi_review_closure/15_iio/stationary_20min_20261007_comparison
{
  "id": "J2",
  "verification": "15_iio/stationary_20min_20261007_verification",
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
  "comparisons": [
    {
      "condition": "Current J2",
      "source": "15_iio/stationary_20min_20261007",
      "n_samples": 60043,
      "n_windows": 3999,
      "duration_s": 1200.0044833249995,
      "sample_rate_hz": 50.035646394946376,
      "gaps": 0,
      "gaps_per_min": 0.0,
      "C_D": 1.0,
      "V_T": 1.0,
      "survival_90": 1.0,
      "dt_p99_ms": 20.00026000016078,
      "dt_max_ms": 20.400000001245644,
      "processing_p99_ms": 15.278337101044599,
      "i2c_failures": null,
      "events": 0,
      "cpu_mean_pct": 4.4683319220998845,
      "rss_max_bytes": 52252672,
      "cpu_temp_max_c": 52.095,
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
      "summary_sha256": "1101871998c0cf4082bd01b9171a53e12c06b7486b5381c7b7588fa60b9d5d64"
    },
    {
      "condition": "Historical FIFO",
      "source": "05_corrected_aba/B_fifo",
      "n_samples": 60595,
      "n_windows": 4029,
      "duration_s": 1200.0067377279993,
      "sample_rate_hz": 50.49554981226682,
      "gaps": 2,
      "gaps_per_min": 0.09999943852581927,
      "C_D": 0.9982656095143707,
      "V_T": 0.9995038451997023,
      "survival_90": 0.9970581429940832,
      "dt_p99_ms": 28.019794280771748,
      "dt_max_ms": 157.97823700268054,
      "processing_p99_ms": 13.747696681239164,
      "i2c_failures": 0,
      "events": 0,
      "cpu_mean_pct": 12.590664423885398,
      "rss_max_bytes": 79757312,
      "cpu_temp_max_c": 52.095,
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
          "mean": 1.405104305220987,
          "std": 0.012210480462996037,
          "min": 1.3269862701416015,
          "max": 1.5071499450683592,
          "rms": 1.4051573592959936
        },
        "ay": {
          "mean": -0.9153591639928175,
          "std": 0.010950328848207867,
          "min": -1.0402806213378906,
          "max": -0.8289923248291016,
          "rms": 0.9154246603667139
        },
        "az": {
          "mean": -9.61126543348423,
          "std": 0.015209994783483897,
          "min": -9.853935482788085,
          "max": -9.33978067626953,
          "rms": 9.611277468517393
        },
        "gx": {
          "mean": -0.15723490147638966,
          "std": 0.08811084902780121,
          "min": -0.8396946564885496,
          "max": 0.47328244274809156,
          "rms": 0.18023966255707966
        },
        "gy": {
          "mean": 2.1594067482201,
          "std": 0.1605610302630365,
          "min": 1.1068702290076335,
          "max": 3.5038167938931295,
          "rms": 2.1653677167394996
        },
        "gz": {
          "mean": 1.1131780328535912,
          "std": 0.31906234528471855,
          "min": -1.3511450381679388,
          "max": 4.206106870229007,
          "rms": 1.158000912351271
        }
      },
      "summary_sha256": "b2a52cc8ae15aef16ef6f4d62b41efbe27702a0ce486fecbbaddf3a117512a7b"
    },
    {
      "condition": "Historical DATA_RDY",
      "source": "13_optional_drdy/stationary_20min_20261006",
      "n_samples": 60688,
      "n_windows": 4042,
      "duration_s": 1200.0156610620002,
      "sample_rate_hz": 50.572673315189746,
      "gaps": 0,
      "gaps_per_min": 0.0,
      "C_D": 1.0,
      "V_T": 1.0,
      "survival_90": 1.0,
      "dt_p99_ms": 22.274308879968885,
      "dt_max_ms": 48.763186999849495,
      "processing_p99_ms": 8.485830749889391,
      "i2c_failures": 0,
      "events": 0,
      "cpu_mean_pct": 4.698487394957984,
      "rss_max_bytes": 53055488,
      "cpu_temp_max_c": 51.121,
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
          "mean": -5.8506308132149,
          "std": 0.014471617795802912,
          "min": -6.043563540649414,
          "max": -5.685630392456054,
          "rms": 5.85064871106284
        },
        "ay": {
          "mean": -0.6066206376985167,
          "std": 0.009145240744776637,
          "min": -0.7619546783447265,
          "max": -0.45669396667480466,
          "rms": 0.606689569310397
        },
        "az": {
          "mean": -7.782199830870674,
          "std": 0.015183174904496794,
          "min": -8.009203103637695,
          "max": -7.6285250396728514,
          "rms": 7.78221464214421
        },
        "gx": {
          "mean": -0.21906829676201436,
          "std": 0.0635056526549161,
          "min": -1.6259541984732824,
          "max": 0.9618320610687022,
          "rms": 0.22808745376573622
        },
        "gy": {
          "mean": 2.0828682255178785,
          "std": 0.34922626350761465,
          "min": -3.83206106870229,
          "max": 5.740458015267175,
          "rms": 2.1119420039374863
        },
        "gz": {
          "mean": 1.0924988880682174,
          "std": 0.049455542456978425,
          "min": 0.47328244274809156,
          "max": 1.5572519083969465,
          "rms": 1.093617698791495
        }
      },
      "summary_sha256": "b5e766a75dcd78497c7d35a76f04570c5ca858b96f2ae35174e503d8f43e6e95"
    },
    {
      "condition": "Historical filtered polling",
      "source": "05_corrected_aba/A1_polling",
      "n_samples": 59837,
      "n_windows": 3986,
      "duration_s": 1200.0134424690004,
      "sample_rate_hz": 49.863608091661646,
      "gaps": 0,
      "gaps_per_min": 0.0,
      "C_D": 1.0,
      "V_T": 1.0,
      "survival_90": 1.0,
      "dt_p99_ms": 29.019639049329275,
      "dt_max_ms": 57.648023997899145,
      "processing_p99_ms": 13.268392601457894,
      "i2c_failures": 0,
      "events": 0,
      "cpu_mean_pct": 8.048569023568954,
      "rss_max_bytes": 52793344,
      "cpu_temp_max_c": 51.121,
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
          "mean": 1.4072898652476107,
          "std": 0.01210529980840495,
          "min": 1.2497732666015624,
          "max": 1.5316905120849609,
          "rms": 1.4073419282861184
        },
        "ay": {
          "mean": -0.9151836246067869,
          "std": 0.018833176767998127,
          "min": -1.0726023437499999,
          "max": -0.766743081665039,
          "rms": 0.9153773840857065
        },
        "az": {
          "mean": -9.611623755198101,
          "std": 0.014390816904125478,
          "min": -9.76116016845703,
          "max": -9.387066159057616,
          "rms": 9.611634528377555
        },
        "gx": {
          "mean": -0.1556792900611547,
          "std": 0.11792816043791368,
          "min": -1.9541984732824427,
          "max": 1.9465648854961832,
          "rms": 0.19530256623561157
        },
        "gy": {
          "mean": 2.159229902813585,
          "std": 0.18201668399195936,
          "min": 0.0,
          "max": 3.900763358778626,
          "rms": 2.1668880558200954
        },
        "gz": {
          "mean": 1.1142096333716776,
          "std": 0.34716477757210606,
          "min": -1.5648854961832062,
          "max": 4.374045801526718,
          "rms": 1.1670417686976493
        }
      },
      "summary_sha256": "d972bc04f1a6160f1aea7433f11ee34f7dacfc80c40256d55cbce5034304234b"
    }
  ],
  "operator_attestation": "Untouched throughout confirmed after capture",
  "limits": "Historical comparisons are descriptive, not simultaneous/matched-motion equivalence or causal estimates. Raw binary decoding and model replay are verified independently. FIFO batch timestamps are host availability; IIO timestamps may be driver reconstructed. Do not compare their dt as physical jitter. Kernel I2C error counts are unavailable for IIO. Reported process CPU excludes separate kernel interrupt work. IIO manages sensor clock/filter configuration and uses sysfs scale values; its physical means and rate are not an acquisition-only matched comparison with the older userspace configuration. Desktop/agent and development activity remained active during current extension captures."
}
