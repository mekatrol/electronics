#!/usr/bin/env python3
"""Generate JLCPCB files from a generated panelized PCB (no schematic needed).

This script is specifically for ``*_panel_*.kicad_pcb`` files produced by the
panelization scripts. It does not run schematic ERC/parity and does not create
a BOM. The source PCB is validated, its zones are refilled, and fabrication
outputs are written to a dedicated directory beside the panel board.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from generate_jlcpcb import (
    GERBER_LAYERS,
    convert_positions,
    copper_layers,
    find_kicad_cli as find_common_kicad_cli,
    reject_newer_autosaves,
    reject_unsaved_open_board,
    run,
)


def find_panel_kicad_cli(override: str | None = None) -> list[str]:
    """Detect KiCad like the shared exporter, plus its standard Windows path."""
    if override:
        return [override]
    windows = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
    if windows.is_file():
        return [str(windows)]
    return find_common_kicad_cli()


def validate_panel_name(board: Path) -> None:
    """Prevent accidental use on the editable single-board design."""
    if "panel" not in board.stem.lower():
        raise ValueError(
            "this exporter is only for generated panelized PCB files; "
            "the filename must contain 'panel'"
        )


def check_panel_drc(board: Path, cli: list[str], report: Path) -> int:
    """Refill/save and reject every finding except intentional routed tabs."""
    completed = subprocess.run(
        [
            *cli, "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--output", str(report), str(board),
        ],
        text=True,
        capture_output=True,
    )
    if completed.returncode or not report.is_file():
        print(completed.stdout, end="")
        print(completed.stderr, end="", file=sys.stderr)
        raise RuntimeError("KiCad could not validate the panel PCB")
    data = json.loads(report.read_text(encoding="utf-8"))
    unexpected = [
        violation for violation in data.get("violations", [])
        if violation.get("type") != "invalid_outline"
    ]
    unconnected = data.get("unconnected_items", [])
    if unexpected or unconnected:
        types = sorted({str(item.get("type", "unknown")) for item in unexpected})
        detail = ", ".join(types) if types else "none"
        raise RuntimeError(
            f"panel DRC failed: {len(unexpected)} non-tab violation(s) "
            f"({detail}); {len(unconnected)} unconnected item(s). "
            f"See {report}"
        )
    tabs = sum(
        violation.get("type") == "invalid_outline"
        for violation in data.get("violations", [])
    )
    report.unlink(missing_ok=True)
    return tabs


def archive_panel_files(output_dir: Path, archive: Path) -> None:
    """Create a ZIP containing only this isolated output directory's fab files."""
    extensions = {
        ".gbr", ".gbl", ".gbo", ".gbp", ".gbs", ".gm1", ".gml",
        ".gko", ".gtl", ".gto", ".gtp", ".gts", ".drl",
    }
    files = sorted(
        path for path in output_dir.iterdir()
        if path.is_file() and (
            path.suffix.lower() in extensions
            or (path.suffix.lower().startswith(".g") and path.suffix[2:].isdigit())
        )
    )
    if not files:
        raise RuntimeError("KiCad produced no Gerber or drill files")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.name)


def generate_panel(board: Path, cli: list[str], output_dir: Path | None = None) -> Path:
    board = board.resolve()
    if not board.is_file() or board.suffix.lower() != ".kicad_pcb":
        raise FileNotFoundError(f"panel .kicad_pcb not found: {board}")
    validate_panel_name(board)
    reject_unsaved_open_board(board)
    reject_newer_autosaves([board])
    destination = (
        output_dir.resolve() if output_dir
        else board.parent / f"{board.stem}-jlcpcb"
    )
    destination.mkdir(parents=True, exist_ok=True)
    report = destination / f"{board.stem}-panel-drc.json"
    tabs = check_panel_drc(board, cli, report)
    print(
        f"Validated {tabs} intentional routed tab opening(s); "
        "no non-tab DRC violations or unconnected items."
    )

    layers = copper_layers(board) + list(GERBER_LAYERS[2:])
    run([
        *cli, "pcb", "export", "gerbers", "--output", str(destination),
        "--layers", ",".join(layers), "--check-zones", str(board),
    ])
    run([
        *cli, "pcb", "export", "drill", "--output", str(destination),
        "--format", "excellon", "--excellon-units", "mm", str(board),
    ])

    raw_positions = destination / f".{board.stem}-positions-kicad.csv"
    try:
        run([
            *cli, "pcb", "export", "pos", "--output", str(raw_positions),
            "--format", "csv", "--units", "mm", "--side", "both", str(board),
        ])
        convert_positions(raw_positions, destination / f"{board.stem}-positions.csv")
    finally:
        raw_positions.unlink(missing_ok=True)

    archive = destination / f"{board.stem}-gerbers.zip"
    archive_panel_files(destination, archive)
    print(f"Panel fabrication package: {archive}")
    print("No BOM was generated because this PCB-only workflow has no schematic.")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", type=Path, help="generated panelized .kicad_pcb")
    parser.add_argument("--output-dir", type=Path, help="dedicated output directory")
    parser.add_argument("--kicad-cli", help="path to KiCad 10 kicad-cli")
    args = parser.parse_args()
    try:
        generate_panel(args.panel, find_panel_kicad_cli(args.kicad_cli), args.output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
