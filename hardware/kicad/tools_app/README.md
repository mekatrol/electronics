# KiCad Tools application

Phase 1 defines the executable allow-list in `module_index.json`. The future
backend must select a module by its stable ID, validate values against its
parameter definitions, and construct an argument array from the stored script
and flags. It must never accept a script path, flag, or command from a client.

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
5. Install `tools_app/requirements-dev.txt`, then run
   `python -m unittest discover -s tools_app/tests` from this directory.

The schema intentionally disallows unknown fields. Extend the schema and its
tests before adding new backend-visible behavior.
