"""Reconcile saved boot evidence; never create physical attestations."""
import argparse
import json
import pandas as pd
import campaign as c

BASE = c.BASE / 'boot_repeatability'
AXES = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']

def read(path):
    return json.loads(path.read_text())

def capture(boot, phase):
    source = BASE / f'boot{boot}_{phase}'
    summary = read(source / 'summary.json')
    raw = pd.read_csv(source / 'raw_sensor.csv', float_precision='round_trip')
    scores = pd.read_csv(source / 'window_scores.csv', float_precision='round_trip')
    assert len(raw) == summary['n_samples'] and len(scores) == summary['n_windows']
    assert summary['exception'] is None
    assert summary['elapsed_s'] >= summary['seconds_requested']
    identity = read(c.BASE / f'01_identity_three_boots/boot{boot}/summary.json')
    assert identity['boot_id'] == read(source / 'metadata.json')['boot_id']
    return dict(boot=boot, phase=phase, boot_id=identity['boot_id'],
                first_sample_uptime_s=float(raw.t_monotonic.iloc[0]),
                identity_counts=identity['identity_counts'],
                registers=read(source / 'registers_during.json'),
                source_hashes={p.name:c.sha(p) for p in source.iterdir() if p.is_file()},
                **{key:summary[key] for key in ['elapsed_s','n_samples','n_windows',
                  'sample_rate_hz','timing','physical_axes','score_distributions',
                  'rail_counts','confirmed_alert_events','i2c_failures','gap_count','C_D']})

def warm():
    early, late = capture(4, 'stationary'), capture(4, 'warm_stationary')
    assert early['boot_id'] == late['boot_id'] and late['first_sample_uptime_s'] >= 3600
    confirmation = read(BASE / 'boot4_warm_comparison/summary.json')['operator_confirmation']
    assert confirmation['same_orientation_since_initial_baseline']
    assert confirmation['untouched_throughout_warm_recording']
    rows = []
    for axis in AXES:
        a, b = early['physical_axes'][axis], late['physical_axes'][axis]
        rows.append(dict(axis=axis, units='m/s^2' if axis[0]=='a' else 'deg/s',
                         early_mean=a['mean'], warm_mean=b['mean'],
                         mean_difference=b['mean']-a['mean'], early_std=a['std'],
                         warm_std=b['std'], std_ratio=b['std']/a['std']))
    out = BASE / 'warm_comparison_20261006'
    out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out / 'axis_comparison.csv', index=False)
    c.finish(['I2'], 'Early-versus-one-hour warm comparison, boot 4',
             'PARTIAL (STARTUP DELAY; WARM COMPARISON COMPLETE)',
             {'early':early, 'warm':late, 'axis_comparison':rows,
              'operator_confirmation':confirmation,
              'boot2_resolution':'Boot2 has a 300-second startup baseline; no boot2 warm recording exists in the active evidence tree. Ten-minute warm recordings exist for boots 1 and 4.',
              'limitations':['Early recording begins 97.27 seconds after boot and lasts ten minutes; the full first ten minutes after boot are not covered.',
                             'No calibrated temperature sweep; observed differences cannot be attributed exclusively to temperature.',
                             'Boot1 warm comparison has a previously documented orientation confound. No new physical measurement.']}, out)

def repeatability():
    rows = [capture(boot, phase) for boot in [1,3,4]
            for phase in ['stationary','guided_motion']]
    assert len({row['boot_id'] for row in rows}) == 3
    fields = ['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2',
              'FIFO_EN','USER_CTRL','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2','WHO_AM_I']
    consistency = {key:len({row['registers'][key] for row in rows})==1 for key in fields}
    out = BASE / 'three_boot_comparison_20261006'
    out.mkdir(exist_ok=True)
    table = []
    for row in rows:
        table.append({k:row[k] for k in ['boot','phase','elapsed_s','n_samples','n_windows',
                     'sample_rate_hz','confirmed_alert_events','i2c_failures','gap_count','C_D']})
    pd.DataFrame(table).to_csv(out/'capture_comparison.csv', index=False)
    axes = [dict(boot=row['boot'],phase=row['phase'],axis=axis,**row['physical_axes'][axis])
            for row in rows for axis in AXES]
    pd.DataFrame(axes).to_csv(out/'axis_comparison.csv',index=False)
    c.finish(['H1'], 'Three-boot saved baseline/motion comparison: boots 1, 3, 4',
             'PARTIAL (BOOT4 MOTION ATTESTATION PENDING)',
             {'captures':rows, 'register_consistency':consistency,
              'excluded_boot2':'Startup baseline valid, motion files empty; preserved, not substituted or relabeled.',
              'operator_confirmations':{'boot1':read(BASE/'boot1_review/summary.json'),
                                        'boot3':read(BASE/'boot3_review/summary.json'),
                                        'boot4_baseline_warm':read(c.BASE/'boot_capture_execution/boot4/operator_attestation.json')},
              'limitations':['Boot4 motion files pass replay verification, but final operator confirmation of the instructed sequence is absent.',
                             'Manual motion amplitudes and resting orientation across boots are not matched; axis offsets are not calibrated bias estimates.',
                             'Each guided capture produced one policy event. Preserve benign-motion events and clipping; no physical alarm or SMS.',
                             'Boot3 baseline was late after boot. No new physical measurement.']},out)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['warm','repeatability'])
    globals()[parser.parse_args().action]()
