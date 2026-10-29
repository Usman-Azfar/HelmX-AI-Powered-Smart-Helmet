"""Separate D4/K1 studies, with short smoke runs and fail-closed verification."""
import argparse
import datetime
import fcntl
import json
import os
import pwd
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import campaign as c
from headless_gate import interactive
from verify_saved_capture import verify
from scheduler_trace import analyze as analyze_scheduler

PLAN = c.BASE / 'randomized_studies_v2_20261011/plan.json'
SYSTEM = ['lightdm.service', 'wayvnc.service']
USER = ['rpi-connect.service', 'rpi-connect-wayvnc.service']
COMPETING = ['helmx-crash-monitor.service', 'helmx-research-boot-capture.service',
             'helmx-cold-warm-research.service']


def make_plan():
    rng = random.Random(20261007)
    studies = {}
    for name in ['D4', 'K1']:
        order = ['AB'] * 3 + ['BA'] * 3
        rng.shuffle(order)
        studies[name] = {'pairs': order, 'seconds_each': 600, 'core': 3,
            'A': 'SCHED_OTHER core 3, ' + ('headless' if name == 'D4' else 'originally active desktop/remote service profile'),
            'B': ('SCHED_FIFO priority 10 core 3, headless' if name == 'D4' else 'SCHED_OTHER core 3, desktop/remote services stopped'),
            'limits': 'K1 compares service profiles with IDE absent in both; no synthetic load. D4 changes scheduler only.'}
    return {'version': 2, 'seed': 20261007, 'created_date_pkt': '2026-10-11', 'studies': studies,
            'supersedes': 'randomized_studies_20261007/plan.json (preserved unchanged)',
            'analysis': 'Within-pair B minus A; mean, median, descriptive percentile 95% bootstrap interval; all pairs reported.',
            'stationarity': 'Helmet untouched; operator attestation required afterward.',
            'perf_sched': 'Filtered main-thread sched_switch, sched_wakeup, sched_waking on all CPUs, throughout every condition; perf sched timehist runnable delay distribution. Recorder SCHED_OTHER on cores 0-2. Trace overhead present in both arms.',
            'smoke': 'One AB pair, 60 seconds each. Optional keep-IDE smoke preserves lightdm and allows IDE/desktop processes, but toggles other configured services. Never research evidence.',
            'observations': 'Processes and service states sampled every two seconds; shorter activity cannot be excluded.'}


def ide_processes(processes):
    return [p for p in processes if any(k in p['name'].lower() for k in ('code', 'codium', 'electron'))]


def observation_checks(observations, expected, loaded, keep_ide):
    return {
        'observations_nonempty': bool(observations),
        'workload_profile': bool(observations) and all(o['services'] == expected for o in observations),
        'ide_absent': keep_ide or not any(ide_processes(o['interactive']) for o in observations),
        'headless': keep_ide or loaded or not any(o['interactive'] for o in observations),
    }


def service_state(ctl, scope, unit):
    proc = ctl(scope, 'is-active', unit)
    state = proc.stdout.strip()
    if (proc.returncode, state) not in ((0, 'active'), (3, 'inactive'), (4, 'unknown')):
        raise RuntimeError(f'Cannot establish service state {unit}: {state}: {proc.stderr}')
    return state


def restore_services(ctl, original):
    """Try every restoration even after timeout; preserve originally inactive units."""
    errors = []
    ordered = [item for item in original if item[2] == 'active']
    ordered += list(reversed([item for item in original if item[2] == 'inactive']))
    for scope, unit, state in ordered:
        try:
            proc = ctl(scope, 'start' if state == 'active' else 'stop', unit)
            if proc.returncode:
                raise RuntimeError(proc.stderr)
        except Exception as exc:
            errors.append(f'{unit}: {exc!r}')
    for scope, unit, state in original:
        try:
            actual = service_state(ctl, scope, unit)
            if actual != state:
                errors.append(f'{unit}: expected {state}, restored {actual}')
        except Exception as exc:
            errors.append(f'{unit}: verification {exc!r}')
    return errors


def stop_child(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
            raise RuntimeError('Capture required forced kill; inspect sensor/trace cleanup')


def preflight(ctl):
    for unit in COMPETING:
        if service_state(ctl, 'system', unit) not in ('inactive', 'unknown'):
            raise RuntimeError('Competing capture service: ' + unit)
    if not Path('/dev/i2c-1').exists():
        raise RuntimeError('/dev/i2c-1 is missing')
    ownership = c.command(['fuser', '/dev/i2c-1'])
    if ownership.get('returncode') != 1 or ownership.get('stdout', '').strip():
        raise RuntimeError('Cannot establish free I2C bus: ' + repr(ownership))


def source_hashes():
    # A smoke pass must cover the exact runner, capture, verification and helper sources.
    return {p.name: c.sha(p) for p in (c.BASE / 'scripts').glob('*.py')}


def require_smoke(study, plan):
    marker = c.BASE / f'randomized_studies_v2_20261011/smoke_{study}.json'
    if not marker.exists():
        raise RuntimeError(f'Run a successful {study} --smoke-test before the full study')
    saved = json.loads(marker.read_text())
    if saved['source_hashes'] != source_hashes() or saved['plan'] != plan:
        raise RuntimeError('Sources or plan changed since smoke test; repeat it')
    status = json.loads((Path(saved['evidence']) / 'session_status.json').read_text())
    if status['failure'] or status['restoration_errors'] or not status['success']:
        raise RuntimeError('Smoke evidence does not show successful capture and restoration')


def paired_analysis(results, count):
    metrics = {'gaps_per_min': lambda r: r['gap_count'] / (r['elapsed_s'] / 60),
               'V_T': lambda r: r['V_T_scored_over_scored_plus_resets'],
               'C_D': lambda r: r['C_D'], 'survival_90': lambda r: r['p_valid_90_sample_position'],
               'processing_p99_ms': lambda r: r['processing_ms']['99'],
               'scheduler_delay_p99_ms': lambda r: r['scheduler']['runnable_delay_ms']['99']}
    rng = np.random.default_rng(20261007)
    analysis = {}
    for name, fn in metrics.items():
        differences = np.array([fn(results[f'{i}_B']) - fn(results[f'{i}_A']) for i in range(1, count + 1)])
        entry = {'pair_differences_B_minus_A': differences.tolist(),
                 'mean': float(differences.mean()), 'median': float(np.median(differences))}
        if count > 1:
            bootstrap = rng.choice(differences, size=(10000, count), replace=True).mean(axis=1)
            entry['bootstrap_mean_95_percentile'] = np.percentile(bootstrap, [2.5, 97.5]).tolist()
        analysis[name] = entry
    return analysis


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['plan', 'run'])
    p.add_argument('--study', choices=['D4', 'K1'])
    p.add_argument('--operator-user', default='helmx')
    p.add_argument('--smoke-test', action='store_true', help='One AB pair, 60 seconds per condition; not research evidence')
    p.add_argument('--keep-ide', action='store_true', help='Smoke only: preserve lightdm/IDE, toggle other configured remote services')
    a = p.parse_args()
    if a.keep_ide and not a.smoke_test:
        p.error('--keep-ide is only allowed with --smoke-test')
    if a.action == 'plan':
        if PLAN.exists() and json.loads(PLAN.read_text()) != make_plan():
            raise RuntimeError('Existing preregistration differs')
        if not PLAN.exists():
            c.save(PLAN, make_plan())
        print(PLAN.read_text())
        return
    if not a.study:
        p.error('--study required')
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo')
    plan = json.loads(PLAN.read_text())
    if plan != make_plan():
        raise RuntimeError('Preregistered plan changed')
    if not a.smoke_test:
        require_smoke(a.study, plan)
    if not a.keep_ide and ide_processes(interactive()):
        raise RuntimeError('Close the IDE before starting')
    uid = pwd.getpwnam(a.operator_user).pw_uid

    def ctl(scope, *args):
        command = ['systemctl', *args] if scope == 'system' else [
            'sudo', '-u', a.operator_user, 'env', f'XDG_RUNTIME_DIR=/run/user/{uid}',
            'systemctl', '--user', *args]
        return subprocess.run(command, capture_output=True, text=True, timeout=30)

    # Prevent concurrent randomized runners before making any service changes.
    lock = (PLAN.parent / 'runner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    preflight(ctl)
    original = [(scope, unit, service_state(ctl, scope, unit))
                for scope, units in [('system', SYSTEM), ('user', USER)] for unit in units]
    managed = [entry for entry in original if not (a.keep_ide and entry[1] == 'lightdm.service')]
    if a.study == 'K1' and not any(state == 'active' for _, _, state in managed):
        raise RuntimeError('K1 needs an initially active service that the test can toggle')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    prefix = 'randomized_smoke' if a.smoke_test else 'randomized'
    base = c.BASE / f'{prefix}_{a.study}_{stamp}'
    base.mkdir()
    seconds = 60 if a.smoke_test else plan['studies'][a.study]['seconds_each']
    orders = ['AB'] if a.smoke_test else plan['studies'][a.study]['pairs']
    sources = source_hashes()
    c.save(base / 'plan.json', plan)
    c.save(base / 'execution.json', {'study': a.study, 'smoke_test': a.smoke_test,
           'keep_ide': a.keep_ide, 'seconds_each': seconds, 'pairs': orders, 'source_hashes': sources,
           'scope': 'SMOKE ONLY; IDE/desktop retained' if a.keep_ide else 'Strict service profiles; operator attestation pending'})
    c.save(base / 'services_before.json', original)

    def profile(loaded):
        ordered = managed if loaded else list(reversed(managed))
        for scope, unit, state in ordered:
            if state == 'active':
                proc = ctl(scope, 'start' if loaded else 'stop', unit)
                if proc.returncode:
                    raise RuntimeError(f'Service transition failed: {unit}: {proc.stderr}')
        time.sleep(5)
        return {unit: ('active' if loaded else 'inactive')
                if state == 'active' and (scope, unit, state) in managed else state
                for scope, unit, state in original}

    def observe():
        return {'monotonic': time.monotonic(), 'interactive': interactive(),
                'services': {unit: service_state(ctl, scope, unit) for scope, unit, _ in original}}

    def stopped(signum, frame):
        raise InterruptedError('Stop requested')

    previous_term = signal.signal(signal.SIGTERM, stopped)
    results = {}
    failure = None
    completed = False
    try:
        for pair, order in enumerate(orders, 1):
            for condition in order:
                loaded = a.study == 'K1' and condition == 'A'
                expected = profile(loaded)
                before = observe()
                if not all(observation_checks([before], expected, loaded, a.keep_ide).values()):
                    raise RuntimeError('Pre-capture profile/IDE/headless gate failed: ' + repr(before))
                preflight(ctl)
                label = f'{base.name}/pair{pair}_{condition}'
                realtime = a.study == 'D4' and condition == 'B'
                cmd = ['chrt', '-f' if realtime else '-o', '10' if realtime else '0',
                       'taskset', '-c', str(plan['studies'][a.study]['core']), sys.executable,
                       str(c.BASE / 'scripts/live.py'), '--seconds', str(seconds), '--label', label,
                       '--scheduler-trace']
                if not loaded and not a.keep_ide:
                    cmd.append('--require-headless')
                print(f'{a.study} pair {pair}/{len(orders)} condition {condition}: {seconds}s; {base}', flush=True)
                observations = [before]
                process = None
                try:
                    with (base / f'pair{pair}_{condition}.log').open('w') as log:
                        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                        while process.poll() is None:
                            current = observe()
                            observations.append(current)
                            if not all(observation_checks([current], expected, loaded, a.keep_ide).values()):
                                raise RuntimeError('Profile/IDE/headless condition changed during recording')
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pass
                        observations.append(observe())
                finally:
                    try:
                        if process is not None:
                            stop_child(process)
                    finally:
                        c.save(base / f'pair{pair}_{condition}_observations.json', observations)
                if process.returncode:
                    raise RuntimeError('Capture failed; inspect ' + str(base / f'pair{pair}_{condition}.log'))
                review = verify(label, seconds)
                folder = c.BASE / label
                meta = json.loads((folder / 'metadata.json').read_text())
                summary = json.loads((folder / 'summary.json').read_text())
                scheduler = analyze_scheduler(folder, summary['capture_start_monotonic'], summary['capture_end_monotonic'])
                c.save(folder / 'scheduler_summary.json', scheduler)
                review['metrics']['scheduler'] = scheduler
                review['checks'].update(observation_checks(observations, expected, loaded, a.keep_ide))
                review['checks'].update(scheduler=meta['scheduler'] == (1 if realtime else 0),
                    priority=meta['priority'] == (10 if realtime else 0), core=meta['affinity'] == [3],
                    scheduler_trace_nonempty=scheduler['runnable_delay_ms']['count'] > 0)
                review['scope'] += '; SMOKE ONLY, IDE/headless checks waived' if a.keep_ide else ''
                review['source_hashes'] = {p.name: c.sha(p) for p in folder.iterdir() if p.is_file()}
                ok = all(review['checks'].values())
                status = ('SMOKE VERIFIED; NOT RESEARCH EVIDENCE' if a.smoke_test else
                          'VERIFIED; OPERATOR ATTESTATION PENDING') if ok else 'FAIL'
                c.finish([], f'{a.study} pair {pair} condition {condition}', status, review,
                         base / f'pair{pair}_{condition}_verification')
                if not ok:
                    raise RuntimeError('Verification failed')
                results[f'{pair}_{condition}'] = review['metrics']
        analysis = paired_analysis(results, len(orders))
        c.finish([], f'{a.study} {len(orders)} pairs',
                 'SMOKE VERIFIED; NOT RESEARCH EVIDENCE' if a.smoke_test else
                 'CAPTURED AND VERIFIED; OPERATOR ATTESTATION PENDING',
                 {'study': a.study, 'smoke_test': a.smoke_test, 'keep_ide': a.keep_ide,
                  'pairs': orders, 'conditions': results, 'analysis': analysis, 'limitations': plan}, base / 'analysis')
        completed = True
    except BaseException as exc:
        failure = repr(exc)
        raise
    finally:
        # A second Ctrl-C must not interrupt the best-effort restoration loop.
        old_int = signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            # Keep-IDE smoke never starts/stops lightdm, including during cleanup.
            restore_errors = restore_services(ctl, managed)
            if a.keep_ide:
                for scope, unit, state in original:
                    if unit == 'lightdm.service':
                        try:
                            if service_state(ctl, scope, unit) != state:
                                restore_errors.append('Preserved lightdm state changed')
                        except Exception as exc:
                            restore_errors.append(repr(exc))
            c.save(base / 'session_status.json', {'failure': failure, 'restoration_errors': restore_errors,
                   'success': completed and not restore_errors, 'smoke_test': a.smoke_test,
                   'keep_ide': a.keep_ide})
        finally:
            signal.signal(signal.SIGINT, old_int)
            signal.signal(signal.SIGTERM, previous_term)
            lock.close()
        if restore_errors and failure is None:
            raise RuntimeError('Service restoration failed: ' + repr(restore_errors))
    if a.smoke_test:
        if sources != source_hashes():
            raise RuntimeError('Sources changed during smoke; repeat before full study')
        c.save(PLAN.parent / f'smoke_{a.study}.json', {'plan': plan, 'source_hashes': sources,
               'evidence': str(base), 'keep_ide': a.keep_ide,
               'limitation': 'IDE-active smoke does not validate removal of desktop/IDE. Full runs enforce those gates.'})
    print('Finished and original service states restored: ' + str(base), flush=True)


if __name__ == '__main__':
    main()
