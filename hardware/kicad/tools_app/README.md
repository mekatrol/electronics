# KiCad Tools application

This directory contains the executable allow-list and local FastAPI backend for
approved KiCad helper modules. The backend validates named values against
`module_index.json`, resolves paths beneath configured roots, and constructs a
shell-free argument array. A client cannot submit a script, flag, or command.

## Development

From `tools_app/`, create and activate a virtual environment, then run:

```console
python3 -m pip install -r requirements-dev.txt
ruff format --check .
ruff check .
mypy
pytest
```

Start the localhost-only API with:

```console
kicad-tools-app
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
Settings and run history are written atomically below `data/` and ignored by
Git. Runs from the previous server process that were still queued or running
are marked failed on startup.

The initial API includes health/readiness, module catalogue, run submission,
polling, output, cancellation, history, and settings endpoints. Mutating runs
require explicit confirmation; KiCad-board mutations are serialized.

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
