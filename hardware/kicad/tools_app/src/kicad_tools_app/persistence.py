"""Atomic JSON settings and run-history persistence."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .models import AppSettings, RunRecord, RunStatus


def atomic_write_json(path: Path, value: object) -> None:
    """Durably replace a JSON file without exposing a partial document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, default=str)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class SettingsStore:
    """Load and atomically save validated application settings."""

    def __init__(self, path: Path, defaults: AppSettings):
        self.path = path
        self.defaults = defaults

    def load(self) -> AppSettings:
        """Return stored settings, creating defaults on first use."""
        if not self.path.exists():
            self.save(self.defaults)
            return self.defaults.model_copy(deep=True)
        return AppSettings.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, settings: AppSettings) -> AppSettings:
        """Atomically persist and return ``settings``."""
        atomic_write_json(self.path, settings.model_dump(mode="json"))
        return settings


class RunStore:
    """Persist one metadata document and two log files per run."""

    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: RunRecord) -> None:
        """Atomically store a complete run snapshot."""
        atomic_write_json(self._metadata(record.id), record.model_dump(mode="json"))

    def get(self, run_id: str) -> RunRecord:
        """Load ``run_id`` or raise ``KeyError`` for an unknown UUID."""
        path = self._metadata(run_id)
        try:
            return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError(run_id) from exc

    def list(self) -> list[RunRecord]:
        """Return all records newest first, ignoring unrelated files."""
        records = [
            RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.runs_dir.glob("*.json")
        ]
        return sorted(records, key=lambda item: item.created_at, reverse=True)

    def recover_interrupted(self) -> int:
        """Mark queued or running records failed after an unclean restart."""
        recovered = 0
        for record in self.list():
            if record.status in (RunStatus.QUEUED, RunStatus.RUNNING):
                record.status = RunStatus.FAILED
                record.finished_at = datetime.now(UTC)
                record.error_summary = "Backend restarted before this run completed."
                self.save(record)
                recovered += 1
        return recovered

    def prune(self, limit: int) -> None:
        """Remove metadata and logs older than the newest ``limit`` records."""
        for record in self.list()[limit:]:
            for path in (
                self._metadata(record.id),
                self.stdout(record.id),
                self.stderr(record.id),
            ):
                path.unlink(missing_ok=True)

    def stdout(self, run_id: str) -> Path:
        """Return the server-controlled stdout path for ``run_id``."""
        return self.runs_dir / f"{run_id}.stdout.log"

    def stderr(self, run_id: str) -> Path:
        """Return the server-controlled stderr path for ``run_id``."""
        return self.runs_dir / f"{run_id}.stderr.log"

    def _metadata(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"
