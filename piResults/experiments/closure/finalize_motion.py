"""Close C3/N5 from verified saved captures, retaining operator limitations."""
import csv
import json
import numpy as np
import pandas as pd
import campaign as c


def main():
    base = c.BASE / '07_high_range_benign_motion'
    plan = json.loads((base / 'guided_plan.json').read_text())
    rows, sources = [], {}
    for phase in plan['phases']:
        source = base / phase
        verification = json.loads((base / (phase + '_resume_verification') / 'summary.json').read_text())
        if not all(verification['checks'].values()):
            raise RuntimeError('Failed replay verification: ' + phase)
        if not all(c.sha(source / name) == digest for name, digest in verification['source_hashes'].items()):
            raise RuntimeError('Capture changed since replay: ' + phase)
        summary = json.loads((source / 'summary.json').read_text())
        raw = pd.read_csv(source / 'raw_sensor.csv', float_precision='round_trip')
        windows = pd.read_csv(source / 'window_scores.csv', float_precision='round_trip')
        if summary['exception'] or summary['i2c_failures'] or len(raw) != summary['n_samples']:
            raise RuntimeError('Invalid capture: ' + phase)
        axes = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
        columns = ['ax_ms2', 'ay_ms2', 'az_ms2', 'gx_dps', 'gy_dps', 'gz_dps']
        row = {'phase': phase, 'duration_s': summary['elapsed_s'], 'samples': len(raw),
               'windows': len(windows), 'classifier_max': float(windows.crash_prob.max()),
               'reconstruction_max': float(windows.recon_error.max()),
               'classifier_crossings': summary['classifier_crossings'],
               'reconstruction_crossings': summary['reconstruction_crossings'],
               'or_positive_windows': summary['or_positive_windows'],
               'confirmed_alerts': summary['confirmed_alert_events']}
        for axis, column in zip(axes, columns):
            values = raw[column].to_numpy()
            step = 9.80665 / 2048 if axis[0] == 'a' else 1 / 16.4
            counts = np.rint(values / step)
            rails = int(np.sum((counts <= -32768) | (counts >= 32767)))
            if rails != summary['rail_counts'][axis]:
                raise RuntimeError('Rail-count mismatch: ' + phase + '/' + axis)
            row.update({axis + '_min': float(values.min()), axis + '_max': float(values.max()),
                        axis + '_rail_hits': rails})
        row['accel_rail_hits'] = sum(row[a + '_rail_hits'] for a in axes[:3])
        row['gyro_rail_hits'] = sum(row[a + '_rail_hits'] for a in axes[3:])
        rows.append(row)
        sources[phase] = {name: c.sha(source / name) for name in
                          ['raw_sensor.csv', 'window_scores.csv', 'summary.json', 'metadata.json',
                           'configuration.json', 'registers_during.json', 'registers_restored.json']}
    disposition = json.loads((base / '05_repeated_tilt_disposition/summary.json').read_text())
    discarded = c.ROOT / disposition['preserved_capture_path'] / 'raw_sensor.csv'
    if c.sha(discarded) != disposition['raw_sha256']:
        raise RuntimeError('Discarded trial provenance changed')
    if sources['05_repeated_tilt']['raw_sensor.csv'] == c.sha(discarded):
        raise RuntimeError('Discarded tilt was reused')
    out = c.BASE / 'motion_C3_completed'
    out.mkdir(exist_ok=True)
    with (out / 'benign_motion.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    limits = [
        'Saved guided captures, not new physical trials. Motion identity is based on recorded instructions/operator statements, not independent observation.',
        'Donning cue preceded recorder initialization; full donning onset coverage is unproven. Operator reported additional movement after donning. A repeat is needed for an onset-complete donning claim.',
        'First repeated-tilt attempt is excluded and preserved as discarded; the replacement capture and its operator confirmation are used.',
        'Separate trials reset gravity, window and cooldown state. Summed events are not a continuous-session or road false-alert rate.',
        'No rail hits were observed in these recorded phases; this does not prove elimination of clipping under amplitude-matched motion or crashes.',
        'Policy events only: this battery did not activate GPIO, execute alarm countdowns, or send SMS.'
    ]
    result = {'phases': rows, 'source_hashes': sources, 'phase_count': len(rows),
              'totals': {key: sum(r[key] for r in rows) for key in
                         ['duration_s', 'samples', 'windows', 'classifier_crossings',
                          'reconstruction_crossings', 'or_positive_windows', 'confirmed_alerts',
                          'accel_rail_hits', 'gyro_rail_hits']},
              'units': 'Acceleration m/s^2; angular velocity deg/s; duration seconds.',
              'limitations': limits,
              'supersedes': 'The hard-coded PARTIAL status in guided_motion_progress despite remaining_phases=[]; no additional motion phases were found missing.'}
    c.finish(['C3'], 'Saved high-range motion battery closure',
             'COMPLETE (GUIDED CAPTURES; DONNING ONSET LIMITED)', result, out)
    table = c.BASE / 'presentation_N5_high_range'
    table.mkdir(exist_ok=True)
    (table / 'benign_motion.csv').write_bytes((out / 'benign_motion.csv').read_bytes())
    c.finish(['N5'], 'High-range benign-motion table', 'COMPLETE (SAVED GUIDED CAPTURES)',
             {'source': str(out.relative_to(c.ROOT)), 'table': 'benign_motion.csv',
              'table_sha256': c.sha(table / 'benign_motion.csv'), 'limitations': limits,
              'historical_table_retained': 'piResults/results/final-closure/presentation_N5'}, table)


if __name__ == '__main__':
    main()
