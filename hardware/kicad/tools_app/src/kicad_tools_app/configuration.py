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
    """Create localhost-safe settings limited to the current repository."""
    return AppSettings(
        allowed_roots=[str(paths.repository_root)],
        python_executable=sys.executable,
    )
