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
from kicad_tools_app.configuration import AppPaths, default_settings
from kicad_tools_app.index_loader import ModuleIndex
from kicad_tools_app.main import create_app
from kicad_tools_app.models import AppSettings, RunRecord, RunStatus
from kicad_tools_app.parameter_validator import ParameterError, ParameterValidator
from kicad_tools_app.persistence import RunStore
from kicad_tools_app.process_runner import ProcessRunner
from kicad_tools_app.readiness import module_preflight, readiness


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
        str(Path(sys.executable).absolute()),
        str(tmp_path / "tool.py"),
        str(board),
        "--count",
        "2",
        "--force",
        "--names",
        "a",
        "b",
    ]


def test_align_component_edge_center_contract() -> None:
    """Validate and serialize the first approved board-editing CLI exactly."""
    app_dir = Path(__file__).resolve().parents[1]
    repository_root = app_dir.parent
    index = ModuleIndex(
        app_dir / "module_index.json",
        app_dir / "schemas" / "module_index.schema.json",
        repository_root,
    )
    module = index.get("align-component-edge-center")
    assert module["execution_type"] == "kicad_modify"
    assert module["risk"]["confirmation_required"] is True
    assert module["requires_pcb_editor"] is True
    assert module["requires_kicad_api"] is True
    values = ParameterValidator([repository_root], repository_root).validate(
        module,
        {
            "reference": "J12",
            "alignment": "vertical",
            "include_text": True,
        },
    )

    assert build_command(module, values, sys.executable) == [
        str(Path(sys.executable).absolute()),
        str((repository_root / "modules/align_component_edge_center.py").resolve()),
        "J12",
        "--alignment",
        "vertical",
        "--include-text",
    ]


def test_align_component_edge_center_rejects_unknown_axis(tmp_path: Path) -> None:
    """Reject an alignment value that the script CLI cannot accept."""
    definition = {
        "parameters": [
            parameter(
                "alignment",
                "option",
                "enum",
                flag="--alignment",
                default="horizontal",
                choices=["horizontal", "vertical"],
            )
        ]
    }
    with pytest.raises(ParameterError, match="not an allowed choice"):
        ParameterValidator([tmp_path], tmp_path).validate(
            definition, {"alignment": "diagonal"}
        )


@pytest.mark.parametrize(
    ("definition", "value", "message"),
    [
        (parameter("reference", "positional", "string"), "  ", "non-empty string"),
        (
            parameter("references", "option", "string_list", flag="--references"),
            [],
            "contain non-empty strings",
        ),
        (
            parameter("references", "option", "string_list", flag="--references"),
            ["J1", ""],
            "contain non-empty strings",
        ),
    ],
)
def test_empty_reference_values_are_rejected(
    tmp_path: Path, definition: dict[str, Any], value: Any, message: str
) -> None:
    """Stop empty footprint selectors before they reach a module process."""
    with pytest.raises(ParameterError, match=message):
        ParameterValidator([tmp_path], tmp_path).validate(
            {"parameters": [definition]}, {definition["name"]: value}
        )


@pytest.mark.parametrize(
    ("module_id", "submitted", "expected_tail"),
    [
        (
            "align-mounting-holes",
            {"direction": "both", "left_offset": 4.0},
            [
                "--top-left",
                "H1",
                "--top-right",
                "H2",
                "--bottom-left",
                "H3",
                "--bottom-right",
                "H4",
                "--direction",
                "both",
                "--left-offset",
                "4.0",
                "--right-offset",
                "3.0",
                "--top-offset",
                "35.5",
                "--bottom-offset",
                "5.5",
            ],
        ),
        (
            "center-and-distribute-items",
            {"references": ["J1", "J2", "J3"], "distribute_spacing": True},
            [
                "--references",
                "J1",
                "J2",
                "J3",
                "--alignment",
                "horizontal",
                "--distribute-spacing",
            ],
        ),
        ("center-routed-design", {}, []),
        ("center-board-outline", {}, ["--zone-edge-tolerance", "0.2"]),
        (
            "space-components",
            {"anchor": "J1", "moving": "H2", "spacing": 12.5},
            ["J1", "H2", "--alignment", "vertical", "--spacing", "12.5"],
        ),
    ],
)
def test_phase_four_board_editing_contracts(
    module_id: str, submitted: dict[str, Any], expected_tail: list[str]
) -> None:
    """Enforce exact safe commands and mutation metadata for Phase 4 tools."""
    app_dir = Path(__file__).resolve().parents[1]
    repository_root = app_dir.parent
    index = ModuleIndex(
        app_dir / "module_index.json",
        app_dir / "schemas" / "module_index.schema.json",
        repository_root,
    )
    module = index.get(module_id)
    assert module["execution_type"] == "kicad_modify"
    assert module["risk"]["confirmation_required"] is True
    assert module["requires_pcb_editor"] is True
    assert module["requires_kicad_api"] is True
    values = ParameterValidator([repository_root], repository_root).validate(
        module, submitted
    )
    command = build_command(module, values, sys.executable)
    assert command == [
        str(Path(sys.executable).absolute()),
        module["resolved_script"],
        *expected_tail,
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


def test_default_settings_discover_repository_ipc_python(tmp_path: Path) -> None:
    """Prefer the dedicated kipy environment above a nested app checkout."""
    app_dir = tmp_path / "hardware" / "kicad" / "tools_app"
    ipc_python = tmp_path / ".venv-kicad-ipc" / "bin" / "python"
    app_dir.mkdir(parents=True)
    ipc_python.parent.mkdir(parents=True)
    ipc_python.write_text("", encoding="utf-8")
    paths = AppPaths(
        app_dir=app_dir,
        repository_root=app_dir.parent,
        index_path=app_dir / "module_index.json",
        schema_path=app_dir / "schemas/module_index.schema.json",
        data_dir=app_dir / "data",
        runs_dir=app_dir / "data/runs",
        settings_path=app_dir / "data/settings.json",
    )

    assert default_settings(paths).python_executable == str(ipc_python.absolute())


def test_command_preserves_virtual_environment_python_symlink(tmp_path: Path) -> None:
    """Do not collapse a venv launcher to its base interpreter."""
    base_python = tmp_path / "base-python"
    venv_python = tmp_path / "venv" / "bin" / "python"
    base_python.write_text("", encoding="utf-8")
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(base_python)
    module = {"resolved_script": "/module.py", "parameters": []}

    assert build_command(module, {}, str(venv_python))[0] == str(venv_python)


def test_readiness_probes_configured_python_for_kipy(tmp_path: Path) -> None:
    """Report kipy from the execution interpreter, not the backend process."""
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)
    settings = AppSettings(
        allowed_roots=[str(tmp_path)], python_executable=str(fake_python)
    )

    report = readiness(settings)
    assert report["kipy_importable"] is True
    assert report["pcb_editor_reachable"] is True


def test_reachable_editor_satisfies_gui_availability() -> None:
    """Allow IPC modules when a Flatpak editor responds without a host binary."""
    module = {
        "requires_kicad": True,
        "requires_pcb_editor": True,
        "requires_kicad_api": True,
    }
    report = {
        "kipy_importable": True,
        "pcb_editor_reachable": True,
        "kicad": {"available": False},
    }

    assert module_preflight(module, report) is None


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
        landing = await client.get("/", follow_redirects=False)
        assert landing.status_code == 200
        assert "text/html" in landing.headers["content-type"]
        assert '<div id="app"></div>' in landing.text
        asset_path = landing.text.split('src="', 1)[1].split('"', 1)[0]
        asset = await client.get(asset_path)
        assert asset.status_code == 200
        assert "javascript" in asset.headers["content-type"]
        assert (await client.get("/runs/example")).status_code == 200
        assert (await client.get("/api/not-a-route")).status_code == 404
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
