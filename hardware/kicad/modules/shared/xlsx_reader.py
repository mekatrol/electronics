"""Read worksheet rows from an Office Open XML workbook without dependencies.

Only the small subset of the XLSX format needed by the hardware scripts is
implemented. Cells containing external hyperlinks return the hyperlink target
instead of the cell's potentially shortened display label.
"""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def column_letters(cell_reference: str) -> str:
    """Extract the column letters (for example, ``AB``) from a cell reference."""
    return "".join(character for character in cell_reference if character.isalpha())


def archive_path(base: str, target: str) -> str:
    """Resolve a relationship target relative to its archive member directory."""
    if target.startswith("/"):
        return target.lstrip("/")
    return str(PurePosixPath(base).parent.joinpath(target))


def relationships(workbook: zipfile.ZipFile, member: str) -> dict[str, str]:
    """Read an OOXML relationship file into an ID-to-target mapping."""
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
    sheets = root.findall(f".//{{{SHEET_NS}}}sheet")
    for sheet in sheets:
        if sheet.attrib["name"] == requested_name:
            relation_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
            return archive_path("xl/workbook.xml", rels[relation_id])
    available = ", ".join(sheet.attrib["name"] for sheet in sheets)
    raise ValueError(f"sheet {requested_name!r} not found (available: {available})")


def external_hyperlinks(
    workbook: zipfile.ZipFile, sheet_member: str, sheet_root: ET.Element
) -> dict[str, str]:
    """Map cells to external hyperlink targets when the sheet uses hyperlinks."""
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
    """Read a worksheet as dictionaries keyed by its first row's headings."""
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
                values[column_letters(reference)] = hyperlinks.get(
                    reference, cell_text(cell, strings)
                ).strip()
            raw_rows.append(values)

    if not raw_rows:
        raise ValueError(f"sheet {sheet_name!r} is empty")

    headers = raw_rows[0]
    return [
        {heading: row.get(column, "") for column, heading in headers.items()}
        for row in raw_rows[1:]
        if any(value.strip() for value in row.values())
    ]
