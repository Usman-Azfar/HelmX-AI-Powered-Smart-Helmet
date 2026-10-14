import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import randomized_studies as r
from scheduler_trace import parse_timehist


class PlanTests(unittest.TestCase):
    def test_separate_balanced_studies(self):
        plan = r.make_plan()
        self.assertEqual(plan, r.make_plan())
        for study in plan['studies'].values():
            self.assertEqual(study['pairs'].count('AB'), 3)
            self.assertEqual(study['pairs'].count('BA'), 3)
            self.assertEqual(study['seconds_each'], 600)
        self.assertIn('SCHED_FIFO', plan['studies']['D4']['B'])
        self.assertIn('SCHED_OTHER', plan['studies']['K1']['B'])
        self.assertIn('service profile', plan['studies']['K1']['A'])
        self.assertIn('runnable delay', plan['perf_sched'])

    def test_loaded_k1_rejects_reopened_ide(self):
        obs = [{'interactive': [{'name': 'code', 'pid': 10}], 'services': {'lightdm': 'active'}}]
        checks = r.observation_checks(obs, {'lightdm': 'active'}, loaded=True, keep_ide=False)
        self.assertFalse(checks['ide_absent'])
        self.assertFalse(all(checks.values()))

    def test_loaded_k1_allows_desktop_without_ide(self):
        obs = [{'interactive': [{'name': 'labwc', 'pid': 10}], 'services': {'lightdm': 'active'}}]
        self.assertTrue(all(r.observation_checks(obs, {'lightdm': 'active'}, True, False).values()))
        self.assertFalse(all(r.observation_checks(obs, {'lightdm': 'active'}, False, False).values()))

    def test_empty_observations_fail(self):
        self.assertFalse(all(r.observation_checks([], {}, True, False).values()))

    def test_service_change_fails_even_keep_ide_smoke(self):
        obs = [{'interactive': [], 'services': {'wayvnc': 'active'}}]
        self.assertFalse(all(r.observation_checks(obs, {'wayvnc': 'inactive'}, False, True).values()))

    def test_restoration_continues_after_timeout_and_restores_inactive(self):
        calls = []
        def ctl(scope, action, unit):
            calls.append((action, unit))
            if action == 'start' and unit == 'first':
                raise subprocess.TimeoutExpired('systemctl', 30)
            state = 'inactive' if unit in ('first', 'third') else 'active'
            return subprocess.CompletedProcess([], 3 if state == 'inactive' and action == 'is-active' else 0,
                                                state, '')
        errors = r.restore_services(ctl, [('system', 'first', 'active'),
                                            ('user', 'second', 'active'), ('user', 'third', 'inactive')])
        self.assertIn(('start', 'second'), calls)
        self.assertIn(('stop', 'third'), calls)
        self.assertTrue(any('TimeoutExpired' in e for e in errors))
        self.assertTrue(any('expected active' in e for e in errors))

    def test_systemctl_bus_error_is_not_an_inactive_service(self):
        with self.assertRaises(RuntimeError):
            r.service_state(lambda *a: subprocess.CompletedProcess([], 1, '', 'bus failed'), 'user', 'x')

    def test_keep_ide_cannot_be_used_for_full_run(self):
        with patch('sys.argv', ['runner', 'run', '--study', 'D4', '--keep-ide']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                r.main()
        self.assertEqual(result.exception.code, 2)

    def test_full_run_requires_matching_smoke(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r.c, 'BASE', Path(tmp)):
            with self.assertRaisesRegex(RuntimeError, 'successful D4'):
                r.require_smoke('D4', r.make_plan())
            folder = Path(tmp) / 'randomized_studies_v2_20261011'
            folder.mkdir()
            (folder / 'smoke_D4.json').write_text(json.dumps({'plan': {}, 'source_hashes': {}}))
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                r.require_smoke('D4', r.make_plan())


class TraceParserTests(unittest.TestCase):
    def test_wait_and_runnable_delay_are_separate_and_boundaries_excluded(self):
        text = '''           time cpu task name wait time sch delay run time
100.001000 [0003] python[42] 20.000 0.500 1.000
100.040000 [0003] python[42/42] 20.000 0.050 1.000
100.060000 [0003] python[42] 20.000 0.125 1.000
100.090000 [0003] python[42] 20.000 0.750 1.000
'''
        rows = parse_timehist(text, 42, 100, 100.070)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1:3], [20, .05])

    def test_empty_or_unrecognized_trace_fails(self):
        for text in ('', '100.01 [0003] unexpected row'):
            with self.assertRaises(ValueError):
                parse_timehist(text, 42, 100, 101)

    def test_wrong_thread_fails(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected thread'):
            parse_timehist('100.040 [0003] python[43] 20.000 0.050 1.000', 42, 100, 101)


class RunnerTests(unittest.TestCase):
    def run_mock(self, study, fail_restore=False, reopen=False, smoke=True):
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            root = Path(tmp)
            plan = root / 'randomized_studies_v2_20261011/plan.json'
            plan.parent.mkdir()
            plan.write_text(json.dumps(r.make_plan()))
            stack.enter_context(patch.object(r, 'PLAN', plan))
            stack.enter_context(patch.object(r.c, 'BASE', root))
            stack.enter_context(patch.object(r, 'source_hashes', return_value={'runner': 'fixed'}))
            stack.enter_context(patch.object(r, 'require_smoke'))
            stack.enter_context(patch.object(r.os, 'geteuid', return_value=0))
            stack.enter_context(patch.object(r, 'preflight'))
            stack.enter_context(patch.object(r.time, 'sleep'))
            states = {'lightdm.service': 'active', 'wayvnc.service': 'active',
                      'rpi-connect.service': 'active', 'rpi-connect-wayvnc.service': 'inactive'}
            initial = dict(states)
            service_calls = []
            captures = []
            capture_running = [False]
            def systemctl(command, **kwargs):
                action, unit = command[-2:]
                service_calls.append((action, unit))
                if action in ('start', 'stop'):
                    if fail_restore and len(captures) == 2 and action == 'start' and unit == 'wayvnc.service':
                        raise subprocess.TimeoutExpired('systemctl', 30)
                    states[unit] = 'active' if action == 'start' else 'inactive'
                    return subprocess.CompletedProcess(command, 0, '', '')
                return subprocess.CompletedProcess(command, 0 if states[unit] == 'active' else 3, states[unit], '')
            stack.enter_context(patch.object(r.subprocess, 'run', side_effect=systemctl))
            def processes():
                # Reopen during K1's loaded first arm, after the pre-capture gate.
                return [{'pid': 99, 'name': 'code'}] if reopen and capture_running[0] else []
            stack.enter_context(patch.object(r, 'interactive', side_effect=processes))
            class Capture:
                def __init__(self, command, **kwargs):
                    captures.append(command)
                    capture_running[0] = True
                    self.returncode = None
                    label = command[command.index('--label') + 1]
                    folder = root / label
                    folder.mkdir()
                    realtime = '-f' in command
                    (folder / 'metadata.json').write_text(json.dumps({'scheduler': 1 if realtime else 0,
                        'priority': 10 if realtime else 0, 'affinity': [3]}))
                    (folder / 'summary.json').write_text(json.dumps({'capture_start_monotonic': 100, 'capture_end_monotonic': 160}))
                def poll(self): return self.returncode
                def wait(self, **kwargs):
                    self.returncode = 0
                    capture_running[0] = False
                    return 0
                def terminate(self): self.wait()
                def kill(self): self.wait()
            stack.enter_context(patch.object(r.subprocess, 'Popen', Capture))
            metrics = {'gap_count': 0, 'elapsed_s': 60, 'V_T_scored_over_scored_plus_resets': 1,
                       'C_D': 1, 'p_valid_90_sample_position': 1, 'processing_ms': {'99': 4}}
            stack.enter_context(patch.object(r, 'verify', side_effect=lambda *args:
                {'checks': {'raw_replay': True}, 'metrics': dict(metrics), 'scope': 'mock'}))
            stack.enter_context(patch.object(r, 'analyze_scheduler', return_value={'runnable_delay_ms': {'count': 100, '99': .1}}))
            def finish(ids, title, status, value, folder):
                folder.mkdir(exist_ok=True)
                (folder / 'summary.json').write_text(json.dumps(value))
            stack.enter_context(patch.object(r.c, 'finish', side_effect=finish))
            args = ['runner', 'run', '--study', study]
            if smoke: args += ['--smoke-test', '--keep-ide']
            stack.enter_context(patch('sys.argv', args))
            with contextlib.redirect_stdout(io.StringIO()):
                if fail_restore or reopen:
                    with self.assertRaises(RuntimeError): r.main()
                else:
                    r.main()
            base = next(root.glob(('randomized_smoke_' if smoke else 'randomized_') + study + '_*'))
            status = json.loads((base / 'session_status.json').read_text())
            self.assertEqual(status['success'], not (fail_restore or reopen))
            if fail_restore:
                self.assertTrue(status['restoration_errors'])
                self.assertIn(('start', 'rpi-connect.service'), service_calls)
                self.assertFalse((plan.parent / f'smoke_{study}.json').exists())
            elif reopen:
                self.assertEqual(len(captures), 1)
                self.assertIn('changed during', status['failure'])
                self.assertTrue(list(base.glob('*observations.json')))
            else:
                self.assertEqual(states, initial)
                self.assertEqual(len(captures), 2 if smoke else 12)
                for command in captures:
                    self.assertIn('--scheduler-trace', command)
                if study == 'D4':
                    self.assertIn('-o', captures[0] if smoke else captures[1])
                    self.assertIn('-f', captures[1] if smoke else captures[0])
                else:
                    self.assertTrue(all('-o' in cmd for cmd in captures))
                if smoke:
                    self.assertTrue((plan.parent / f'smoke_{study}.json').exists())
                    self.assertFalse(any(action in ('stop', 'start') and unit == 'lightdm.service' for action, unit in service_calls))
                analysis = json.loads((base / 'analysis/summary.json').read_text())['analysis']
                self.assertEqual(len(analysis['gaps_per_min']['pair_differences_B_minus_A']), 1 if smoke else 6)
                self.assertEqual('bootstrap_mean_95_percentile' in analysis['gaps_per_min'], not smoke)

    def test_d4_smoke_both_conditions(self): self.run_mock('D4')
    def test_k1_smoke_both_conditions(self): self.run_mock('K1')
    def test_d4_full_six_pair_path(self): self.run_mock('D4', smoke=False)
    def test_k1_full_six_pair_path(self): self.run_mock('K1', smoke=False)
    def test_smoke_restore_timeout_writes_status_no_pass_marker(self): self.run_mock('D4', fail_restore=True)
    def test_k1_reopened_ide_aborts_and_restores(self): self.run_mock('K1', reopen=True, smoke=False)


if __name__ == '__main__':
    unittest.main()
