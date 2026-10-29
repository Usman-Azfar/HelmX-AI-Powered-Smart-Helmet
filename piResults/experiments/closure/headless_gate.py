"""Shared headless gate; match application names, never arbitrary substrings."""
import psutil


def is_interactive(name):
    name = (name or '').lower()
    exact = {'code', 'code-insiders', 'code-oss', 'codium', 'electron',
             'devtool', 'wayvnc', 'rpi-connect', 'xorg', 'xwayland',
             'labwc', 'lxsession', 'lightdm'}
    prefixes = ('code-', 'vs-code', 'vscode', 'devtool-', 'rpi-connect-')
    return name in exact or name.startswith(prefixes)


def interactive():
    return [{'pid': p.pid, 'name': p.info['name']}
            for p in psutil.process_iter(['name'])
            if is_interactive(p.info['name'])]
