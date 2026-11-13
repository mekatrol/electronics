"""FastAPI application factory and local development entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .command_builder import build_command
from .configuration import AppPaths, default_paths, default_settings
from .index_loader import ModuleIndex
from .models import AppSettings, RunOutput, RunRecord, RunRequest, RunStatus
from .parameter_validator import ParameterError, ParameterValidator
from .persistence import RunStore, SettingsStore
from .process_runner import ProcessRunner
from .readiness import module_preflight, readiness


def create_app(paths: AppPaths | None = None) -> FastAPI:
    """Create an isolated backend instance using optional test filesystem paths."""
    locations = paths or default_paths()
    index = ModuleIndex(
        locations.index_path, locations.schema_path, locations.repository_root
    )
    settings_store = SettingsStore(locations.settings_path, default_settings(locations))
    settings = settings_store.load()
    runs = RunStore(locations.runs_dir)
    runs.recover_interrupted()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.runner = ProcessRunner(runs, settings.max_concurrent_runs)
        yield

    app = FastAPI(
        title="KiCad Tools API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.paths = locations
    app.state.index = index
    app.state.settings_store = settings_store
    app.state.settings = settings
    app.state.runs = runs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect the landing URL to the interactive API documentation."""
        return RedirectResponse(
            url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    @app.get("/api/health")
    async def health(request: Request) -> dict[str, Any]:
        """Report backend health and non-fatal KiCad readiness information."""
        return readiness(request.app.state.settings)

    @app.get("/api/modules")
    async def list_modules(request: Request) -> list[dict[str, Any]]:
        """List enabled module metadata without resolved executable paths."""
        index = cast(ModuleIndex, request.app.state.index)
        return index.list_public()

    @app.get("/api/modules/{module_id}")
    async def get_module(module_id: str, request: Request) -> dict[str, Any]:
        """Return one enabled module definition by stable ID."""
        try:
            index = cast(ModuleIndex, request.app.state.index)
            return index.get_public(module_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Module not found") from exc

    @app.post(
        "/api/runs", response_model=RunRecord, status_code=status.HTTP_202_ACCEPTED
    )
    async def create_run(body: RunRequest, request: Request) -> RunRecord:
        """Validate, preflight, persist, and queue an approved module run."""
        try:
            module = request.app.state.index.get(body.module_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Module not found") from exc
        if module["risk"]["confirmation_required"] and not body.confirmed:
            raise HTTPException(
                status_code=409, detail="Explicit confirmation is required"
            )
        settings: AppSettings = request.app.state.settings
        validator = ParameterValidator(
            [Path(root) for root in settings.allowed_roots],
            request.app.state.paths.repository_root,
        )
        try:
            values = validator.validate(module, body.parameters)
        except ParameterError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        blocker = module_preflight(module, readiness(settings))
        if blocker:
            raise HTTPException(status_code=503, detail=blocker)
        command = build_command(module, values, settings.python_executable)
        run_id = str(uuid4())
        store: RunStore = request.app.state.runs
        record = RunRecord(
            id=run_id,
            module_id=body.module_id,
            module_index_version=request.app.state.index.version,
            parameters=values,
            arguments=command,
            status=RunStatus.QUEUED,
            created_at=datetime.now(UTC),
            stdout_path=str(store.stdout(run_id)),
            stderr_path=str(store.stderr(run_id)),
        )
        request.app.state.runner.submit(
            record,
            command=command,
            cwd=_working_directory(module, values, request.app.state.paths),
            timeout=module["timeout_seconds"],
            mutates_kicad=module["execution_type"] == "kicad_modify",
            on_finished=lambda: store.prune(settings.history_limit),
        )
        return record

    @app.get("/api/runs", response_model=list[RunRecord])
    async def list_runs(request: Request) -> list[RunRecord]:
        """Return persisted run history, newest first."""
        store = cast(RunStore, request.app.state.runs)
        return store.list()

    @app.get("/api/runs/{run_id}", response_model=RunRecord)
    async def get_run(run_id: str, request: Request) -> RunRecord:
        """Return one historical or active run."""
        return _get_run(request, run_id)

    @app.get("/api/runs/{run_id}/output", response_model=RunOutput)
    async def get_output(run_id: str, request: Request) -> RunOutput:
        """Return captured logs without accepting any client-defined path."""
        _get_run(request, run_id)
        store: RunStore = request.app.state.runs
        return RunOutput(
            stdout=_read_log(store.stdout(run_id)),
            stderr=_read_log(store.stderr(run_id)),
        )

    @app.post("/api/runs/{run_id}/cancel", response_model=RunRecord)
    async def cancel_run(run_id: str, request: Request) -> RunRecord:
        """Cancel a queued or active run and terminate its process group."""
        try:
            runner = cast(ProcessRunner, request.app.state.runner)
            return await runner.cancel(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Run not found") from exc

    @app.get("/api/settings", response_model=AppSettings)
    async def get_settings(request: Request) -> AppSettings:
        """Return active validated application settings."""
        return cast(AppSettings, request.app.state.settings)

    @app.put("/api/settings", response_model=AppSettings)
    async def put_settings(body: AppSettings, request: Request) -> AppSettings:
        """Validate safe roots and executables, then atomically persist settings."""
        roots = [Path(root).resolve() for root in body.allowed_roots]
        if not roots or not all(root.is_dir() for root in roots):
            raise HTTPException(status_code=422, detail="Allowed roots must exist")
        executable = Path(body.python_executable).resolve()
        if not executable.is_file():
            raise HTTPException(status_code=422, detail="Python executable must exist")
        body.allowed_roots = [str(root) for root in roots]
        body.python_executable = str(executable)
        request.app.state.settings = request.app.state.settings_store.save(body)
        return body

    return app


def _get_run(request: Request, run_id: str) -> RunRecord:
    try:
        store = cast(RunStore, request.app.state.runs)
        return store.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


def _read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def _working_directory(
    module: dict[str, Any], values: dict[str, Any], paths: AppPaths
) -> Path:
    policy = module["working_directory"]
    if policy == "repository_root":
        return paths.repository_root
    if policy == "script_directory":
        return Path(module["resolved_script"]).parent
    if policy == "input_parent":
        path_value = next(
            value
            for definition in module["parameters"]
            if definition["type"] in ("file", "directory")
            and (value := values.get(definition["name"]))
        )
        path = Path(path_value)
        return path if path.is_dir() else path.parent
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    return paths.data_dir


app = create_app()


def run() -> None:
    """Run the local-only development server on port 8000."""
    uvicorn.run("kicad_tools_app.main:app", host="127.0.0.1", port=8000)
