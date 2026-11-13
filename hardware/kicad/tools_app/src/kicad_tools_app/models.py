"""Public API and persistence models for the KiCad tools backend."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(StrEnum):
    """Lifecycle states stored for a submitted module run."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class RunRequest(BaseModel):
    """Request an indexed module run with named, non-executable values."""

    model_config = ConfigDict(extra="forbid")
    module_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    parameters: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class RunRecord(BaseModel):
    """Persisted metadata for one subprocess execution."""

    model_config = ConfigDict(extra="forbid")
    id: str
    module_id: str
    module_index_version: str
    parameters: dict[str, Any]
    arguments: list[str]
    status: RunStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    stdout_path: str
    stderr_path: str
    artifacts: list[str] = Field(default_factory=list)
    error_summary: str | None = None


class RunOutput(BaseModel):
    """Captured standard output and error for a historical run."""

    stdout: str
    stderr: str


class AppSettings(BaseModel):
    """Validated local execution settings persisted by the application."""

    model_config = ConfigDict(extra="forbid")
    allowed_roots: list[str]
    python_executable: str
    kicad_executable: str = "kicad"
    kicad_cli_executable: str = "kicad-cli"
    max_concurrent_runs: int = Field(default=2, ge=1, le=16)
    history_limit: int = Field(default=200, ge=1, le=10_000)
    frontend_origin: str = "http://localhost:5173"
