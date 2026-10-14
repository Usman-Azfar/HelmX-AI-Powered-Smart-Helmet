"""Non-blocking cross-platform alarm playback with a safe terminal fallback."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path


def play_alarm(path: str | Path) -> None:
    alarm = Path(path).resolve()
    if not alarm.is_file():
        print("\a", end="", flush=True)
        return
    if platform.system() == "Windows":
        import winsound

        # The stdlib winsound stub is intentionally empty on non-Windows type-checkers.
        # Resolve its platform-only members dynamically while keeping the import lazy.
        members = vars(winsound)
        play_sound = members["PlaySound"]
        flags = members["SND_FILENAME"] | members["SND_ASYNC"]
        play_sound(str(alarm), flags)
        return
    candidates = (("afplay", [str(alarm)]), ("paplay", [str(alarm)]), ("aplay", [str(alarm)]))
    for executable, arguments in candidates:
        resolved = shutil.which(executable)
        if resolved:
            subprocess.Popen(
                [resolved, *arguments],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
    print("\a", end="", flush=True)
