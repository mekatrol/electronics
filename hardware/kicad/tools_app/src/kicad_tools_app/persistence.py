"""Atomic JSON settings persistence and ephemeral latest-run state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import AppSettings, RunRecord


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
        value = json.loads(self.path.read_text(encoding="utf-8"))
        # Migrate settings written before run-history retention was removed.
        if value.pop("history_limit", None) is not None:
            settings = AppSettings.model_validate(value)
            return self.save(settings)
        return AppSettings.model_validate(value)

    def save(self, settings: AppSettings) -> AppSettings:
        """Atomically persist and return ``settings``."""
        atomic_write_json(self.path, settings.model_dump(mode="json"))
        return settings


class RunStore:
    """Keep only the latest run and its output in process memory."""

    def __init__(self) -> None:
        self._record: RunRecord | None = None
        self._stdout = ""
        self._stderr = ""

    def save(self, record: RunRecord) -> None:
        """Replace the in-memory latest-run snapshot."""
        if (
            self._record is None
            or record.id == self._record.id
            or record.created_at > self._record.created_at
        ):
            if self._record is None or record.id != self._record.id:
                self._stdout = ""
                self._stderr = ""
            self._record = record.model_copy(deep=True)

    def get(self, run_id: str) -> RunRecord:
        """Return ``run_id`` if it is the latest run."""
        if self._record is None or self._record.id != run_id:
            raise KeyError(run_id)
        return self._record.model_copy(deep=True)

    def latest(self) -> RunRecord | None:
        """Return the latest submitted run, if one exists."""
        return self._record.model_copy(deep=True) if self._record else None

    def set_output(self, run_id: str, stdout: bytes, stderr: bytes) -> None:
        """Store decoded output only when ``run_id`` is still the latest run."""
        if self._record is not None and self._record.id == run_id:
            self._stdout = stdout.decode("utf-8", errors="replace")
            self._stderr = stderr.decode("utf-8", errors="replace")

    def output(self, run_id: str) -> tuple[str, str]:
        """Return output for the latest run or raise ``KeyError``."""
        self.get(run_id)
        return self._stdout, self._stderr
