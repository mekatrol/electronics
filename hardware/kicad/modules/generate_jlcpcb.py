#!/usr/bin/env python3
"""Generate JLCPCB fabrication and assembly files from a KiCad project.

The output is written to a ``gerber`` directory beside the board:

* one Gerber per manufacturing layer and Excellon drill file(s)
* ``<project>-gerbers.zip`` for upload as the PCB fabrication file
* ``<project>-bom.csv``
* ``<project>-positions.csv`` (CPL / centroid / pick-and-place)

KiCad 10 or newer and its ``kicad-cli`` executable are required.  This script
does not use the deprecated SWIG ``pcbnew`` module.

Execution::

    python3 hardware/kicad/modules/generate_jlcpcb.py <project>
    python3 hardware/kicad/modules/generate_jlcpcb.py --help
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path
from typing import Sequence

import kicad_netlist_reader


GERBER_LAYERS = (
    "F.Cu",
    "B.Cu",
    "F.Paste",
    "B.Paste",
    "F.SilkS",
    "B.SilkS",
    "F.Mask",
    "B.Mask",
    "Edge.Cuts",
)
HARDWARE_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = HARDWARE_DIR.parent
IPC_PYTHON = REPOSITORY_DIR / ".venv-kicad-ipc" / "bin" / "python"
IPC_UNSAVED_CHECK = Path(__file__).with_name("check_kicad_unsaved.py")
UNSAVED_PROJECT_MESSAGE = (
    "the KiCad project has unsaved changes; save it in KiCad, then run this "
    "command again"
)


def run(command: Sequence[str]) -> None:
    """Print and execute one external command, failing on a non-zero status."""
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def print_failure(error: Exception) -> None:
    """Print every expected failure prominently, with a KiCad hint if useful."""
    messages = [f"ERROR: {error}"]
    if isinstance(error, subprocess.CalledProcessError):
        command = [str(part) for part in error.cmd]
        if "sch" in command and "erc" in command:
            messages.append("Run DRC in schematic to see detail")
        elif "pcb" in command and "drc" in command:
            messages.append("Run DRC in PCB to see detail")

    lines = [
        line
        for message in messages
        for line in textwrap.wrap(
            message, width=75, break_long_words=False, break_on_hyphens=False
        )
    ]
    content_width = max(len(line) for line in lines)
    border = "*" * (content_width + 4)
    print(border, file=sys.stderr)
    for line in lines:
        print(f"* {line:<{content_width}} *", file=sys.stderr)
    print(border, file=sys.stderr)


def find_kicad_cli(override: str | None = None) -> list[str]:
    """Find a native KiCad CLI or the CLI in the official KiCad Flatpak."""
    if override:
        return [override]

    native = shutil.which("kicad-cli")
    if native:
        return [native]

    flatpak = shutil.which("flatpak")
    if flatpak:
        result = subprocess.run(
            [flatpak, "info", "org.kicad.KiCad"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return [flatpak, "run", "--command=kicad-cli", "org.kicad.KiCad"]

    raise FileNotFoundError(
        "kicad-cli was not found; install KiCad 7 or newer, or pass "
        "--kicad-cli /path/to/kicad-cli"
    )


def find_project_files(source: Path) -> tuple[Path, Path | None]:
    """Return the board and optional root schematic selected by *source*."""
    if not source.exists() and len(source.parts) == 1 and not source.suffix:
        source = HARDWARE_DIR / source
    source = source.resolve()
    if source.suffix == ".kicad_pcb":
        board = source
    elif source.suffix in {".kicad_pro", ".pro"}:
        board = source.with_suffix(".kicad_pcb")
    elif source.is_dir():
        boards = sorted(
            path for path in source.glob("*.kicad_pcb")
            if not path.name.startswith("_autosave-")
        )
        if len(boards) != 1:
            raise ValueError(
                f"expected one .kicad_pcb in {source}, found {len(boards)}"
            )
        board = boards[0]
    else:
        raise ValueError(
            "input must be a hardware project name, KiCad project, board, "
            "or project directory"
        )

    if not board.is_file():
        raise FileNotFoundError(f"board not found: {board}")
    schematic = board.with_suffix(".kicad_sch")
    return board, schematic if schematic.is_file() else None


def reject_newer_autosaves(files: Sequence[Path]) -> None:
    """Refuse to manufacture from files older than KiCad's autosaved state."""
    newer_autosaves = []
    for source in files:
        autosave = source.with_name(f"_autosave-{source.name}")
        if autosave.is_file() and autosave.stat().st_mtime > source.stat().st_mtime:
            newer_autosaves.append(autosave)

    if newer_autosaves:
        raise RuntimeError(UNSAVED_PROJECT_MESSAGE)


def reject_unsaved_open_board(board: Path) -> None:
    """Use KiCad IPC, when available, to detect changes before autosave runs."""
    if not IPC_PYTHON.is_file() or not IPC_UNSAVED_CHECK.is_file():
        return
    result = subprocess.run(
        [str(IPC_PYTHON), str(IPC_UNSAVED_CHECK), str(board)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=6,
    )
    if result.returncode == 2:
        raise RuntimeError(UNSAVED_PROJECT_MESSAGE)


def copper_layers(board: Path) -> list[str]:
    """Read enabled copper layer names directly from the board file."""
    layers: list[str] = []
    in_layers = False
    depth = 0
    with board.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            stripped = line.strip()
            if not in_layers and stripped == "(layers":
                in_layers = True
                depth = 1
                continue
            if not in_layers:
                continue
            depth += line.count("(") - line.count(")")
            parts = stripped.split('"')
            if len(parts) >= 3 and parts[1].endswith(".Cu"):
                layers.append(parts[1])
            if depth <= 0:
                break
    return layers or ["F.Cu", "B.Cu"]


def write_bom(netlist_file: Path, output_file: Path) -> None:
    """Convert KiCad's XML BOM netlist to JLCPCB's assembly columns."""
    net = kicad_netlist_reader.netlist(str(netlist_file))
    with output_file.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for group in net.groupComponents():
            populated = [
                part for part in group if (part.getField("LCSC Part #") or "").strip()
            ]
            if not populated:
                continue
            part = populated[0]
            footprints = part.getFootprint().split(":", 1)
            writer.writerow(
                [
                    part.getValue(),
                    ",".join(item.getRef() for item in populated),
                    footprints[-1],
                    part.getField("LCSC Part #"),
                ]
            )


def convert_positions(source: Path, destination: Path) -> None:
    """Convert KiCad position CSV columns and side names to JLCPCB format."""
    with source.open(newline="", encoding="utf-8-sig") as input_stream:
        reader = csv.DictReader(input_stream)
        required = {"Ref", "PosX", "PosY", "Rot", "Side"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"unexpected KiCad position-file columns: {reader.fieldnames}")
        with destination.open("w", newline="", encoding="utf-8") as output_stream:
            writer = csv.writer(output_stream)
            writer.writerow(["Designator", "Mid X", "Mid Y", "Rotation", "Layer"])
            for row in reader:
                side = row["Side"].strip().lower()
                writer.writerow(
                    [
                        row["Ref"],
                        row["PosX"],
                        row["PosY"],
                        row["Rot"],
                        "Bottom" if side in {"back", "bottom"} else "Top",
                    ]
                )


def archive_fabrication_files(output_dir: Path, archive: Path) -> None:
    """Bundle only Gerber and drill outputs into the fabrication archive."""
    extensions = {
        ".gbr", ".gbl", ".gbo", ".gbp", ".gbs", ".gm1", ".gml",
        ".gko", ".gtl", ".gto", ".gtp", ".gts", ".drl",
    }
    files = sorted(
        path
        for path in output_dir.iterdir()
        if path.suffix.lower() in extensions
        or (path.suffix.lower().startswith(".g") and path.suffix[2:].isdigit())
    )
    if not files:
        raise RuntimeError("KiCad produced no Gerber or drill files")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.name)


def generate(source: Path, kicad_cli: Sequence[str]) -> Path:
    """Run validation and exports for one project, returning its output path."""
    board, schematic = find_project_files(source)
    if schematic is None:
        raise FileNotFoundError(
            f"root schematic not found: {board.with_suffix('.kicad_sch')}"
        )
    reject_unsaved_open_board(board)
    reject_newer_autosaves([schematic, board])

    output_dir = board.parent / "gerber"
    output_dir.mkdir(exist_ok=True)
    project_name = board.stem
    erc_report = board.parent / f"{project_name}-erc.rpt"
    drc_report = board.parent / f"{project_name}-drc.rpt"

    # KiCad calls its schematic design-rule check ERC.  Asking the CLI to use
    # a non-zero exit code for violations makes both checks hard release gates.
    run(
        [
            *kicad_cli, "sch", "erc",
            "--output", str(erc_report),
            "--exit-code-violations",
            str(schematic),
        ]
    )
    run(
        [
            *kicad_cli, "pcb", "drc",
            "--output", str(drc_report),
            "--refill-zones",
            "--save-board",
            "--exit-code-violations",
            str(board),
        ]
    )

    layers = copper_layers(board) + list(GERBER_LAYERS[2:])
    run(
        [
            *kicad_cli, "pcb", "export", "gerbers",
            "--output", str(output_dir),
            "--layers", ",".join(layers),
            "--check-zones",
            str(board),
        ]
    )
    run(
        [
            *kicad_cli, "pcb", "export", "drill",
            "--output", str(output_dir),
            "--format", "excellon",
            "--excellon-units", "mm",
            str(board),
        ]
    )

    raw_positions = output_dir / f".{project_name}-positions-kicad.csv"
    try:
        run(
            [
                *kicad_cli, "pcb", "export", "pos",
                "--output", str(raw_positions),
                "--format", "csv", "--units", "mm", "--side", "both",
                str(board),
            ]
        )
        convert_positions(raw_positions, output_dir / f"{project_name}-positions.csv")
    finally:
        raw_positions.unlink(missing_ok=True)

    netlist = output_dir / f".{project_name}-bom-kicad.xml"
    try:
        run(
            [
                *kicad_cli, "sch", "export", "python-bom",
                "--output", str(netlist), str(schematic),
            ]
        )
        write_bom(netlist, output_dir / f"{project_name}-bom.csv")
    finally:
        netlist.unlink(missing_ok=True)

    archive_fabrication_files(output_dir, output_dir / f"{project_name}-gerbers.zip")
    return output_dir


def parse_args() -> argparse.Namespace:
    """Parse the project selector and optional KiCad CLI override."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project",
        type=Path,
        help=(
            "name under hardware/ (for example led_controller), .kicad_pro, "
            ".kicad_pcb, or directory containing one board"
        ),
    )
    parser.add_argument(
        "--kicad-cli",
        default=None,
        help="path to kicad-cli (default: detect native or Flatpak install)",
    )
    return parser.parse_args()


def main() -> int:
    """Run generation and translate expected failures to a shell exit code."""
    args = parse_args()
    try:
        output_dir = generate(args.project, find_kicad_cli(args.kicad_cli))
    except subprocess.CalledProcessError as error:
        print_failure(error)
        return 1
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print_failure(error)
        return 1
    print(f"JLCPCB files written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
