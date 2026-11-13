"""Non-fatal environment readiness checks for KiCad-backed modules."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from typing import Any

from .models import AppSettings


def readiness(settings: AppSettings) -> dict[str, Any]:
    """Return executable, Python package, socket, and editor availability hints."""
    socket_candidates = list(Path("/tmp").glob("kicad/api.sock"))
    api_socket = next((path for path in socket_candidates if path.is_socket()), None)
    return {
        "status": "ok",
        "python": _executable(settings.python_executable),
        "kicad": _executable(settings.kicad_executable),
        "kicad_cli": _executable(settings.kicad_cli_executable),
        "kipy_importable": importlib.util.find_spec("kipy") is not None,
        "kicad_api_socket": str(api_socket) if api_socket else None,
        "pcb_editor_reachable": api_socket is not None,
    }


def module_preflight(module: dict[str, Any], report: dict[str, Any]) -> str | None:
    """Return a clear blocker for an indexed module, or ``None`` when ready."""
    if module["requires_kicad_api"] and not report["kipy_importable"]:
        return "The configured Python interpreter cannot import kipy."
    if module["requires_pcb_editor"] and not report["pcb_editor_reachable"]:
        return "KiCad PCB Editor or its API server is not reachable."
    if module["requires_kicad"] and not report["kicad"]["available"]:
        return "KiCad is not available on the configured path."
    return None


def _executable(value: str) -> dict[str, Any]:
    path = shutil.which(value)
    if path is None and Path(value).is_file():
        path = str(Path(value).resolve())
    return {"configured": value, "available": path is not None, "resolved": path}
