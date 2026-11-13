# KiCad Tools application

This directory contains the executable allow-list and local FastAPI backend for
approved KiCad helper modules. The backend validates named values against
`module_index.json`, resolves paths beneath configured roots, and constructs a
shell-free argument array. A client cannot submit a script, flag, or command.

## Development

Open `tools_app/` as the VS Code workspace. On first use, run these tasks from
**Terminal > Run Task**:

1. `Backend: Setup environment`
2. `Backend: Install dependencies`

Then use `Backend: Run (reload)` to start the development server. Open
`http://127.0.0.1:8000/docs` to use the generated interactive API.

To debug, open **Run and Debug**, select `Debug KiCad Tools backend`, and press
F5. Breakpoints in `src/kicad_tools_app/` will be active. The debug launch does
not use auto-reload because reload starts a child process that makes breakpoint
behaviour less predictable. Stop any running reload task before debugging so
port 8000 is free.

The `Backend: Test` task is the default test task, and `Backend: Quality checks`
runs formatting checks, linting, strict type checking, and the complete test
suite.

For equivalent command-line setup from `tools_app/`, run:

```console
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn kicad_tools_app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
Settings and run history are written atomically below `data/` and ignored by
Git. Runs from the previous server process that were still queued or running
are marked failed on startup.

The initial API includes health/readiness, module catalogue, run submission,
polling, output, cancellation, history, and settings endpoints. Mutating runs
require explicit confirmation; KiCad-board mutations are serialized.

The backend and KiCad tools intentionally use separate Python environments.
VS Code launches FastAPI with `tools_app/.venv`, while indexed IPC modules run
with the nearest repository `.venv-kicad-ipc` interpreter. The application
discovers that interpreter for new settings and checks `kipy` by invoking the
configured interpreter itself. Existing installations can select it on the
Settings screen; in this repository it is
`/home/dad/repos/electronics/.venv-kicad-ipc/bin/python`.

The Vue frontend is in `frontend/`. For development, start the backend, run
`npm install` and `npm run dev` there, then open `http://127.0.0.1:5173`.
The development server proxies `/api` to the backend.

For normal use, run `npm run build` in `frontend/`. Vite minifies the frontend
and writes it to `src/kicad_tools_app/static/`; the backend then serves the UI
at `http://127.0.0.1:8000` with no Node process or Vite development server.
Frontend quality checks are `npm run lint`, `npm run type-check`,
`npm run test:unit`, `npm run test:e2e`, and `npm run build`.

## Adding a module

1. Classify the file in `INVENTORY.md`. Do not expose tests, legacy files,
   support libraries, or scripts that still require source-code edits.
2. Give the script a normal `argparse` interface backed by a callable
   `run(options)` function where practical. Browser-configurable settings must
   be explicit arguments; module-level constants are not configurable.
3. Add one entry to `module_index.json`. Use a repository-relative static
   script path, a conservative timeout, accurate KiCad requirements, and a
   risk statement. System-control entries must be disabled.
4. Describe every accepted argument. Options need a literal long-form flag;
   path inputs need appropriate extensions and `may_create` only for outputs.
5. Install `tools_app/requirements-dev.txt`, then run the development commands
   above from this directory.

The schema intentionally disallows unknown fields. Extend the schema and its
tests before adding new backend-visible behavior.
