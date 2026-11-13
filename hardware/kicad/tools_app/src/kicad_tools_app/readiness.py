"""Non-fatal environment readiness checks for KiCad-backed modules."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import AppSettings


def readiness(settings: AppSettings) -> dict[str, Any]:
    """Return executable, Python package, socket, and editor availability hints."""
    python = _executable(settings.python_executable)
    api_socket = _api_socket()
    return {
        "status": "ok",
        "python": python,
        "kicad": _kicad_executable(settings.kicad_executable),
        "kicad_cli": _executable(settings.kicad_cli_executable),
        "kipy_importable": _can_import_kipy(python["resolved"]),
        "kicad_api_socket": str(api_socket) if api_socket else None,
        "pcb_editor_reachable": _can_reach_kicad(python["resolved"]),
    }


def module_preflight(module: dict[str, Any], report: dict[str, Any]) -> str | None:
    """Return a clear blocker for an indexed module, or ``None`` when ready."""
    if module["requires_kicad_api"] and not report["kipy_importable"]:
        return "The configured Python interpreter cannot import kipy."
    if module["requires_pcb_editor"] and not report["pcb_editor_reachable"]:
        return "KiCad PCB Editor or its API server is not reachable."
    if (
        module["requires_kicad"]
        and not report["kicad"]["available"]
        and not report["pcb_editor_reachable"]
    ):
        return "KiCad is not available on the configured path."
    return None


def _executable(value: str) -> dict[str, Any]:
    path = shutil.which(value)
    if path is None and Path(value).is_file():
        path = str(Path(value).expanduser().absolute())
    return {"configured": value, "available": path is not None, "resolved": path}


def _kicad_executable(value: str) -> dict[str, Any]:
    """Resolve native KiCad or report the installed Flatpak application."""
    result = _executable(value)
    if result["available"] or value != "kicad":
        return result
    try:
        flatpak = subprocess.run(
            ["flatpak", "info", "org.kicad.KiCad"],
            check=False,
            capture_output=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return result
    if flatpak.returncode == 0:
        result["available"] = True
        result["resolved"] = "flatpak:org.kicad.KiCad"
    return result


def _can_import_kipy(python_executable: str | None) -> bool:
    """Return whether the configured interpreter imports kipy within a timeout."""
    if python_executable is None:
        return False
    try:
        result = subprocess.run(
            [python_executable, "-c", "import kipy"],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _can_reach_kicad(python_executable: str | None) -> bool:
    """Return whether kipy can ping the running KiCad API using its defaults."""
    if python_executable is None:
        return False
    probe = (
        "from kipy import KiCad; "
        "client = KiCad(timeout_ms=1000); "
        "client.ping(); "
        "client.close()"
    )
    try:
        result = subprocess.run(
            [python_executable, "-c", probe],
            check=False,
            capture_output=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _api_socket() -> Path | None:
    """Return a visible native or Flatpak socket for diagnostic display."""
    configured = os.environ.get("KICAD_API_SOCKET", "")
    if configured.startswith("ipc://"):
        configured = configured.removeprefix("ipc://")
    candidates = [
        Path(configured) if configured else None,
        Path("/tmp/kicad/api.sock"),
        Path.home() / ".var/app/org.kicad.KiCad/cache/tmp/kicad/api.sock",
    ]
    return next(
        (candidate for candidate in candidates if candidate and candidate.is_socket()),
        None,
    )
