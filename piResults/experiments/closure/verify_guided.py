"""Verify saved guided captures and replay their frozen scoring/policy path."""
import csv
import json
import logging
import numpy as np
import pandas as pd
import campaign as c
import crash_monitor as cm


def main():
    initial = json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    if not all(c.sha(c.ROOT/name) == digest for name, digest in initial.items()):
        raise RuntimeError('Frozen artifacts changed; do not interpret replay as equivalent')
    base = c.BASE/'07_high_range_benign_motion'
    plan = json.loads((base/'guided_plan.json').read_text())
    rows = []
    for phase in plan['phases']:
        source = base/phase
        if not (source/'summary.json').exists():
            continue
        summary = json.loads((source/'summary.json').read_text())
        raw = pd.read_csv(source/'raw_sensor.csv', float_precision='round_trip')
        windows = pd.read_csv(source/'window_scores.csv', float_precision='round_trip')
        before = json.loads((source/'registers_before.json').read_text())
        after = json.loads((source/'registers_restored.json').read_text())
        during = json.loads((source/'registers_during.json').read_text())
        fields = ['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2',
                  'FIFO_EN','USER_CTRL','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
        cfg = json.loads((source/'configuration.json').read_text())
        th = cm.load_model_thresholds(cfg)
        scorer = cm.WindowScorer(cfg, cm.CrashModel(
            c.BASE/'frozen/models/helmx_crash_model_int8.tflite',
            c.BASE/'frozen/models/normalizer.npz'), cm.CausalGravityFilter(.3,50))
        guard = cm.SampleStreamGuard(cfg['sensor']['timing_guard'], .02, logging.getLogger('verify'))
        replay = []
        for r in raw.itertuples():
            gap, dt = guard.observe(r.t_monotonic)
            if gap:
                scorer.clear()
                if dt >= guard.long_gap_reset_s:
                    scorer.gravity_filter.reset()
            scorer.append([r.ax_ms2,r.ay_ms2,r.az_ms2,r.gx_dps,r.gy_dps,r.gz_dps])
            result = scorer.try_score()
            if result is not None:
                replay.append([r.sample_idx,result['crash_prob'],result['recon_error']])
        replay = np.asarray(replay).reshape(-1,3)
        policy = cm.TriggerPolicy(*th,3,60)
        decisions = [policy.update(r.crash_prob,r.recon_error,now=r.t_monotonic)
                     for r in windows.itertuples()]
        observed = windows[['crash_prob','recon_error']].to_numpy()
        checks = {
            'sample_rows_match': len(raw) == summary['n_samples'],
            'window_rows_match': len(windows) == summary['n_windows'],
            'full_duration': summary['elapsed_s'] >= summary['seconds_requested'],
            'no_exception': summary['exception'] is None,
            'sample_indices_contiguous': bool(np.array_equal(raw.sample_idx, np.arange(len(raw)))),
            'timestamps_increasing': bool(np.all(np.diff(raw.t_monotonic)>0)),
            'configuration_restored': all(before[k] == after[k] for k in fields),
            'high_range_filtered_readback': all(during[k] == v for k,v in {
                'WHO_AM_I':0x70,'GYRO_CONFIG':24,'ACCEL_CONFIG':24,
                'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19}.items()),
            'replay_endpoint_indices_exact': bool(np.array_equal(replay[:,0],windows.sample_idx)),
            'replay_scores_exact': bool(np.array_equal(replay[:,1:],observed)),
            'replay_policy_exact': bool(np.array_equal(np.asarray(decisions),
                                      windows[['or_positive','confirmed_triggered']].to_numpy())),
            'event_count_matches': int(windows.confirmed_triggered.sum()) == summary['confirmed_alert_events'],
        }
        result = {'phase':phase,'checks':checks,
                  'source_hashes':{name:c.sha(source/name) for name in
                    ['raw_sensor.csv','window_scores.csv','summary.json','metadata.json']},
                  'max_abs_replay_score_error':np.max(abs(replay[:,1:]-observed),axis=0).tolist(),
                  'scope':'Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.'}
        if (source/'movement_cue.json').exists():
            cue = json.loads((source/'movement_cue.json').read_text())['cue_prepared_monotonic']
            result.update(cue_after_first_sample_s=cue-float(raw.t_monotonic.iloc[0]),
                          recorded_time_after_cue_s=float(raw.t_monotonic.iloc[-1])-cue)
        c.finish([], 'C3 saved phase verification: '+phase,
                 'PASS (OFFLINE VERIFICATION)' if all(checks.values()) else 'FAIL — SEE CHECKS',
                 result, base/(phase+'_resume_verification'))
        if not all(checks.values()):
            raise RuntimeError('Verification failed: '+phase)
        rows.append({'phase':phase,'duration_s':summary['elapsed_s'],
                     'samples':len(raw),'windows':len(windows),
                     'classifier_max':float(windows.crash_prob.max()),
                     'reconstruction_max':float(windows.recon_error.max()),
                     'classifier_crossings':summary['classifier_crossings'],
                     'reconstruction_crossings':summary['reconstruction_crossings'],
                     'or_positive_windows':summary['or_positive_windows'],
                     'confirmed_alerts':summary['confirmed_alert_events'],
                     'accel_rail_hits':sum(summary['rail_counts'][a] for a in ['ax','ay','az']),
                     'gyro_rail_hits':sum(summary['rail_counts'][a] for a in ['gx','gy','gz'])})
    out = c.BASE/'guided_motion_progress'
    out.mkdir(exist_ok=True)
    if rows:
        with (out/'benign_motion_partial.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    remaining=[p for p in plan['phases'] if p not in {r['phase'] for r in rows}]
    progress_status = 'PARTIAL — USER PHASES REMAIN' if remaining else 'ALL SAVED PHASES VERIFIED; SEE C3 CLOSURE LIMITATIONS'
    c.finish([], 'C3 saved motion battery progress', progress_status,
             {'verified_phases':rows,'remaining_phases':remaining,
              'interpretation':'No rail hits in these saved high-range phases. Benign-motion policy alerts remain observed; absence of clipping does not imply absence of false alerts. Counts are separate per-phase trials with fresh filter and cooldown state.',
              'donning_limitation':'The donning START cue preceded recorder initialization; complete onset coverage is unproven. Operator reported additional motion after donning.',
              'next_phase':remaining[0] if remaining else None},out)


if __name__ == '__main__':
    main()
