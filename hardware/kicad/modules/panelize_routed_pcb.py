#!/usr/bin/env python3
"""Create a routed mouse-bite panel while preserving castellated edges.

Unlike panelize_pcb.py (V-score), this copies each source Edge.Cuts outline.
Straight sections at the middle of each side are opened for breakaway tabs and
0.6 mm NPTH mouse-bite holes. The source PCB is read only.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
from pathlib import Path

from panelize_pcb import (
    Bounds, STRUCTURAL, children, dump_sexpr, edge_bounds, fiducial,
    find_fiducial_library_file, find_kicad_cli, first_child, graphic_line, head,
    load_fiducial_template, number, parse_sexpr, quoted, remap_nets,
    remove_zone_fills, renew_uuids, translate_item,
)


MIN_GAP_MM = 2.0
MIN_TAB_WIDTH_MM = 5.0
FIDUCIAL_EDGE_OFFSET_MM = 3.85
TOOLING_HOLE_DIAMETER_MM = 2.0
TOOLING_HOLE_EDGE_OFFSET_MM = 2.5


def is_edge_item(item: list) -> bool:
    layer = first_child(item, "layer")
    return bool(layer and len(layer) >= 2 and str(layer[1]).strip('"') == "Edge.Cuts")


def split_tab_line(item: list, bounds: Bounds, tab_width: float) -> list[list] | None:
    """Split a straight outer-edge segment around one centred tab opening."""
    if head(item) != "gr_line" or not is_edge_item(item):
        return None
    start, end = first_child(item, "start"), first_child(item, "end")
    if not start or not end:
        return None
    x1, y1, x2, y2 = map(float, (start[1], start[2], end[1], end[2]))
    tolerance = 1e-6
    horizontal_side = abs(y1 - y2) < tolerance and (
        abs(y1 - bounds.top) < tolerance or abs(y1 - bounds.bottom) < tolerance
    )
    # Tabs deliberately use only the top/bottom edges. The sample board has
    # castellated PTHs on both vertical edges, where a mouse-bite row would
    # collide with the plated holes and prevent a clean routing pass.
    if not horizontal_side:
        return None

    centre = (bounds.left + bounds.right) / 2
    low, high = centre - tab_width / 2, centre + tab_width / 2
    a, b = sorted((x1, x2))
    if low <= a + tolerance or high >= b - tolerance:
        return None

    def piece(first: float, second: float) -> list:
        result = copy.deepcopy(item)
        renew_uuids(result)
        result_start, result_end = first_child(result, "start"), first_child(result, "end")
        result_start[1:3], result_end[1:3] = [number(first), number(y1)], [number(second), number(y1)]
        return result

    return [piece(a, low), piece(high, b)]


def npth_hole(reference: str, value: str, x: float, y: float, diameter: float) -> list:
    """Create a board-only NPTH drill with no library association."""
    import uuid
    return [
        "footprint", quoted(""), ["layer", quoted("F.Cu")],
        ["uuid", quoted(str(uuid.uuid4()))], ["at", number(x), number(y)],
        ["property", quoted("Reference"), quoted(reference), ["at", "0", "0", "0"],
         ["layer", quoted("F.Fab")], ["hide", "yes"],
         ["effects", ["font", ["size", "0.5", "0.5"], ["thickness", "0.08"]]]],
        ["property", quoted("Value"), quoted(value), ["at", "0", "0", "0"],
         ["layer", quoted("F.Fab")], ["hide", "yes"],
         ["effects", ["font", ["size", "0.5", "0.5"], ["thickness", "0.08"]]]],
        ["attr", "board_only", "exclude_from_pos_files", "exclude_from_bom"],
        ["pad", quoted(""), "np_thru_hole", "circle", ["at", "0", "0"],
         ["size", number(diameter), number(diameter)], ["drill", number(diameter)],
         ["layers", quoted("*.Cu"), quoted("*.Mask")],
         ["uuid", quoted(str(uuid.uuid4()))]],
        ["embedded_fonts", "no"],
    ]


def mouse_bite(reference: str, x: float, y: float, diameter: float) -> list:
    return npth_hole(reference, "MouseBite", x, y, diameter)


def bite_positions(centre: float, tab_width: float, diameter: float, clearance: float) -> list[float]:
    pitch = diameter + clearance
    count = max(2, math.floor((tab_width + clearance) / pitch))
    span = (count - 1) * pitch
    return [centre - span / 2 + index * pitch for index in range(count)]


def build_routed_panel(
    source: list, count_x: int, count_y: int, gap: float, rail: float,
    tab_width: float, bite_diameter: float, bite_clearance: float,
    fiducial_template: list,
) -> tuple[list, Bounds]:
    if gap < MIN_GAP_MM:
        raise ValueError(f"gap must be at least {MIN_GAP_MM:.1f} mm for JLCPCB routing")
    if rail < 5.0:
        raise ValueError("rail must be at least 5 mm for JLCPCB SMT assembly")
    if tab_width < MIN_TAB_WIDTH_MM:
        raise ValueError("mouse-bite tab width must be at least 5 mm")
    if not 0.5 <= bite_diameter <= 0.8:
        raise ValueError("mouse-bite diameter must be 0.5 to 0.8 mm")
    if not 0.2 <= bite_clearance <= 0.3:
        raise ValueError("mouse-bite edge clearance must be 0.2 to 0.3 mm")
    bounds = edge_bounds(source)
    width = count_x * bounds.width + (count_x - 1) * gap + 2 * rail
    height = count_y * bounds.height + (count_y - 1) * gap + 2 * rail
    result = ["kicad_pcb"]
    result.extend(copy.deepcopy(item) for item in source[1:]
                  if isinstance(item, list) and head(item) in STRUCTURAL)
    source_items = [item for item in source[1:] if isinstance(item, list) and head(item) not in STRUCTURAL]
    bite_number = 1
    for row in range(count_y):
        for column in range(count_x):
            suffix = f"@X{column + 1}Y{row + 1}"
            dx = rail + column * (bounds.width + gap) - bounds.left
            dy = rail + row * (bounds.height + gap) - bounds.top
            split_sides: set[str] = set()
            for original in source_items:
                pieces = split_tab_line(original, bounds, tab_width)
                if pieces:
                    x = float(first_child(original, "start")[1])
                    y = float(first_child(original, "start")[2])
                    if abs(x - bounds.left) < 1e-6: split_sides.add("left")
                    elif abs(x - bounds.right) < 1e-6: split_sides.add("right")
                    elif abs(y - bounds.top) < 1e-6: split_sides.add("top")
                    else: split_sides.add("bottom")
                    for item in pieces:
                        translate_item(item, dx, dy)
                        result.append(item)
                    continue
                item = copy.deepcopy(original)
                renew_uuids(item)
                remap_nets(item, {}, suffix)
                translate_item(item, dx, dy)
                remove_zone_fills(item)
                result.append(item)
            if split_sides != {"top", "bottom"}:
                missing = ", ".join(sorted({"top", "bottom"} - split_sides))
                raise ValueError(f"source has no straight section long enough for a {tab_width:g} mm tab on: {missing}")
            x0, x1 = rail + column * (bounds.width + gap), rail + column * (bounds.width + gap) + bounds.width
            y0, y1 = rail + row * (bounds.height + gap), rail + row * (bounds.height + gap) + bounds.height
            for x in bite_positions((x0 + x1) / 2, tab_width, bite_diameter, bite_clearance):
                for y in (y0, y1):
                    result.append(mouse_bite(f"MB{bite_number}", x, y, bite_diameter)); bite_number += 1
    fiducial_x_left = rail + 5.0
    fiducial_x_right = width - rail - 5.0
    tooling_inset = TOOLING_HOLE_EDGE_OFFSET_MM
    result.extend([
        graphic_line(0, 0, width, 0, "Edge.Cuts", 0.1),
        graphic_line(width, 0, width, height, "Edge.Cuts", 0.1),
        graphic_line(width, height, 0, height, "Edge.Cuts", 0.1),
        graphic_line(0, height, 0, 0, "Edge.Cuts", 0.1),
        # Four global fiducials sit in the horizontal process rails. Their Y
        # centres satisfy JLCPCB's 3.85 mm edge offset, while moving them away
        # from the corners leaves clearance for the four tooling holes.
        fiducial(fiducial_template, "PFID1", fiducial_x_left, FIDUCIAL_EDGE_OFFSET_MM),
        fiducial(fiducial_template, "PFID2", fiducial_x_right, FIDUCIAL_EDGE_OFFSET_MM),
        fiducial(fiducial_template, "PFID3", fiducial_x_left, height - FIDUCIAL_EDGE_OFFSET_MM),
        fiducial(fiducial_template, "PFID4", fiducial_x_right, height - FIDUCIAL_EDGE_OFFSET_MM),
        # JLCPCB panel tooling holes: four 2 mm NPTH holes in the process-rail
        # corners, 2.5 mm from each panel edge and clear of the fiducials.
        npth_hole("TH1", "PanelToolingHole_2mm", tooling_inset, tooling_inset, TOOLING_HOLE_DIAMETER_MM),
        npth_hole("TH2", "PanelToolingHole_2mm", width - tooling_inset, tooling_inset, TOOLING_HOLE_DIAMETER_MM),
        npth_hole("TH3", "PanelToolingHole_2mm", tooling_inset, height - tooling_inset, TOOLING_HOLE_DIAMETER_MM),
        npth_hole("TH4", "PanelToolingHole_2mm", width - tooling_inset, height - tooling_inset, TOOLING_HOLE_DIAMETER_MM),
        ["embedded_fonts", "no"],
    ])
    return result, Bounds(0, 0, width, height)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-x", "--count-x", type=int, required=True)
    parser.add_argument("-y", "--count-y", type=int, required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--gap", type=float, default=2.0, help="routed space between PCBs (minimum/default: 2 mm)")
    parser.add_argument("--rail", type=float, default=5.0)
    parser.add_argument("--tab-width", type=float, default=5.0)
    parser.add_argument("--mouse-bite-diameter", type=float, default=0.6)
    parser.add_argument("--mouse-bite-clearance", type=float, default=0.25)
    parser.add_argument("--fiducial-footprint", type=Path)
    parser.add_argument("--kicad-cli")
    parser.add_argument("--no-kicad-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.count_x < 1 or args.count_y < 1:
        raise SystemExit("count-x and count-y must be positive")
    source_path = args.input.resolve()
    output_path = (args.output or source_path.with_name(
        f"{source_path.stem}_routed_panel_{args.count_x}x{args.count_y}.kicad_pcb"
    )).resolve()
    if source_path == output_path:
        raise SystemExit("output must differ from input")
    if output_path.exists() and not args.force:
        raise SystemExit(f"output already exists: {output_path} (use --force)")
    source_bytes = source_path.read_bytes()
    source = parse_sexpr(source_bytes.decode("utf-8-sig"))
    fid_path = find_fiducial_library_file(args.fiducial_footprint)
    panel, panel_bounds = build_routed_panel(
        source, args.count_x, args.count_y, args.gap, args.rail, args.tab_width,
        args.mouse_bite_diameter, args.mouse_bite_clearance,
        load_fiducial_template(fid_path),
    )
    output_path.write_text(dump_sexpr(panel) + "\n", encoding="utf-8", newline="\n")
    if not args.no_kicad_check:
        cli = find_kicad_cli(args.kicad_cli)
        if not cli:
            output_path.unlink(missing_ok=True)
            raise SystemExit("KiCad 10 kicad-cli not found")
        report = output_path.with_name(f".{output_path.stem}.panelize-drc.json")
        completed = subprocess.run(
            [cli, "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
             "--output", str(report), str(output_path)],
            text=True, capture_output=True,
        )
        drc = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
        report.unlink(missing_ok=True)
        if completed.returncode:
            print(completed.stdout, end="")
            print(completed.stderr, end="")
            output_path.unlink(missing_ok=True)
            raise SystemExit("KiCad rejected the routed panel")
        unexpected = [
            violation for violation in drc.get("violations", [])
            if violation.get("type") != "invalid_outline"
        ]
        unconnected = drc.get("unconnected_items", [])
        if unexpected or unconnected:
            print(completed.stdout, end="")
            print(completed.stderr, end="")
            output_path.unlink(missing_ok=True)
            raise SystemExit(
                "routed panel failed DRC: "
                f"{len(unexpected)} non-tab violation(s), "
                f"{len(unconnected)} unconnected item(s)"
            )
        tab_markers = sum(
            violation.get("type") == "invalid_outline"
            for violation in drc.get("violations", [])
        )
        if tab_markers:
            print(
                f"Validated {tab_markers} intentional routed tab opening(s); "
                "no non-tab DRC violations or unconnected items."
            )
    if source_path.read_bytes() != source_bytes:
        raise RuntimeError("source PCB changed unexpectedly")
    print(f"Created routed {args.count_x} x {args.count_y} panel: {output_path}")
    print(f"Panel size: {panel_bounds.width:.3f} x {panel_bounds.height:.3f} mm; routing gap: {args.gap:.3f} mm")
    print("Select Castellated Holes and customer-supplied panelization when ordering from JLCPCB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
