#!/usr/bin/env python3
"""Download and consistently name datasheets listed in an Excel workbook.

Run from the hardware repository root with::

    ./fetch_datasheets.py

Preview the changes without downloading or renaming files with::

    ./fetch_datasheets.py --dry-run

By default, the script reads the ``Stock`` sheet in ``components.xlsx`` and
writes PDFs to ``datasheets/``.  Run ``./fetch_datasheets.py --help`` to see
options for changing the workbook, sheet, URL column, output, and timeout.

This script deliberately uses only Python's standard library.  In particular, it
reads the small amount of XML needed from an .xlsx file instead of requiring
openpyxl, and it uses urllib for HTTPS downloads.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

# Add characters to this list when they should be converted to underscores in
# generated filenames.  A later cleanup step collapses consecutive underscores.
REPLACE_WITH_UNDERSCORE = [" ", "-", "."]

# User setting: directory where downloaded datasheets will be stored.
OUTPUT_DIRECTORY = Path("datasheets")

# These are the workbook columns used to build the filename and stable identity.
FUNCTION_COLUMN = "Function"
PART_NAME_COLUMN = "Part Name"
SUPPLIER_COLUMN = "Supplier"
PART_NUMBER_COLUMN = "Part No"
DEFAULT_URL_COLUMN = "LCSC Datasheet"

# XML namespaces used by the Office Open XML (.xlsx) file format.
SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


@dataclass(frozen=True)
class Datasheet:
    """One validated datasheet row from the workbook."""

    row_number: int
    function: str
    part_name: str
    supplier: str
    part_number: str
    url: str

    @property
    def identity(self) -> str:
        """Return a case-insensitive supplier/part-number identity key."""

        return f"{self.supplier.casefold()}\0{self.part_number.casefold()}"

    @property
    def filename(self) -> str:
        """Return the required descriptive, lowercase PDF filename."""

        fields = (self.function, self.part_name, self.supplier, self.part_number)
        return "_".join(filename_component(field) for field in fields) + ".pdf"


@dataclass
class Results:
    """Counters collected for the final run summary."""

    rows_with_urls: int = 0
    downloaded: int = 0
    renamed: int = 0
    already_current: int = 0
    would_download: int = 0
    would_rename: int = 0
    errors: int = 0


def filename_component(value: str) -> str:
    """Convert a workbook value into a safe, lowercase filename component."""

    # Normalize accented characters so filenames remain portable between systems.
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii").lower()

    # Keep the requested substitutions in an easy-to-extend array.
    for character in REPLACE_WITH_UNDERSCORE:
        value = value.replace(character, "_")

    # Replace any other filesystem-unfriendly run with one underscore as a safety
    # measure, then ensure replacements never create consecutive underscores.
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unnamed"


def column_letters(cell_reference: str) -> str:
    """Extract the column letters (for example, 'AB') from an Excel cell ref."""

    return "".join(character for character in cell_reference if character.isalpha())


def archive_path(base: str, target: str) -> str:
    """Resolve a relationship target relative to its archive member directory."""

    if target.startswith("/"):
        return target.lstrip("/")
    return str(PurePosixPath(base).parent.joinpath(target))


def relationships(workbook: zipfile.ZipFile, member: str) -> dict[str, str]:
    """Read an OOXML .rels file into an ID-to-target mapping."""

    root = ET.fromstring(workbook.read(member))
    return {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in root.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
    }


def shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    """Read the workbook's optional shared-string table."""

    try:
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    except KeyError:
        return []

    # Rich-text cells can contain several <t> nodes, so concatenate all of them.
    return [
        "".join(text.text or "" for text in item.iter(f"{{{SHEET_NS}}}t"))
        for item in root.findall(f"{{{SHEET_NS}}}si")
    ]


def cell_text(cell: ET.Element, strings: list[str]) -> str:
    """Return the display text for a shared, inline, or ordinary Excel cell."""

    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.iter(f"{{{SHEET_NS}}}t"))

    value = cell.find(f"{{{SHEET_NS}}}v")
    raw = "" if value is None else value.text or ""
    if cell_type == "s" and raw:
        return strings[int(raw)]
    return raw


def find_sheet_member(workbook: zipfile.ZipFile, requested_name: str) -> str:
    """Find an Excel worksheet archive member by its visible sheet name."""

    root = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels = relationships(workbook, "xl/_rels/workbook.xml.rels")
    for sheet in root.findall(f".//{{{SHEET_NS}}}sheet"):
        if sheet.attrib["name"] == requested_name:
            relation_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
            return archive_path("xl/workbook.xml", rels[relation_id])
    available = ", ".join(
        sheet.attrib["name"] for sheet in root.findall(f".//{{{SHEET_NS}}}sheet")
    )
    raise ValueError(f"sheet {requested_name!r} not found (available: {available})")


def external_hyperlinks(
    workbook: zipfile.ZipFile, sheet_member: str, sheet_root: ET.Element
) -> dict[str, str]:
    """Map cells to external hyperlink targets, when the sheet uses hyperlinks."""

    path = PurePosixPath(sheet_member)
    rels_member = str(path.parent / "_rels" / f"{path.name}.rels")
    try:
        rels = relationships(workbook, rels_member)
    except KeyError:
        return {}

    links: dict[str, str] = {}
    for hyperlink in sheet_root.findall(f".//{{{SHEET_NS}}}hyperlink"):
        relation_id = hyperlink.attrib.get(f"{{{OFFICE_REL_NS}}}id")
        if relation_id in rels:
            links[hyperlink.attrib["ref"]] = rels[relation_id]
    return links


def read_rows(workbook_path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read a worksheet as dictionaries keyed by the first row's headings."""

    with zipfile.ZipFile(workbook_path) as workbook:
        strings = shared_strings(workbook)
        sheet_member = find_sheet_member(workbook, sheet_name)
        root = ET.fromstring(workbook.read(sheet_member))
        hyperlinks = external_hyperlinks(workbook, sheet_member, root)

        raw_rows: list[dict[str, str]] = []
        for row in root.findall(f".//{{{SHEET_NS}}}sheetData/{{{SHEET_NS}}}row"):
            values: dict[str, str] = {}
            for cell in row.findall(f"{{{SHEET_NS}}}c"):
                reference = cell.attrib["r"]
                # Prefer a hyperlink target over its potentially shortened label.
                values[column_letters(reference)] = hyperlinks.get(
                    reference, cell_text(cell, strings)
                ).strip()
            raw_rows.append(values)

    if not raw_rows:
        raise ValueError(f"sheet {sheet_name!r} is empty")

    headers = raw_rows[0]
    return [
        # Include empty cells as empty strings.  Besides simplifying validation,
        # this preserves the fact that a completely empty URL column still exists.
        {heading: row.get(column, "") for column, heading in headers.items()}
        for row in raw_rows[1:]
        if any(value.strip() for value in row.values())
    ]


def datasheets_from_rows(
    rows: Iterable[dict[str, str]], url_column: str
) -> tuple[list[Datasheet], list[str]]:
    """Validate relevant rows and turn them into Datasheet objects."""

    required = [FUNCTION_COLUMN, PART_NAME_COLUMN, SUPPLIER_COLUMN, PART_NUMBER_COLUMN]
    sheets: list[Datasheet] = []
    errors: list[str] = []
    identities: dict[str, int] = {}

    # Row 1 contains headers, so the first record corresponds to Excel row 2.
    for row_number, row in enumerate(rows, start=2):
        url = row.get(url_column, "").strip()
        if not url:
            continue
        missing = [column for column in required if not row.get(column, "").strip()]
        if missing:
            errors.append(f"row {row_number}: missing {', '.join(missing)}")
            continue

        sheet = Datasheet(
            row_number=row_number,
            function=row[FUNCTION_COLUMN].strip(),
            part_name=row[PART_NAME_COLUMN].strip(),
            supplier=row[SUPPLIER_COLUMN].strip(),
            part_number=row[PART_NUMBER_COLUMN].strip(),
            url=url,
        )
        if sheet.identity in identities:
            errors.append(
                f"row {row_number}: supplier/part number duplicates row "
                f"{identities[sheet.identity]} ({sheet.supplier} {sheet.part_number})"
            )
            continue
        identities[sheet.identity] = row_number
        sheets.append(sheet)

    return sheets, errors


def identity_suffix(sheet: Datasheet) -> str:
    """Return the stable supplier/part-number suffix used to find a PDF."""

    return f"_{filename_component(sheet.supplier)}_{filename_component(sheet.part_number)}.pdf"


def locate_existing(sheet: Datasheet, output: Path) -> Path | None:
    """Locate an existing PDF by its stable supplier/part-number suffix."""

    expected = output / sheet.filename
    if expected.is_file():
        return expected

    # Function and part-name edits change the beginning of the filename, while
    # this suffix remains stable because supplier + part number is the unique key.
    matches = [
        candidate
        for candidate in output.glob("*.pdf")
        if candidate.name.casefold().endswith(identity_suffix(sheet).casefold())
    ]
    return matches[0] if len(matches) == 1 else None


def download_pdf(url: str, destination: Path, timeout: float) -> None:
    """Download one PDF to a temporary file and atomically move it into place."""

    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "components-datasheet-downloader/1.0"},
    )
    try:
        with (
            urllib.request.urlopen(request, timeout=timeout) as response,
            temporary.open("wb") as file,
        ):
            first_chunk = response.read(64 * 1024)
            if not first_chunk.startswith(b"%PDF-"):
                raise ValueError("response is not a PDF (missing %PDF header)")
            file.write(first_chunk)
            while chunk := response.read(64 * 1024):
                file.write(chunk)
        os.replace(temporary, destination)
    finally:
        # Remove an incomplete file after network, validation, or disk failures.
        temporary.unlink(missing_ok=True)


def process(
    sheets: list[Datasheet], output: Path, timeout: float, dry_run: bool
) -> tuple[Results, list[str]]:
    """Rename existing files or download missing ones, returning a run summary."""

    results = Results(rows_with_urls=len(sheets))
    errors: list[str] = []

    if not dry_run:
        output.mkdir(parents=True, exist_ok=True)

    for sheet in sheets:
        expected = output / sheet.filename
        existing = locate_existing(sheet, output)
        try:
            if existing and existing != expected:
                if expected.exists():
                    raise FileExistsError(
                        f"rename target already exists: {expected.name}"
                    )
                if dry_run:
                    print(f"WOULD RENAME  {existing.name} -> {expected.name}")
                    results.would_rename += 1
                else:
                    existing.rename(expected)
                    print(f"RENAMED       {existing.name} -> {expected.name}")
                    results.renamed += 1
            elif existing:
                print(f"CURRENT       {expected.name}")
                results.already_current += 1
            elif dry_run:
                print(f"WOULD DOWNLOAD {sheet.url} -> {expected.name}")
                results.would_download += 1
            else:
                download_pdf(sheet.url, expected, timeout)
                print(f"DOWNLOADED    {expected.name}")
                results.downloaded += 1

        except (OSError, ValueError, urllib.error.URLError) as error:
            results.errors += 1
            errors.append(
                f"row {sheet.row_number} ({sheet.supplier} {sheet.part_number}): {error}"
            )

    return results, errors


def parse_args() -> argparse.Namespace:
    """Define and parse the command-line interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("components.xlsx"))
    parser.add_argument(
        "--sheet", default="Stock", help="worksheet name (default: Stock)"
    )
    parser.add_argument(
        "--url-column",
        default=DEFAULT_URL_COLUMN,
        help=f"datasheet URL column heading (default: {DEFAULT_URL_COLUMN!r})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIRECTORY,
        help=f"PDF output directory (default: {OUTPUT_DIRECTORY})",
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="per-request timeout in seconds"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show downloads and renames without changing files",
    )
    return parser.parse_args()


def print_summary(results: Results, errors: list[str], dry_run: bool) -> None:
    """Print a concise but complete summary at the end of every run."""

    print("\nSummary")
    print(f"  Datasheet rows:       {results.rows_with_urls}")
    print(f"  Downloaded:           {results.downloaded}")
    print(f"  Renamed:              {results.renamed}")
    print(f"  Already current:      {results.already_current}")
    if dry_run:
        print(f"  Would download:       {results.would_download}")
        print(f"  Would rename:         {results.would_rename}")
    print(f"  Errors:               {len(errors)}")
    if errors:
        print("\nErrors")
        for error in errors:
            print(f"  - {error}")


def main() -> int:
    """Run the downloader and return a shell-friendly exit status."""

    args = parse_args()
    errors: list[str] = []
    try:
        rows = read_rows(args.workbook, args.sheet)
        if rows and args.url_column not in rows[0]:
            raise ValueError(f"URL column {args.url_column!r} was not found")
        sheets, validation_errors = datasheets_from_rows(rows, args.url_column)
        results, processing_errors = process(
            sheets, args.output, args.timeout, args.dry_run
        )
        errors.extend(validation_errors)
        errors.extend(processing_errors)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        results = Results()
        errors.append(str(error))

    print_summary(results, errors, args.dry_run)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
