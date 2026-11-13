"""Resolve immutable application paths and default runtime settings."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .models import AppSettings


@dataclass(frozen=True)
class AppPaths:
    """Filesystem locations used by the backend."""

    app_dir: Path
    repository_root: Path
    index_path: Path
    schema_path: Path
    data_dir: Path
    runs_dir: Path
    settings_path: Path


def default_paths(app_dir: Path | None = None) -> AppPaths:
    """Return canonical application paths, optionally rooted at ``app_dir``."""
    root = (app_dir or Path(__file__).resolve().parents[2]).resolve()
    return AppPaths(
        app_dir=root,
        repository_root=root.parent,
        index_path=root / "module_index.json",
        schema_path=root / "schemas" / "module_index.schema.json",
        data_dir=root / "data",
        runs_dir=root / "data" / "runs",
        settings_path=root / "data" / "settings.json",
    )


def default_settings(paths: AppPaths) -> AppSettings:
    """Create localhost-safe settings and prefer a dedicated KiCad IPC Python."""
    return AppSettings(
        allowed_roots=[str(paths.repository_root)],
        python_executable=_ipc_python(paths.app_dir),
    )


def _ipc_python(app_dir: Path) -> str:
    """Return the nearest repository IPC interpreter, or this Python as fallback."""
    executable_parts = (
        ("bin", "python"),
        ("Scripts", "python.exe"),
    )
    # The electronics repository keeps this environment above hardware/kicad.
    # Searching ancestors also supports a standalone checkout without a fixed
    # assumption about how many directory levels surround tools_app.
    for parent in (app_dir, *app_dir.parents):
        for parts in executable_parts:
            candidate = parent / ".venv-kicad-ipc" / Path(*parts)
            if candidate.is_file():
                return str(candidate.absolute())
    return sys.executable
