# Module inventory

The user-facing module catalogue is organised by workflow under `modules/`.
The executable index remains the authoritative web-application allow-list.

## Complete runnable catalogue

Every non-test Python script with a direct command-line entry point is indexed
and enabled in the browser. This includes internal workflow stages and discovery
helpers, which are useful independently. Modules whose behavior is controlled by
source-level configuration are exposed with no parameters and clearly identified
by their description and risk confirmation.

## Libraries and tests

Everything in `shared/` is reusable implementation code and never an entry
point. Everything in `tests/` is test code. Package `__init__.py` files are also
not commands. None of these may appear in the executable index.
