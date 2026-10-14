"""Verify a saved boot baseline without opening hardware or inferring power removal."""
import argparse
import collections
import json
import logging

import numpy as np
import pandas as pd

import campaign as c
import crash_monitor as cm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--boot', type=int, choices=[1, 2, 3, 4], required=True)
    parser.add_argument('--capture', choices=['stationary', 'warm_stationary', 'guided_motion'], default='stationary')
    args = parser.parse_args()
    source = c.BASE / f'boot_repeatability/boot{args.boot}_{args.capture}'
    identity = c.BASE / f'01_identity_three_boots/boot{args.boot}'
    read = lambda path: json.loads(path.read_text())
    hashes = read(c.BASE / 'hashes/initial_artifacts.json')
    if not all(c.sha(c.ROOT / name) == digest for name, digest in hashes.items()):
        raise RuntimeError('Frozen artifacts changed')
    summary = read(source / 'summary.json')
    raw = pd.read_csv(source / 'raw_sensor.csv', float_precision='round_trip')
    windows = pd.read_csv(source / 'window_scores.csv', float_precision='round_trip')
    cfg = read(source / 'configuration.json')
    scorer = cm.WindowScorer(cfg, cm.CrashModel(
        c.BASE / 'frozen/models/helmx_crash_model_int8.tflite',
        c.BASE / 'frozen/models/normalizer.npz'), cm.CausalGravityFilter(.3, 50))
    guard = cm.SampleStreamGuard(cfg['sensor']['timing_guard'], .02, logging.getLogger('boot_verify'))
    replay = []
    for row in raw.itertuples():
        gap, dt = guard.observe(row.t_monotonic)
        if gap:
            scorer.clear()
            if dt >= guard.long_gap_reset_s:
                scorer.gravity_filter.reset()
        scorer.append([row.ax_ms2, row.ay_ms2, row.az_ms2, row.gx_dps, row.gy_dps, row.gz_dps])
        result = scorer.try_score()
        if result is not None:
            replay.append([row.sample_idx, result['crash_prob'], result['recon_error']])
    replay = np.asarray(replay).reshape(-1, 3)
    policy = cm.TriggerPolicy(*cm.load_model_thresholds(cfg), 3, 60)
    decisions = [policy.update(row.crash_prob, row.recon_error, now=row.t_monotonic)
                 for row in windows.itertuples()]
    before = read(source / 'registers_before.json')
    after = read(source / 'registers_restored.json')
    fields = ['SMPLRT_DIV', 'CONFIG', 'GYRO_CONFIG', 'ACCEL_CONFIG', 'ACCEL_CONFIG2',
              'FIFO_EN', 'USER_CTRL', 'INT_ENABLE', 'PWR_MGMT_1', 'PWR_MGMT_2']
    ids = read(identity / 'identity_reads.json')
    ident = read(identity / 'summary.json')
    counts = dict(collections.Counter(hex(row['value']) for row in ids))
    checks = {
        'raw_rows_match': len(raw) == summary['n_samples'],
        'score_rows_match': len(windows) == summary['n_windows'],
        'full_requested_duration': summary['elapsed_s'] >= summary['seconds_requested'],
        'protocol_duration_met': summary['elapsed_s'] >= {'stationary': 300, 'warm_stationary': 600, 'guided_motion': 120}[args.capture],
        'no_exception': summary['exception'] is None,
        'indices_contiguous': bool(np.array_equal(raw.sample_idx, np.arange(len(raw)))),
        'timestamps_increasing': bool(np.all(np.diff(raw.t_monotonic) > 0)),
        'configuration_restored': all(before[k] == after[k] for k in fields),
        'identity_100_reads': len(ids) == 100,
        'identity_counts_match': counts == ident['identity_counts'],
        'identity_baseline_same_boot': ident['boot_id'] == read(source / 'metadata.json')['boot_id'],
        'replay_endpoints_exact': bool(np.array_equal(replay[:, 0], windows.sample_idx)),
        'replay_scores_exact': bool(np.array_equal(replay[:, 1:], windows[['crash_prob', 'recon_error']].to_numpy())),
        'replay_policy_exact': bool(np.array_equal(decisions, windows[['or_positive', 'confirmed_triggered']].to_numpy())),
        'event_count_matches': int(windows.confirmed_triggered.sum()) == summary['confirmed_alert_events'],
    }
    if args.capture == 'warm_stationary':
        checks['warm_start_after_one_hour'] = float(raw.t_monotonic.iloc[0]) >= 3600
    result = {
        'boot': args.boot, 'capture': args.capture, 'checks': checks, 'identity_counts': counts,
        'power_off_seconds_user_reported': ident.get('user_reported_power_off_seconds'),
        'first_sample_uptime_s': float(raw.t_monotonic.iloc[0]),
        'samples': len(raw), 'windows': len(windows),
        'elapsed_s': summary['elapsed_s'], 'sample_rate_hz': summary['sample_rate_hz'],
        'i2c_failures': summary['i2c_failures'], 'gap_count': summary['gap_count'],
        'confirmed_policy_events': summary['confirmed_alert_events'],
        'rail_counts': summary['rail_counts'],
        'source_hashes': {name: c.sha(source / name) for name in
                          ['raw_sensor.csv', 'window_scores.csv', 'summary.json', 'metadata.json']},
        'scope': 'Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage.',
    }
    suffix = {'stationary': 'baseline_review', 'warm_stationary': 'warm_stationary_review', 'guided_motion': 'guided_motion_verification'}[args.capture]
    c.finish([], f'Boot {args.boot} saved {args.capture} verification',
             'PASS (OFFLINE VERIFICATION)' if all(checks.values()) else 'FAIL — SEE CHECKS',
             result, c.BASE / f'boot_repeatability/boot{args.boot}_{suffix}')
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
