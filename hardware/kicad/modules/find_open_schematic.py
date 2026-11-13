"""Print the root schematic open in KiCad using the supported IPC API."""

import sys
from pathlib import Path

from kipy import KiCad
from kipy.errors import ApiError as KiCadApiError
from kipy.errors import ConnectionError as KiCadConnectionError
from kipy.proto.common.types import DocumentType

HARDWARE_DIR = Path(__file__).resolve().parents[2]


def schematic_paths(document) -> list[Path]:
    """Resolve a schematic using IPC metadata or a filesystem fallback."""
    filename = Path(document.board_filename)

    if not filename.name:
        return []

    # Use an absolute filename if supplied by the API.
    if filename.is_absolute():
        return [filename.resolve()] if filename.is_file() else []

    # Prefer explicit project metadata where available.
    if document.project.path:
        candidate = Path(document.project.path) / filename
        return [candidate.resolve()] if candidate.is_file() else []

    # KiCad 10.0.8 returns only the schematic filename.
    # Search the hardware directory and reject ambiguous matches later.
    return [
        path.resolve() for path in HARDWARE_DIR.rglob(filename.name) if path.is_file()
    ]


def main() -> int:
    """Print the sole open root schematic path for the parent process."""
    try:
        client = KiCad(timeout_ms=3000)
        try:
            client.ping()
            schematic_documents = client.get_open_documents(
                DocumentType.DOCTYPE_SCHEMATIC
            )
        finally:
            client.close()

    except (KiCadApiError, KiCadConnectionError, OSError) as error:
        print(
            "Could not communicate with Schematic Editor through KiCad IPC. "
            f"KiCad IPC error: {error}",
            file=sys.stderr,
        )
        return 1

    if not schematic_documents:
        print("No schematic is open in Schematic Editor.", file=sys.stderr)
        return 1

    # Deduplicate paths before enforcing exactly one schematic.
    schematics = sorted(
        {path for document in schematic_documents for path in schematic_paths(document)}
    )

    if len(schematics) != 1:
        names = ", ".join(str(path) for path in schematics) or "none"
        print(
            "Could not uniquely resolve the open schematic. "
            f"Found {len(schematics)} matching file(s): {names}. "
            "Pass the schematic path explicitly if needed.",
            file=sys.stderr,
        )
        return 1

    print(schematics[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
