
 — 04_polling_fifo_equivalence/polling
Status: PASS (UNATTENDED PHYSICAL CONDITIONS)
UTC: 2026-09-29T19:50:54.722391+00:00
Evidence: piResults/final_pi_review_closure/04_polling_fifo_equivalence/polling
{
  "mode": "polling",
  "seconds_requested": 600.0,
  "elapsed_s": 600.0098899549994,
  "samples": 30000,
  "achieved_samples_per_s": 49.99917585066805,
  "filtered": true,
  "high_range": false,
  "i2c_errors": 0,
  "overflows": 0,
  "exception": null,
  "raw": {
    "ax": {
      "mean": 2363.8973,
      "std": 19.1897599266727,
      "rms": 2363.9751884978264,
      "min": 2233.0,
      "max": 2478.0,
      "p1": 2319.0,
      "p50": 2364.0,
      "p99": 2410.0,
      "negative_rail": 0,
      "positive_rail": 0
    },
    "ay": {
      "mean": -1555.1089333333334,
      "std": 16.07022298732106,
      "rms": 1555.1919645497144,
      "min": -1710.0,
      "max": -1404.0,
      "p1": -1592.0,
      "p50": -1555.0,
      "p99": -1517.0,
      "negative_rail": 0,
      "positive_rail": 0
    },
    "az": {
      "mean": -16084.697133333333,
      "std": 23.708988558116285,
      "rms": 16084.714606955262,
      "min": -16248.0,
      "max": -15562.0,
      "p1": -16139.0,
      "p50": -16085.0,
      "p99": -16030.0,
      "negative_rail": 0,
      "positive_rail": 0
    },
    "gx": {
      "mean": -18.201066666666666,
      "std": 10.002331671276563,
      "rms": 20.768376601618787,
      "min": -90.0,
      "max": 57.0,
      "p1": -42.0,
      "p50": -18.0,
      "p99": 5.0,
      "negative_rail": 0,
      "positive_rail": 0
    },
    "gy": {
      "mean": 280.7293,
      "std": 18.525300398194176,
      "rms": 281.3398774317877,
      "min": 190.0,
      "max": 422.0,
      "p1": 236.0,
      "p50": 281.0,
      "p99": 324.0,
      "negative_rail": 0,
      "positive_rail": 0
    },
    "gz": {
      "mean": 148.43203333333332,
      "std": 43.89581506854864,
      "rms": 154.7866631851724,
      "min": -172.0,
      "max": 496.0,
      "p1": 37.99000000000001,
      "p50": 148.0,
      "p99": 261.0,
      "negative_rail": 0,
      "positive_rail": 0
    }
  },
  "physical": {
    "ax": {
      "mean": 1.4149117100247193,
      "std": 0.011486038768609914,
      "rms": 1.41495833021742,
      "min": 1.3365630767822265,
      "max": 1.4832079284667967,
      "p1": 1.3880384124755858,
      "p50": 1.4149731811523436,
      "p99": 1.4425065002441406
    },
    "ay": {
      "mean": -0.9308110974776204,
      "std": 0.009618838638831301,
      "rms": 0.9308607958466464,
      "min": -1.0235212097167967,
      "max": -0.8403647827148437,
      "p1": -0.9528922607421875,
      "p50": -0.9307458953857422,
      "p99": -0.9080009796142577
    },
    "az": {
      "mean": -9.627502144934285,
      "std": 0.014191024941616882,
      "rms": 9.627512603777943,
      "min": -9.725247143554688,
      "max": -9.31464155883789,
      "p1": -9.66000514831543,
      "p50": -9.627683425903319,
      "p99": -9.59476315307617
    },
    "gx": {
      "mean": -0.13893944020356236,
      "std": 0.07635367687997377,
      "rms": 0.1585372259665556,
      "min": -0.6870229007633587,
      "max": 0.4351145038167939,
      "p1": -0.32061068702290074,
      "p50": -0.13740458015267176,
      "p99": 0.03816793893129771
    },
    "gy": {
      "mean": 2.1429717557251906,
      "std": 0.1414145068564441,
      "rms": 2.147632652151051,
      "min": 1.450381679389313,
      "max": 3.2213740458015265,
      "p1": 1.8015267175572518,
      "p50": 2.145038167938931,
      "p99": 2.4732824427480917
    },
    "gz": {
      "mean": 1.1330689567430026,
      "std": 0.3350825577751805,
      "rms": 1.1815775815662013,
      "min": -1.3129770992366412,
      "max": 3.7862595419847325,
      "p1": 0.29000000000000004,
      "p50": 1.129770992366412,
      "p99": 1.9923664122137403
    }
  },
  "accel_magnitude": {
    "mean": 9.775346973365215,
    "std": 0.014120329973765486,
    "rms": 9.77535717165358,
    "min": 9.458664421382709,
    "max": 9.875641667987404,
    "p1": 9.743063010167464,
    "p50": 9.775360979072996,
    "p99": 9.80771326329872
  },
  "gyro_magnitude": {
    "mean": 2.450606456239405,
    "std": 0.16767122144275723,
    "rms": 2.4563358161827877,
    "min": 1.5150893044601306,
    "max": 4.489951486956629,
    "p1": 2.087558355869462,
    "p50": 2.440737483544693,
    "p99": 2.9247298382999296
  },
  "timestamp_note": "Host read completion times, not physical sample timestamps. FIFO batch samples share host time; never interpret those intervals as sensor dt.",
  "conditions": "Unattended; no physical mounting/stationarity confirmation from user. No inference, GPIO, or SMS.",
  "configuration_note": "Filtered 50-Hz ODR changes CONFIG/ACCEL_CONFIG2/SMPLRT_DIV from deployment. Polling equivalence must use these SAME settings.",
  "stationary_physical_plausibility_gate": true
}
