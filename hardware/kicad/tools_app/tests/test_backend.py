"""Unit and API coverage for the Phase 2 backend safety boundaries."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from kicad_tools_app.command_builder import build_command
from kicad_tools_app.configuration import AppPaths
from kicad_tools_app.main import create_app
from kicad_tools_app.models import RunRecord, RunStatus
from kicad_tools_app.parameter_validator import ParameterError, ParameterValidator
from kicad_tools_app.persistence import RunStore
from kicad_tools_app.process_runner import ProcessRunner


def parameter(name: str, kind: str, value_type: str, **extra: Any) -> dict[str, Any]:
    """Create a compact index parameter definition for focused unit tests."""
    return {
        "name": name,
        "kind": kind,
        "type": value_type,
        "required": extra.pop("required", False),
        "default": extra.pop("default", None),
        **extra,
    }


def test_parameter_types_constraints_and_exact_command(tmp_path: Path) -> None:
    """Accept typed values and build only index-owned flags in index order."""
    board = tmp_path / "board.kicad_pcb"
    board.write_text("board", encoding="utf-8")
    module = {
        "resolved_script": str(tmp_path / "tool.py"),
        "parameters": [
            parameter(
                "input", "positional", "file", required=True, extensions=[".kicad_pcb"]
            ),
            parameter(
                "count", "option", "integer", flag="--count", default=1, minimum=1
            ),
            parameter("force", "option", "boolean", flag="--force", default=False),
            parameter("names", "option", "string_list", flag="--names", default=[]),
        ],
    }
    validator = ParameterValidator([tmp_path], tmp_path)
    values = validator.validate(
        module,
        {"input": "board.kicad_pcb", "count": 2, "force": True, "names": ["a", "b"]},
    )
    command = build_command(module, values, sys.executable)
    assert command == [
        str(Path(sys.executable).resolve()),
        str(tmp_path / "tool.py"),
        str(board),
        "--count",
        "2",
        "--force",
        "--names",
        "a",
        "b",
    ]


@pytest.mark.parametrize(
    ("submitted", "message"),
    [
        ({"unknown": 1}, "Unknown parameters"),
        ({}, "Missing required parameter"),
        ({"input": "board.txt"}, "unsupported extension"),
        ({"input": "../outside.kicad_pcb"}, "outside the allowed roots"),
    ],
)
def test_parameter_rejections(
    tmp_path: Path, submitted: dict[str, Any], message: str
) -> None:
    """Reject unknown, missing, wrongly suffixed, and escaping values."""
    module = {
        "parameters": [
            parameter(
                "input", "positional", "file", required=True, extensions=[".kicad_pcb"]
            )
        ]
    }
    with pytest.raises(ParameterError, match=message):
        ParameterValidator([tmp_path], tmp_path).validate(module, submitted)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """Resolve symlinks before checking that a path remains in an allowed root."""
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    (outside / "secret.kicad_pcb").write_text("x", encoding="utf-8")
    (allowed / "jump").symlink_to(outside, target_is_directory=True)
    definition = parameter(
        "input", "positional", "file", required=True, extensions=[".kicad_pcb"]
    )
    with pytest.raises(ParameterError, match="outside the allowed roots"):
        ParameterValidator([allowed], allowed).validate(
            {"parameters": [definition]}, {"input": "jump/secret.kicad_pcb"}
        )


@pytest.mark.asyncio
async def test_runner_success_failure_and_timeout(tmp_path: Path) -> None:
    """Persist terminal states and captured output for representative processes."""
    store = RunStore(tmp_path / "runs")
    runner = ProcessRunner(store)
    cases = [
        ("ok", "print('hello')", 5, RunStatus.SUCCEEDED),
        ("bad", "raise SystemExit(3)", 5, RunStatus.FAILED),
        ("slow", "import time; time.sleep(2)", 1, RunStatus.TIMED_OUT),
    ]
    for run_id, code, timeout, expected in cases:
        record = _record(store, run_id)
        runner.submit(
            record,
            command=[sys.executable, "-c", code],
            cwd=tmp_path,
            timeout=timeout,
            mutates_kicad=False,
        )
        for _ in range(100):
            await asyncio.sleep(0.03)
            if store.get(run_id).status not in (RunStatus.QUEUED, RunStatus.RUNNING):
                break
        assert store.get(run_id).status is expected
    assert store.stdout("ok").read_text(encoding="utf-8") == "hello\n"


@pytest.mark.asyncio
async def test_runner_cancellation(tmp_path: Path) -> None:
    """Cancel an active process and persist the cancelled state."""
    store = RunStore(tmp_path / "runs")
    runner = ProcessRunner(store)
    record = _record(store, "cancel")
    runner.submit(
        record,
        command=[sys.executable, "-c", "import time; time.sleep(10)"],
        cwd=tmp_path,
        timeout=20,
        mutates_kicad=False,
    )
    for _ in range(50):
        await asyncio.sleep(0.02)
        if store.get("cancel").status is RunStatus.RUNNING:
            break
    assert (await runner.cancel("cancel")).status is RunStatus.CANCELLED


def test_recovery_marks_interrupted_runs_failed(tmp_path: Path) -> None:
    """Make pre-restart active records honest historical failures."""
    store = RunStore(tmp_path / "runs")
    store.save(_record(store, "interrupted"))
    assert store.recover_interrupted() == 1
    assert store.get("interrupted").status is RunStatus.FAILED


@pytest.mark.asyncio
async def test_api_contract_and_disabled_module_hiding(tmp_path: Path) -> None:
    """Expose module/settings/history APIs without leaking script paths."""
    paths = _app_tree(tmp_path)
    app = create_app(paths)
    transport = ASGITransport(app=app)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=transport, base_url="http://test") as client,
    ):
        health = await client.get("/api/health")
        assert health.status_code == 200
        modules = (await client.get("/api/modules")).json()
        assert [item["id"] for item in modules] == ["fake-tool"]
        assert "script" not in modules[0]
        assert (await client.get("/api/modules/disabled-tool")).status_code == 404
        assert (await client.get("/api/runs")).json() == []
        assert (await client.get("/api/settings")).status_code == 200
        response = await client.post(
            "/api/runs", json={"module_id": "fake-tool", "parameters": {"bogus": 1}}
        )
        assert response.status_code == 422


def _record(store: RunStore, run_id: str) -> RunRecord:
    return RunRecord(
        id=run_id,
        module_id="fake",
        module_index_version="1.0.0",
        parameters={},
        arguments=[sys.executable],
        status=RunStatus.QUEUED,
        created_at=datetime.now(UTC),
        stdout_path=str(store.stdout(run_id)),
        stderr_path=str(store.stderr(run_id)),
    )


def _app_tree(tmp_path: Path) -> AppPaths:
    repository = tmp_path / "repo"
    app_dir = repository / "tools_app"
    modules = repository / "modules"
    schemas = app_dir / "schemas"
    modules.mkdir(parents=True)
    schemas.mkdir(parents=True)
    (modules / "fake.py").write_text("print('ok')\n", encoding="utf-8")
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "module_index.schema.json").read_text(
            encoding="utf-8"
        )
    )
    (schemas / "module_index.schema.json").write_text(
        json.dumps(schema), encoding="utf-8"
    )
    base = {
        "name": "Fake",
        "description": "Harmless test module.",
        "script": "../modules/fake.py",
        "category": "analysis",
        "execution_type": "read_only",
        "requires_kicad": False,
        "requires_pcb_editor": False,
        "requires_kicad_api": False,
        "working_directory": "repository_root",
        "timeout_seconds": 5,
        "parameters": [],
        "risk": {
            "level": "low",
            "summary": "Test only.",
            "confirmation_required": False,
        },
    }
    index = {
        "schema_version": "1.0.0",
        "application_compatibility": ">=0.1.0 <1.0.0",
        "modules": [
            {"id": "fake-tool", "enabled": True, **base},
            {"id": "disabled-tool", "enabled": False, **base},
        ],
    }
    (app_dir / "module_index.json").write_text(json.dumps(index), encoding="utf-8")
    return AppPaths(
        app_dir=app_dir,
        repository_root=repository,
        index_path=app_dir / "module_index.json",
        schema_path=schemas / "module_index.schema.json",
        data_dir=app_dir / "data",
        runs_dir=app_dir / "data" / "runs",
        settings_path=app_dir / "data" / "settings.json",
    )
