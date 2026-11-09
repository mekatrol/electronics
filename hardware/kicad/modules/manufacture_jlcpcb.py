"""Panelize one KiCad project and generate its complete JLCPCB upload set.

Run from the repository root with::

    python3 hardware/kicad/modules/manufacture_jlcpcb.py mek-smd-mag-led -x 4 -y 3

The project directory must contain ``<directory-name>.kicad_pcb``. All output
is written to its ignored ``manufacture`` subdirectory.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from generate_jlcpcb import HARDWARE_DIR, run

MODULES_DIR = Path(__file__).resolve().parent


def project_board(project: Path) -> Path:
    """Resolve a project directory and its same-named board file."""
    if not project.exists() and len(project.parts) == 1:
        project = HARDWARE_DIR / project
    project = project.resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"project directory not found: {project}")
    board = project / f"{project.name}.kicad_pcb"
    if not board.is_file():
        raise FileNotFoundError(
            f"same-named board not found: {board}; expected "
            f"{project.name}.kicad_pcb"
        )
    return board


def manufacture(
    project: Path,
    count_x: int,
    count_y: int,
    kicad_cli: str | None = None,
) -> Path:
    """Generate the panel and every JLCPCB fabrication/assembly artifact."""
    if count_x < 1 or count_y < 1:
        raise ValueError("count-x and count-y must be positive")
    board = project_board(project)
    output_dir = board.parent / "manufacture"
    panel = output_dir / f"{board.stem}_routed_panel_{count_x}x{count_y}.kicad_pcb"

    panel_command = [
        sys.executable,
        str(MODULES_DIR / "panelize_routed_pcb.py"),
        str(board),
        "-x",
        str(count_x),
        "-y",
        str(count_y),
        "--output",
        str(panel),
        "--force",
    ]
    export_command = [
        sys.executable,
        str(MODULES_DIR / "generate_jlcpcb_panel.py"),
        str(panel),
        "--output-dir",
        str(output_dir),
    ]
    if kicad_cli:
        panel_command.extend(["--kicad-cli", kicad_cli])
        export_command.extend(["--kicad-cli", kicad_cli])

    run(panel_command)
    run(export_command)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="project directory or name")
    parser.add_argument("-x", "--count-x", type=int, required=True)
    parser.add_argument("-y", "--count-y", type=int, required=True)
    parser.add_argument("--kicad-cli", help="path to KiCad 10 kicad-cli")
    args = parser.parse_args()
    try:
        output_dir = manufacture(
            args.project, args.count_x, args.count_y, args.kicad_cli
        )
    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Complete JLCPCB upload set written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
