#!/usr/bin/env python3
"""Generate JLCPCB fabrication and assembly files from a KiCad project.

The output is written to a ``gerber`` directory beside the board:

* one Gerber per manufacturing layer and Excellon drill file(s)
* ``<project>-gerbers.zip`` for upload as the PCB fabrication file
* ``<project>-bom.csv``
* ``<project>-positions.csv`` (CPL / centroid / pick-and-place)

KiCad 7 or newer, its ``kicad-cli`` executable, and its ``pcbnew`` Python
module are required.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
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
REFILL_ZONES_SCRIPT = """\
import pcbnew
import sys

board = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[1], board)
"""


def run(command: Sequence[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


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


def find_pcbnew_python(kicad_cli: Sequence[str]) -> list[str]:
    """Return a Python command that can import the matching pcbnew module."""
    command = list(kicad_cli)
    try:
        flatpak_command = command.index("--command=kicad-cli")
    except ValueError:
        python = shutil.which("python3")
        if python:
            return [python]
        raise FileNotFoundError(
            "python3 was not found; it is required to persist refilled zones"
        )

    command[flatpak_command] = "--command=python3"
    return command


def refill_zones(board: Path, kicad_cli: Sequence[str]) -> None:
    """Refill every copper zone and save the result into the board file."""
    run([*find_pcbnew_python(kicad_cli), "-c", REFILL_ZONES_SCRIPT, str(board)])


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
        paths = ", ".join(str(path) for path in newer_autosaves)
        raise RuntimeError(
            "newer KiCad autosave file(s) found; save the open project before "
            f"generating manufacturing files: {paths}"
        )


def copper_layers(board: Path) -> list[str]:
    """Read enabled copper layer names without requiring the pcbnew Python API."""
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
    board, schematic = find_project_files(source)
    if schematic is None:
        raise FileNotFoundError(
            f"root schematic not found: {board.with_suffix('.kicad_sch')}"
        )
    reject_newer_autosaves([schematic, board])

    output_dir = board.parent / "gerber"
    output_dir.mkdir(exist_ok=True)
    project_name = board.stem
    erc_report = board.parent / f"{project_name}-erc.rpt"
    drc_report = board.parent / f"{project_name}-drc.rpt"

    refill_zones(board, kicad_cli)

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
    args = parse_args()
    try:
        output_dir = generate(args.project, find_kicad_cli(args.kicad_cli))
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"JLCPCB files written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
