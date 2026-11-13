"""Check an open KiCad schematic BOM against ``components.xlsx`` stock.

The script finds the schematic project currently open in KiCad through its IPC
API::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/check_bom_stock.py
    .venv-kicad-ipc/bin/python hardware/kicad/modules/check_bom_stock.py --minimum-stock 50

The check is read-only.  KiCad's CLI exports a temporary XML netlist so that
hierarchical sheets, library symbol identities, and BOM exclusions are handled
in the same way as the existing manufacturing scripts.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import kicad_netlist_reader
from kicad_discovery import find_kicad_cli
from xlsx_reader import read_rows

HARDWARE_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = HARDWARE_DIR.parent
IPC_PYTHON = REPOSITORY_DIR / ".venv-kicad-ipc" / "bin" / "python"
IPC_SCHEMATIC_FINDER = Path(__file__).with_name("find_open_schematic.py")
DEFAULT_WORKBOOK = HARDWARE_DIR / "components.xlsx"
DEFAULT_SHEET = "Stock"
DEFAULT_MINIMUM_STOCK = 10
NOT_APPLICABLE = "N/A"

# References matching any of these regular expressions are excluded from
# BOM-to-stock validation. Matching is case-insensitive and covers the
# complete reference designator (e.g. H1, H22, FID3).
IGNORED_DESIGNATOR_PATTERNS = (
    r"FID\d+",
    r"H\d+",
)

VALUE_COLUMN = "Value"
PART_COLUMN = "Supplier Part #"
SYMBOL_COLUMN = "KiCad 10 Symbol"
FOOTPRINT_COLUMN = "KiCad 10 Footprint"
STOCK_COLUMN = "QTY Total"
DATASHEET_COLUMN = "LCSC Datasheet"
REQUIRED_COLUMNS = (
    VALUE_COLUMN,
    PART_COLUMN,
    SYMBOL_COLUMN,
    FOOTPRINT_COLUMN,
    STOCK_COLUMN,
    DATASHEET_COLUMN,
)


@dataclass(frozen=True)
class StockPart:
    """The workbook fields used to identify and validate one stocked part."""

    row: int
    value: str
    lcsc: str
    symbol: str
    footprint: str
    quantity: float
    datasheet: str


@dataclass(frozen=True)
class BomPart:
    """The schematic fields checked for one or more equivalent references."""

    references: tuple[str, ...]
    value: str
    lcsc: str
    symbol: str
    footprint: str
    datasheet: str


def is_excluded_from_bom(component: object) -> bool:
    """Return whether KiCad marked a netlist component as excluded from BOMs."""
    return any(
        prop.attributes.get("name") == "exclude_from_bom"
        for prop in component.element.getChildren("property")
    )


def clean(value: str) -> str:
    """Strip values before comparison or display."""
    return (value or "").strip()


def key(value: str) -> str:
    """Return a case-insensitive identity key without changing display text."""
    return clean(value).casefold()


def parse_quantity(value: str, row: int) -> float:
    """Parse an Excel quantity and give a row-specific error when invalid."""
    try:
        return float(clean(value).replace(",", ""))
    except ValueError as error:
        raise ValueError(
            f"workbook row {row}: invalid {STOCK_COLUMN} {value!r}"
        ) from error


def load_stock(workbook: Path, sheet: str) -> list[StockPart]:
    """Load non-empty stock rows using the shared OOXML workbook reader."""
    rows = read_rows(workbook, sheet)
    missing = [column for column in REQUIRED_COLUMNS if column not in rows[0]]
    if missing:
        raise ValueError(f"workbook is missing columns: {', '.join(missing)}")

    parts: list[StockPart] = []
    for row_number, row in enumerate(rows, start=2):
        # The workbook contains formatted placeholder rows; they are not parts.
        if not clean(row[VALUE_COLUMN]):
            continue
        parts.append(
            StockPart(
                row=row_number,
                value=clean(row[VALUE_COLUMN]),
                lcsc=clean(row[PART_COLUMN]),
                symbol=clean(row[SYMBOL_COLUMN]),
                footprint=clean(row[FOOTPRINT_COLUMN]),
                quantity=parse_quantity(row[STOCK_COLUMN], row_number),
                datasheet=clean(row[DATASHEET_COLUMN]),
            )
        )
    if not parts:
        raise ValueError(f"sheet {sheet!r} contains no stock parts")
    return parts


def find_open_schematic() -> Path:
    """Return the root schematic reported by KiCad's supported IPC API."""
    if not IPC_PYTHON.is_file():
        raise FileNotFoundError(f"KiCad IPC Python environment not found: {IPC_PYTHON}")
    completed = subprocess.run(
        [str(IPC_PYTHON), str(IPC_SCHEMATIC_FINDER)],
        text=True,
        capture_output=True,
        check=False,
        timeout=8,
    )
    if completed.returncode:
        message = completed.stderr.strip() or "KiCad did not return an open schematic"
        raise RuntimeError(message)
    schematic = Path(completed.stdout.strip()).resolve()
    if not schematic.is_file():
        raise FileNotFoundError(f"open schematic not found on disk: {schematic}")
    return schematic


def resolve_schematic(source: Path | None) -> Path:
    """Resolve an optional project selector to its root schematic."""
    if source is None:
        return find_open_schematic()
    if not source.exists() and len(source.parts) == 1 and not source.suffix:
        source = HARDWARE_DIR / source
    source = source.resolve()
    if source.is_dir():
        candidate = source / f"{source.name}.kicad_sch"
    elif source.suffix in {".kicad_pro", ".pro"}:
        candidate = source.with_suffix(".kicad_sch")
    elif source.suffix == ".kicad_sch":
        candidate = source
    else:
        raise ValueError(
            "input must be a schematic, KiCad project, or project directory"
        )
    if not candidate.is_file():
        raise FileNotFoundError(f"schematic not found: {candidate}")
    return candidate


def bom_parts(netlist_file: Path) -> list[BomPart]:
    """Read and group BOM components from a KiCad XML netlist."""
    netlist = kicad_netlist_reader.netlist(str(netlist_file))
    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for component in netlist.getInterestingComponents():
        if is_excluded_from_bom(component):
            continue
        reference = clean(component.getRef())
        if any(
            re.fullmatch(pattern, reference, flags=re.IGNORECASE)
            for pattern in IGNORED_DESIGNATOR_PATTERNS
        ):
            continue
        identity = (
            clean(component.getValue()),
            clean(component.getField("LCSC Part #")),
            f"{clean(component.getLibName())}:{clean(component.getPartName())}",
            clean(component.getFootprint()),
            clean(component.getDatasheet()),
        )
        grouped[identity].append(reference)
    return [
        BomPart(tuple(sorted(refs)), *identity)
        for identity, refs in sorted(grouped.items(), key=lambda item: item[1][0])
    ]


def matching_score(part: StockPart, bom: BomPart) -> int:
    """Rank same-value rows when an explicit LCSC identity is intentionally absent."""
    return sum(
        key(actual) == key(expected)
        for actual, expected in (
            (part.symbol, bom.symbol),
            (part.footprint, bom.footprint),
            (part.datasheet, bom.datasheet),
        )
    )


def select_stock_part(
    bom: BomPart,
    by_value: dict[str, list[StockPart]],
    by_lcsc: dict[str, list[StockPart]],
) -> tuple[StockPart | None, list[str]]:
    """Select the stock identity and report missing or ambiguous mappings."""
    label = ",".join(bom.references)
    value_matches = by_value.get(key(bom.value), [])
    errors: list[str] = []
    if not value_matches:
        errors.append(f"{label}: value {bom.value!r} does not exist in the workbook")

    if not bom.lcsc:
        errors.append(
            f"{label}: LCSC Part # is not assigned (use {NOT_APPLICABLE} to opt out)"
        )
        return None, errors

    if key(bom.lcsc) != key(NOT_APPLICABLE):
        lcsc_matches = by_lcsc.get(key(bom.lcsc), [])
        if not lcsc_matches:
            errors.append(
                f"{label}: LCSC Part # {bom.lcsc!r} does not exist in the workbook"
            )
            return None, errors
        if len(lcsc_matches) > 1:
            rows = ", ".join(str(part.row) for part in lcsc_matches)
            errors.append(
                f"{label}: LCSC Part # {bom.lcsc!r} is duplicated in workbook rows {rows}"
            )
            return None, errors
        part = lcsc_matches[0]
        if key(part.value) != key(bom.value):
            errors.append(
                f"{label}: value {bom.value!r} does not match workbook row {part.row} value {part.value!r}"
            )
        return part, errors

    # N/A explicitly opts out of LCSC matching.  Prefer the same-value row that
    # agrees with the most schematic metadata, but reject tied identities.
    if not value_matches:
        return None, errors
    best_score = max(matching_score(part, bom) for part in value_matches)
    best = [part for part in value_matches if matching_score(part, bom) == best_score]
    if len(best) != 1:
        rows = ", ".join(str(part.row) for part in best)
        errors.append(
            f"{label}: value {bom.value!r} is ambiguous in workbook rows {rows}"
        )
        return None, errors
    return best[0], errors


def check_parts(
    parts: Iterable[BomPart],
    stock: Iterable[StockPart],
    minimum: float,
) -> list[str]:
    """Return every BOM-to-stock validation failure."""
    stock = list(stock)
    by_value: dict[str, list[StockPart]] = defaultdict(list)
    by_lcsc: dict[str, list[StockPart]] = defaultdict(list)
    for part in stock:
        by_value[key(part.value)].append(part)
        if part.lcsc:
            by_lcsc[key(part.lcsc)].append(part)

    errors: list[str] = []
    for bom in parts:
        label = ",".join(bom.references)
        part, selection_errors = select_stock_part(bom, by_value, by_lcsc)
        errors.extend(selection_errors)
        if part is None:
            continue

        for field, actual, expected in (
            ("symbol", bom.symbol, part.symbol),
            ("footprint", bom.footprint, part.footprint),
            ("datasheet", bom.datasheet, part.datasheet),
        ):
            if key(actual) != key(expected):
                errors.append(
                    f"{label}: {field} {actual!r} does not match workbook row "
                    f"{part.row} {expected!r}"
                )
        if part.quantity < minimum:
            errors.append(
                f"{label}: workbook row {part.row} has {part.quantity:g} in stock; "
                f"minimum is {minimum:g}"
            )
    return errors


def export_netlist(command: Sequence[str], schematic: Path, output: Path) -> None:
    """Export the XML netlist consumed by the repository's BOM reader."""
    subprocess.run(
        [
            *command,
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "--output",
            str(output),
            str(schematic),
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse schematic selection and stock-check settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schematic", nargs="?", type=Path)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--sheet", default=DEFAULT_SHEET)
    parser.add_argument("--minimum-stock", type=float, default=DEFAULT_MINIMUM_STOCK)
    parser.add_argument("--kicad-cli", help="path to kicad-cli")
    return parser.parse_args()


def main() -> int:
    """Export the selected BOM, validate it, and return a CI-friendly status."""
    args = parse_args()
    try:
        if args.minimum_stock < 0:
            raise ValueError("--minimum-stock cannot be negative")
        schematic = resolve_schematic(args.schematic)
        stock = load_stock(args.workbook.resolve(), args.sheet)
        command = find_kicad_cli(args.kicad_cli)
        if command is None:
            raise FileNotFoundError("kicad-cli was not found")
        # Flatpak gives applications a private /tmp.  Keep the transient export
        # beside this script so both a native or Flatpak CLI and this process see
        # the same file.
        with tempfile.TemporaryDirectory(
            prefix=".check-bom-stock-", dir=Path(__file__).resolve().parent
        ) as temporary:
            netlist = Path(temporary) / "bom.xml"
            export_netlist(command, schematic, netlist)
            parts = bom_parts(netlist)
        errors = check_parts(parts, stock, args.minimum_stock)
    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"BOM stock check failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    references = sum(len(part.references) for part in parts)
    print(
        f"BOM stock check passed: {references} component(s), "
        f"minimum stock {args.minimum_stock:g}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
