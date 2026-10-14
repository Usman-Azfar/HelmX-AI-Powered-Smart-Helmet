"""Filtered scheduler trace for the acquisition thread; no sensor access.

Keep waking/switch events on every CPU (a waker may be on another core), but
filter by acquisition TID to avoid recording the entire desktop workload.
perf timehist's 'sch delay' is runnable delay; 'wait time' includes sleep.
"""
import csv
import json
import os
import re
import select
import signal
import subprocess
import time
from pathlib import Path

import numpy as np


class SchedulerTrace:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.process = None
        self.log = None
        self.tid = os.getpid()
        self.command = None
        self.control_fds = []

    def start(self):
        control_read, control_write = os.pipe()
        ack_read, ack_write = os.pipe()
        # The recorder must not inherit the acquisition thread's FIFO policy
        # or compete on its pinned core. The Pi has four cores.
        self.command = [
            'chrt', '-o', '0', 'taskset', '-c', '0-2',
            'perf', 'record', '-a', '--clockid', 'mono', '--no-buildid-cache',
            '-m', '256', '-o', str(self.folder / 'scheduler.data'),
            '--delay=-1', '--control', f'fd:{control_read},{ack_write}',
            '-e', 'sched:sched_switch', '--filter',
            f'prev_pid == {self.tid} || next_pid == {self.tid}',
            '-e', 'sched:sched_wakeup', '--filter', f'pid == {self.tid}',
            '-e', 'sched:sched_waking', '--filter', f'pid == {self.tid}',
        ]
        self.log = (self.folder / 'scheduler_record.log').open('w')
        try:
            self.process = subprocess.Popen(
                self.command, stdout=self.log, stderr=subprocess.STDOUT,
                pass_fds=(control_read, ack_write), start_new_session=True,
                env={**os.environ, 'LC_ALL': 'C'},
            )
            os.close(control_read); control_read = None
            os.close(ack_write); ack_write = None
            os.write(control_write, b'enable\n')
            if not select.select([ack_read], [], [], 15)[0]:
                raise RuntimeError('perf readiness acknowledgement timed out')
            acknowledgement = os.read(ack_read, 128)
            if acknowledgement.strip(b'\n\r\x00 ') != b'ack':
                raise RuntimeError('perf did not acknowledge tracing readiness: ' + repr(acknowledgement))
            self.check()
            self.ready_monotonic = time.monotonic()
            # Closing the control pipe ends recording in perf 6.12.
            self.control_fds = [control_write, ack_read]
            control_write = ack_read = None
        except BaseException:
            self.stop()
            raise
        finally:
            for fd in (control_read, control_write, ack_read, ack_write):
                if fd is not None:
                    os.close(fd)

    def check(self):
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError('Scheduler recorder exited before capture finished')

    def stop(self):
        if self.process is None:
            if self.log is not None:
                self.log.close()
            return None
        forced = False
        requested_stop = self.process.poll() is None
        if requested_stop:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                forced = True
                self.process.kill()
                self.process.wait(timeout=10)
        self.log.close()
        for fd in self.control_fds:
            os.close(fd)
        self.control_fds = []
        result = {'tid': self.tid, 'command': self.command,
                  'ready_monotonic': getattr(self, 'ready_monotonic', None),
                  'returncode': self.process.returncode, 'forced_kill': forced,
                  'requested_stop': requested_stop}
        (self.folder / 'scheduler_trace.json').write_text(json.dumps(result, indent=2) + '\n')
        if forced or not requested_stop or self.process.returncode not in (0, -signal.SIGINT):
            return 'Scheduler recorder failed: ' + repr(result)
        return None


ROW = re.compile(
    r'^\s*(\d+\.\d+)\s+\[\d+\]\s+.*?\[(\d+)(?:/\d+)?\]\s+'
    r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$'
)


def parse_timehist(text, tid, start, end):
    rows = []
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            if re.match(r'^\s*\d+\.\d+\s+\[\d+\]', line):
                raise ValueError('Unrecognized perf timehist data row: ' + line)
            continue
        timestamp, row_tid, wait, delay, runtime = match.groups()
        if int(row_tid) != tid:
            raise ValueError('Unexpected thread in filtered perf report')
        timestamp, wait, delay, runtime = map(float, (timestamp, wait, delay, runtime))
        # timehist prints the switch-out timestamp. Drop boundary rows whose
        # preceding sleep/run interval began before the capture interval.
        if timestamp <= end and timestamp - (wait + runtime) / 1000 >= start:
            rows.append([timestamp, wait, delay, runtime])
    if not rows:
        raise ValueError('No complete acquisition-thread scheduler events')
    return rows


def distribution(values):
    return {'count': len(values), 'mean': float(np.mean(values)),
            **{str(q): float(np.percentile(values, q)) for q in (0, 50, 95, 99, 100)}}


def analyze(folder, start, end):
    folder = Path(folder)
    trace = json.loads((folder / 'scheduler_trace.json').read_text())
    if (trace['forced_kill'] or not trace['requested_stop'] or
            trace['returncode'] not in (0, -signal.SIGINT) or trace['ready_monotonic'] is None):
        raise RuntimeError('Invalid scheduler recording')
    command = ['perf', 'sched', 'timehist', '-i', str(folder / 'scheduler.data'),
               '-t', str(trace['tid']), '--time', f'{start:.9f},{end:.9f}']
    result = subprocess.run(command, capture_output=True, text=True, timeout=120,
                            env={**os.environ, 'LC_ALL': 'C'})
    (folder / 'scheduler_timehist.txt').write_text(result.stdout)
    (folder / 'scheduler_timehist.stderr').write_text(result.stderr)
    diagnostics = result.stderr + '\n' + (folder / 'scheduler_record.log').read_text()
    # Fail closed on lost-event diagnostics. Zero-loss informational summaries
    # aren't emitted by the supported perf timehist invocation.
    if result.returncode or re.search(r'\b(lost|WARNING|Error|failed)\b', diagnostics, re.I):
        raise RuntimeError('perf analysis failed or reported trace loss: ' + diagnostics)
    rows = parse_timehist(result.stdout, trace['tid'], start, end)
    with (folder / 'scheduler_waits.csv').open('w') as stream:
        writer = csv.writer(stream)
        writer.writerow(['switch_out_monotonic', 'off_cpu_wait_ms', 'runnable_delay_ms', 'run_ms'])
        writer.writerows(rows)
    return {'tid': trace['tid'], 'capture_start_monotonic': start,
            'capture_end_monotonic': end,
            'runnable_delay_ms': distribution([row[2] for row in rows]),
            'off_cpu_wait_ms': distribution([row[1] for row in rows]),
            'scope': 'Acquisition main thread only; perf sched timehist sch delay is runnable wait. '
                     'Off-CPU wait includes intentional sleep. Trace overhead present in both arms. '
                     'Values have perf timehist millisecond output precision.',
            'documentation': 'https://github.com/torvalds/linux/blob/v6.12/tools/perf/Documentation/perf-sched.txt'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Two-second scheduler probe; no sensor or service changes')
    parser.add_argument('--probe-dir', type=Path, required=True)
    args = parser.parse_args()
    args.probe_dir.mkdir(parents=True, exist_ok=False)
    recorder = SchedulerTrace(args.probe_dir)
    recorder.start()
    try:
        begin = time.monotonic()
        for _ in range(100):
            time.sleep(.02)
            recorder.check()
        end = time.monotonic()
    finally:
        error = recorder.stop()
    if error:
        raise RuntimeError(error)
    report = analyze(args.probe_dir, begin, end)
    (args.probe_dir / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
