# KiCad Tools Web Application Plan

## Overview

Create a local web application that provides a Vue.js GUI for selected KiCad 10
helper scripts in `modules/`.

The application will use:

- A Python backend, because the existing tools are Python modules and several
  use KiCad's `kipy` IPC client.
- A Vue.js frontend supplied separately from the user's preferred template.
- JSON files for module definitions, application settings, and run history.
- Separate subprocesses for script execution, providing isolation between the
  server and each KiCad tool.

The application will live in `hardware/kicad/tools_app/`. From the current
KiCad directory, this is the `tools_app/` directory.

## General engineering requirements

- All code must pass its configured formatting, linting, type-checking, and
  test commands.
- Public modules, classes, functions, and methods must include documentation
  describing their signatures, inputs, return values, errors, side effects,
  and purpose.
- Comments inside methods must explain the purpose of important logic and why
  a decision or safety check is necessary.
- Comments must not merely restate programming-language syntax or semantics.
- Script execution must use explicit argument arrays and must never accept raw
  commands from the browser.
- File paths and executable paths must be validated by the backend.
- The server must bind to localhost by default.

## Phase 1: Create the module index

**Status: Complete (2026-11-13).** All Phase 1 deliverables and acceptance
criteria are implemented. The module-index validation suite passes, along with
the relevant existing module tests. Continue with Phase 2 when work resumes.

Create `tools_app/module_index.json` as the authoritative description of the
scripts that the web application may execute.

### 1.1 Inventory and classify modules

Review every non-test, non-legacy Python file under `modules/` and classify it
as one of the following:

- User-facing runnable module
- Shared support library
- Test module
- Legacy module
- Unsafe or unsuitable for web execution

Only explicitly approved runnable modules will appear in the index. Helper
libraries, tests, and legacy scripts will not be exposed.

Each runnable module will also have an execution classification:

- `read_only`: Reports information without modifying files or KiCad.
- `kicad_modify`: Modifies the board open in KiCad, normally through an
  undoable IPC commit.
- `file_generate`: Generates manufacturing, panel, report, or other files.
- `system_control`: Controls an external application, such as terminating
  KiCad.

System-control modules will be disabled by default.

### 1.2 Define the module index schema

Each module entry will include:

- A stable ID
- A display name
- A description of its purpose
- Its script path
- Whether it is enabled
- Its category and execution type
- Whether it requires KiCad, PCB Editor, or the KiCad API server
- Its working-directory policy
- Its execution timeout
- Its parameters and their defaults
- Its risk and confirmation requirements

An example entry is:

```json
{
  "id": "panelize-routed-pcb",
  "name": "Panelize Routed PCB",
  "description": "Create a routed mouse-bite production panel from a KiCad PCB.",
  "script": "../modules/panelize_routed_pcb.py",
  "enabled": true,
  "category": "manufacturing",
  "execution_type": "file_generate",
  "requires_kicad": false,
  "requires_kicad_api": false,
  "working_directory": "repository_root",
  "timeout_seconds": 600,
  "parameters": [
    {
      "name": "input",
      "label": "Input PCB",
      "description": "Source .kicad_pcb file.",
      "kind": "positional",
      "type": "file",
      "required": true,
      "default": null,
      "extensions": [".kicad_pcb"]
    },
    {
      "name": "count_x",
      "label": "Horizontal count",
      "description": "Number of boards across the panel.",
      "kind": "option",
      "flag": "--count-x",
      "type": "integer",
      "required": true,
      "default": 1,
      "minimum": 1
    }
  ]
}
```

The top-level document will include:

- A schema version
- An application compatibility version
- The module collection
- Optional category definitions

Parameter definitions will support:

- `string`
- `integer`
- `number`
- `boolean`
- `enum`
- `file`
- `directory`
- `string_list`

Parameter validation metadata will include defaults, minimums, maximums, file
extensions, enum choices, required status, and whether a path may be created.

### 1.3 Refactor script interfaces where necessary

The existing scripts currently use two interface styles:

- Command-line arguments, as used by scripts such as
  `panelize_routed_pcb.py`, `generate_jlcpcb.py`, and `check_bom_stock.py`.
- Module-level settings, as used by several IPC board-editing scripts.

The application must not rewrite Python source files to change module-level
settings. These scripts will gradually receive explicit command-line
parameters or callable configuration dataclasses.

A consistent target interface is:

```python
def run(options: ModuleOptions) -> int:
    """Run the module with validated options and return its process status."""
```

A thin `argparse` entry point can call the same function to preserve normal
command-line use.

Scripts that have not yet been refactored can initially appear with no
configurable parameters and use their existing defaults. They must not be
represented as configurable until the backend can pass the settings safely.

### 1.4 Validate the index

Add a JSON Schema at:

```text
tools_app/schemas/module_index.schema.json
```

Add automated tests that verify:

- The index conforms to its schema.
- Module IDs are unique.
- Referenced scripts exist.
- Script paths cannot escape the repository.
- Parameter defaults satisfy their constraints.
- CLI flags are unique within a module.
- Tests, legacy scripts, and support libraries are not accidentally exposed.
- Every enabled module has a description, risk classification, and timeout.

### Phase 1 deliverables

- `module_index.json`
- `schemas/module_index.schema.json`
- An initial approved module inventory
- Refactored interfaces for the first supported modules
- Module-index validation tests
- Documentation for adding another module

### Phase 1 acceptance criteria

- The index validates during lint and test execution.
- Every enabled entry maps to a real, approved script.
- The backend can construct arguments without importing arbitrary script code.
- No client-provided script path or command is accepted.

## Phase 2: Create the Python backend

**Status: Complete (2026-11-13).** The localhost FastAPI backend, strict
parameter and path validation, safe subprocess lifecycle, atomic persistence,
readiness reporting, REST endpoints, quality tooling, tests, and development
documentation are implemented. Continue with Phase 3 when the preferred Vue
template is available.

Use FastAPI for the backend. It provides typed request validation, JSON APIs,
generated OpenAPI documentation, and straightforward integration with the
existing Python scripts.

### 2.1 Proposed directory structure

```text
tools_app/
├── PLAN.md
├── README.md
├── module_index.json
├── pyproject.toml
├── schemas/
│   └── module_index.schema.json
├── src/
│   └── kicad_tools_app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── modules.py
│       │   ├── runs.py
│       │   └── settings.py
│       ├── models/
│       │   ├── module.py
│       │   ├── run.py
│       │   └── settings.py
│       ├── services/
│       │   ├── index_loader.py
│       │   ├── parameter_validator.py
│       │   ├── command_builder.py
│       │   ├── process_runner.py
│       │   └── persistence.py
│       └── configuration.py
├── data/
│   ├── settings.json
│   └── runs/
└── tests/
```

Runtime-generated files under `data/` will be ignored by Git. Sanitized
example files may be committed where useful.

### 2.2 API design

Initial API endpoints will be:

```text
GET    /api/health
GET    /api/modules
GET    /api/modules/{module_id}
POST   /api/runs
GET    /api/runs
GET    /api/runs/{run_id}
GET    /api/runs/{run_id}/output
POST   /api/runs/{run_id}/cancel
GET    /api/settings
PUT    /api/settings
```

`POST /api/runs` will accept a module ID and parameter values, for example:

```json
{
  "module_id": "panelize-routed-pcb",
  "parameters": {
    "input": "project/example.kicad_pcb",
    "count_x": 4,
    "count_y": 3
  }
}
```

The server will obtain the script and argument rules from `module_index.json`.
The client will never submit executable paths or raw command fragments.

### 2.3 Execution model

Run every module in a separate subprocess:

- Use an argument array rather than a shell command string.
- Set `shell=False`.
- Use a configured Python interpreter, preferably the KiCad IPC virtual
  environment.
- Capture standard output and standard error separately.
- Record start time, finish time, exit status, and cancellation state.
- Enforce the module-specific timeout.
- Allow only a small, configurable number of concurrent processes.
- Initially serialize scripts that modify the active KiCad board.
- Terminate the complete process group when cancelling or timing out.

Run states will be:

```text
queued -> running -> succeeded
                  -> failed
                  -> cancelled
                  -> timed_out
```

The first version can use client polling. Server-Sent Events may be added later
for live output without changing the underlying execution model.

### 2.4 File-based persistence

Store one metadata file and separate output logs for each run:

```text
data/runs/{run_id}.json
data/runs/{run_id}.stdout.log
data/runs/{run_id}.stderr.log
```

Run metadata will include:

- Run ID
- Module ID and module-index version
- Submitted parameters
- The resolved and redacted argument list
- Status and exit code
- Created, started, and finished timestamps
- Output and log paths
- Generated artifact paths, when known
- An error summary

Persistence rules will include:

- Write to a temporary file and atomically rename it.
- Use UUIDs for run IDs.
- Recover interrupted `queued` or `running` records during startup.
- Apply a configurable history-retention limit.
- Never store secrets in module parameters or logs.
- Keep application settings in `data/settings.json`.

A database is unnecessary for the expected single-host workload.

### 2.5 Path and execution security

The backend can execute local programs, so it must enforce strict boundaries:

- Modules must come only from the checked-in index.
- Resolve and validate every file and directory parameter.
- Configure explicit allowed project roots.
- Reject paths outside those roots.
- Reject symlink-based path escapes.
- Validate file extensions where specified.
- Do not expose arbitrary environment-variable configuration.
- Do not pass unrecognised parameters.
- Do not invoke a shell.
- Require explicit confirmation metadata for mutating or destructive modules.
- Keep `kill_kicad.py` and similar modules disabled unless deliberately
  enabled.
- Bind to localhost by default.

If the application later becomes remotely accessible, authentication,
authorization, CSRF protection, and TLS will become a separate required phase.

### 2.6 KiCad-specific readiness checks

Expose readiness information through the health endpoint:

- KiCad executable availability
- `kicad-cli` availability
- Configured Python interpreter availability
- `kipy` import status
- KiCad API socket presence
- Whether PCB Editor appears reachable

These checks will report status but will not prevent the backend from starting.
Before running an IPC module, the backend will return a clear preflight error
if PCB Editor or the API server is unavailable.

### 2.7 Code quality

Use:

- Ruff for formatting and linting
- mypy for static type checking
- pytest for testing
- JSON Schema validation for the module index

Public modules, classes, functions, and methods will have docstrings describing:

- Signature and parameter expectations
- Return values
- Raised errors
- Side effects
- The purpose of the operation

Comments inside methods will explain non-obvious decisions, safety boundaries,
filesystem assumptions, subprocess handling, and recovery logic. The same
standard will later apply to Vue code through ESLint, TypeScript checks, and
JSDoc where appropriate.

### 2.8 Backend testing

Tests will cover:

- Index loading and schema errors
- Every supported parameter type and validation rule
- Missing and unknown parameters
- Path traversal and symlink escapes
- Exact subprocess argument construction
- Successful, failed, cancelled, and timed-out runs
- Atomic JSON persistence
- Startup recovery
- Concurrent-run limits
- KiCad preflight failures
- API response contracts
- A harmless fake module for end-to-end execution tests

Real KiCad integration tests will be marked separately because they require a
running GUI and API server.

### Phase 2 deliverables

- FastAPI backend
- File-based settings and run history
- Safe subprocess runner
- REST API and generated OpenAPI document
- Health and KiCad readiness checks
- Unit and API tests
- Ruff, mypy, and pytest configuration
- Backend usage and development documentation

### Phase 2 acceptance criteria

- Formatting, linting, type checking, and tests pass.
- A supported module can be launched and monitored through the API.
- Invalid parameters cannot reach the subprocess runner.
- Arbitrary commands and out-of-root paths cannot be submitted.
- Runs survive a backend restart as historical records.
- Mutating KiCad tasks cannot overlap unintentionally.

## Phase 3: Integrate the Vue.js frontend

**Status: Complete (2026-11-13).** The supplied Vue template is integrated
with the backend through a typed API client. It provides metadata-driven
parameter forms, risk confirmations, submission and polling, persistent run
history and logs, cancellation, readiness, settings, clear API errors, a
development proxy, responsive styling, and unit and browser tests. Frontend
and backend quality checks pass. Continue with Phase 4 by refactoring and
approving additional module candidates.

The user will supply the preferred Vue.js template. This phase defines a stable
backend contract and integrates that template rather than generating a separate
frontend design.

### 3.1 Recommended screens

- Module catalogue grouped by category
- Module details and a dynamically generated parameter form
- Confirmation page for mutating operations
- Active-run view with standard output and standard error
- Run history
- Application and KiCad readiness status
- Settings page for allowed roots and executable configuration

Forms will be generated from each module's `parameters` metadata. This avoids
creating a custom Vue component for every script.

### 3.2 Frontend API contract

Provide TypeScript interfaces generated from, or kept consistent with, the
OpenAPI schema:

```typescript
interface ModuleDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  executionType: string;
  parameters: ModuleParameter[];
}

interface RunRecord {
  id: string;
  moduleId: string;
  status: RunStatus;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  exitCode: number | null;
}
```

The backend will configure development CORS only for the known Vue development
origin. Production should serve both applications through the same origin,
either by having FastAPI serve the built Vue assets or by using a local reverse
proxy.

### 3.3 Integration sequence

1. Add the preferred Vue template under `tools_app/frontend/`.
2. Generate or implement the typed API client.
3. Build the module catalogue.
4. Build schema-driven parameter controls.
5. Add validation messages from backend responses.
6. Add run submission and status polling.
7. Add log display and cancellation.
8. Add run history and readiness views.
9. Add confirmations for mutating and destructive actions.
10. Add frontend linting, type checking, unit tests, and a small end-to-end
    suite.

### Phase 3 acceptance criteria

- The Vue application does not contain hard-coded module definitions.
- Forms are derived from backend metadata.
- Client-side validation improves usability while the backend remains
  authoritative.
- Run state and logs remain usable after a page refresh.
- Backend error messages are presented clearly.
- Both frontend and backend lint and test commands pass.

## Phase 4: Expand the approved module catalogue

**Status: In progress (started 2026-11-13).** The representative read-only and
file-generation workflows are available. The next work is to expose suitable
board-editing candidates incrementally without weakening the execution or path
safety boundaries established in Phases 1–3.

### 4.1 Refactor candidate interfaces

- Select one related group of board-editing scripts at a time from
  `INVENTORY.md`.
- Replace browser-configurable module constants with typed option dataclasses
  and explicit command-line arguments while preserving direct CLI use.
- Keep each operation's KiCad IPC changes within an undoable commit where the
  KiCad API supports it.

### 4.2 Approve and index modules

- Review each refactored script's risk, preflight requirements, timeout, and
  parameter constraints before adding it to `module_index.json`.
- Add exact command-construction and parameter-validation tests for every new
  interface.
- Exercise the schema-driven form and confirmation flow without adding
  module-specific frontend code.

### Phase 4 acceptance criteria

- Each newly enabled module has an explicit, tested CLI contract.
- Board-editing operations require confirmation and remain serialized.
- No module requires source rewriting or accepts raw command fragments.
- Backend and frontend quality checks continue to pass.

## Recommended implementation order

Begin with three representative modules:

1. `report_board_dimensions.py` for read-only IPC execution.
2. `generate_jlcpcb.py` for file generation with a simple argument interface.
3. `panelize_routed_pcb.py` for complex validation and generated output.

Once the module index, subprocess runner, persistence, and frontend contract
work for these three cases, add the remaining scripts one category at a time.
This keeps the initial implementation small while exercising the important
execution patterns.
