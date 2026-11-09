"""Stop stuck KiCad processes and remove stale local IPC sockets.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/kill_kicad.py

Use this recovery script only after closing KiCad normally. It targets KiCad
processes owned by the current user, asks them to terminate, and force-stops
only processes that remain after a short grace period. It also asks Flatpak to
stop org.kicad.KiCad and removes abandoned KiCad API socket files. Board and
project files are never modified.
"""

from __future__ import annotations

import os
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from pathlib import Path

from kicad_discovery import FLATPAK_APP_ID

# Match executable names rather than command-line text so an unrelated command
# that happens to mention "kicad" is not terminated.
KICAD_PROCESS_NAMES = {
    "bitmap2component",
    "eeschema",
    "gerbview",
    "kicad",
    "kicad-cli",
    "pcbnew",
    "pl_editor",
}

TERMINATE_GRACE_SECONDS = 3.0


def current_user_kicad_processes() -> dict[int, str]:
    """Return current-user KiCad process IDs and their executable names."""
    processes: dict[int, str] = {}
    own_pid = os.getpid()
    own_uid = os.getuid()

    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == own_pid:
            continue
        try:
            if entry.stat().st_uid != own_uid:
                continue
            name = (entry / "comm").read_text(encoding="utf-8").strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            # Processes can exit while /proc is being inspected.
            continue
        if name in KICAD_PROCESS_NAMES:
            processes[pid] = name
    return processes


def signal_processes(processes: dict[int, str], selected_signal: signal.Signals):
    """Send one signal to each process that still exists."""
    for pid, name in processes.items():
        try:
            os.kill(pid, selected_signal)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            print(f"Could not signal {name} process {pid}: {error}")


def stop_native_processes() -> tuple[dict[int, str], dict[int, str]]:
    """Terminate current-user KiCad processes, escalating after a grace period."""
    found = current_user_kicad_processes()
    if not found:
        return {}, {}

    signal_processes(found, signal.SIGTERM)
    deadline = time.monotonic() + TERMINATE_GRACE_SECONDS
    remaining = current_user_kicad_processes()
    while remaining and time.monotonic() < deadline:
        time.sleep(0.1)
        remaining = current_user_kicad_processes()

    forced = {pid: name for pid, name in remaining.items() if pid in found}
    if forced:
        signal_processes(forced, signal.SIGKILL)
    return found, forced


def stop_flatpak():
    """Ask Flatpak to stop all processes belonging to the KiCad application."""
    flatpak = shutil.which("flatpak")
    if flatpak is None:
        return
    subprocess.run(
        [flatpak, "kill", FLATPAK_APP_ID],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def ipc_socket_directories() -> list[Path]:
    """Return native and Flatpak directories used by KiCad's local IPC API."""
    return [
        Path(tempfile.gettempdir()) / "kicad",
        Path.home() / ".var/app" / FLATPAK_APP_ID / "cache/tmp/kicad",
    ]


def remove_stale_sockets() -> list[Path]:
    """Remove only Unix sockets with KiCad API socket names."""
    removed: list[Path] = []
    for directory in ipc_socket_directories():
        if not directory.is_dir():
            continue
        for path in directory.glob("api*.sock"):
            try:
                mode = path.lstat().st_mode
                if not stat.S_ISSOCK(mode):
                    print(f"Skipped non-socket path: {path}")
                    continue
                path.unlink()
                removed.append(path)
            except FileNotFoundError:
                pass
            except PermissionError as error:
                print(f"Could not remove socket {path}: {error}")
    return removed


def main():
    """Stop KiCad and clear IPC sockets that can trap later API clients."""
    # Flatpak may supervise child processes, so stop the application before
    # inspecting and terminating any native processes that remain.
    stop_flatpak()
    found, forced = stop_native_processes()
    sockets = remove_stale_sockets()

    if found:
        descriptions = ", ".join(
            f"{name} ({pid})" for pid, name in sorted(found.items())
        )
        print(f"Stopped KiCad process(es): {descriptions}")
    else:
        print("No remaining current-user KiCad processes were found.")

    if forced:
        descriptions = ", ".join(
            f"{name} ({pid})" for pid, name in sorted(forced.items())
        )
        print(
            f"Force-stopped after {TERMINATE_GRACE_SECONDS:.0f} seconds: {descriptions}"
        )

    if sockets:
        print("Removed stale IPC socket(s):")
        for path in sockets:
            print(f"  {path}")
    else:
        print("No stale KiCad IPC sockets were found.")


if __name__ == "__main__":
    main()
