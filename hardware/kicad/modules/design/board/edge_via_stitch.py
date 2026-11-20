"""Place clearance-aware ground stitching vias around the PCB perimeter.

The script modifies the board currently open in PCB Editor.  Candidate via
centres follow the outer Edge.Cuts contour at a configurable inward offset.
Candidates are omitted when their copper-and-clearance envelope intersects a
footprint, pad, track, existing via, non-GND zone, keepout/rule area, or other
board graphic.  All accepted vias are created in one undoable transaction and
the live board is left unsaved for review.
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from kipy.board_types import Via
from kipy.proto.board.board_types_pb2 import ViaType

# Ruff: noqa: E402
# Support direct path execution from any working directory.
if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    modules_directory = next(
        parent
        for parent in Path(__file__).resolve().parents
        if parent.name == "modules"
    )
    sys.path.insert(0, str(modules_directory.parent))

from modules.shared.kicad_geometry import edge_contours
from modules.shared.kicad_ipc import (
    BoardLayer,
    box_edges,
    connect_board,
    editor_commit,
    footprint_reference,
    from_mm,
    vector,
)


@dataclass(frozen=True)
class ModuleOptions:
    """User-configurable via geometry and placement clearances, in mm."""

    edge_offset: float = 0.60
    spacing: float = 2.50
    clearance: float = 0.25
    via_diameter: float = 0.60
    drill_diameter: float = 0.30
    net_name: str = "GND"


def validate_options(options: ModuleOptions) -> None:
    """Reject settings that cannot describe manufacturable placements."""
    if options.edge_offset <= 0:
        raise ValueError("edge offset must be greater than zero")
    if options.spacing <= 0:
        raise ValueError("spacing must be greater than zero")
    if options.clearance < 0:
        raise ValueError("clearance cannot be negative")
    if options.via_diameter <= 0 or options.drill_diameter <= 0:
        raise ValueError("via and drill diameters must be greater than zero")
    if options.drill_diameter >= options.via_diameter:
        raise ValueError("drill diameter must be smaller than via diameter")
    if options.edge_offset < options.via_diameter / 2:
        raise ValueError(
            "edge offset must be at least half the via diameter so copper "
            "does not cross Edge.Cuts"
        )
    if not options.net_name.strip():
        raise ValueError("net name cannot be empty")


def signed_area(contour) -> float:
    """Return a contour's signed doubled area in board coordinates."""
    return sum(
        first.x * second.y - second.x * first.y for first, second in pairwise(contour)
    )


def point_in_polygon(x: float, y: float, polygon) -> bool:
    """Return whether a point lies inside a closed polygon."""
    inside = False
    for first, second in pairwise(polygon):
        if (first.y > y) == (second.y > y):
            continue
        crossing_x = first.x + (y - first.y) * (second.x - first.x) / (
            second.y - first.y
        )
        if x < crossing_x:
            inside = not inside
    return inside


def point_on_board(x: float, y: float, outer, holes) -> bool:
    """Test the finished-board area represented by outer contour and cutouts."""
    return point_in_polygon(x, y, outer) and not any(
        point_in_polygon(x, y, hole) for hole in holes
    )


def contour_lengths(contour):
    """Return non-zero segments with their lengths and total perimeter."""
    segments = []
    total = 0.0
    for first, second in pairwise(contour):
        length = math.hypot(second.x - first.x, second.y - first.y)
        if length:
            segments.append((first, second, length))
            total += length
    return segments, total


def candidate_points(outer, holes, edge_offset_nm: int, spacing_nm: int):
    """Yield evenly distributed points offset inward from the outer contour."""
    segments, perimeter = contour_lengths(outer)
    count = max(1, math.floor(perimeter / spacing_nm))
    pitch = perimeter / count
    targets = [(index + 0.5) * pitch for index in range(count)]
    segment_start = 0.0
    target_index = 0
    for first, second, length in segments:
        while (
            target_index < len(targets)
            and targets[target_index] <= segment_start + length
        ):
            along = targets[target_index] - segment_start
            fraction = along / length
            edge_x = first.x + (second.x - first.x) * fraction
            edge_y = first.y + (second.y - first.y) * fraction
            normal_x = -(second.y - first.y) / length
            normal_y = (second.x - first.x) / length
            alternatives = [
                (
                    edge_x + normal_x * edge_offset_nm,
                    edge_y + normal_y * edge_offset_nm,
                ),
                (
                    edge_x - normal_x * edge_offset_nm,
                    edge_y - normal_y * edge_offset_nm,
                ),
            ]
            valid = [
                point for point in alternatives if point_on_board(*point, outer, holes)
            ]
            if valid:
                # Exactly one side is normally inside. At very tight concave
                # geometry both may be inside; either remains the requested
                # distance from the sampled edge, so keep the first.
                yield vector(round(valid[0][0]), round(valid[0][1]))
            target_index += 1
        segment_start += length


def item_box_near(board, item, point, radius_nm: int, *, include_text=None) -> bool:
    """Cheaply reject items whose bounding boxes cannot touch the envelope."""
    kwargs = {} if include_text is None else {"include_text": include_text}
    box = board.get_item_bounding_box(item, **kwargs)
    if box is None:
        return True
    left, right, top, bottom = box_edges(box)
    return not (
        point.x + radius_nm < left
        or point.x - radius_nm > right
        or point.y + radius_nm < top
        or point.y - radius_nm > bottom
    )


def hits_item(board, item, point, radius_nm: int) -> bool:
    """Test actual item geometry after a bounding-box proximity filter."""
    if not item_box_near(board, item, point, radius_nm):
        return False
    try:
        return board.hit_test(item, point, tolerance=radius_nm)
    except (AttributeError, TypeError):
        # Some IPC item types have a bounding box but no hit-test operation.
        # Treat proximity as a conflict; a false skip is safer than a DRC error.
        return True


def collision_reason(board, point, radius_nm: int, obstacles) -> str | None:
    """Return a readable reason when a candidate conflicts with board content."""
    for footprint in obstacles["footprints"]:
        # Physical footprint bounds include pads, body/fabrication graphics,
        # and courtyard geometry but deliberately exclude movable text.
        if item_box_near(board, footprint, point, radius_nm, include_text=False):
            return f"footprint {footprint_reference(footprint)}"
    for kind in ("vias", "tracks", "zones", "shapes"):
        for label, item in obstacles[kind]:
            if hits_item(board, item, point, radius_nm):
                return label
    return None


def collect_obstacles(board, net_name: str):
    """Collect all geometry capable of conflicting with a through-via."""
    zones = []
    for index, zone in enumerate(board.get_zones(), start=1):
        zone_net = zone.net.name if getattr(zone, "net", None) is not None else ""
        if not zone.is_rule_area() and zone_net == net_name:
            continue
        kind = (
            "keepout/rule area"
            if zone.is_rule_area()
            else f"zone on {zone_net or 'no net'}"
        )
        zones.append((f"{kind} {index}", zone))
    return {
        "footprints": list(board.get_footprints()),
        "vias": [
            (f"existing via {i}", item) for i, item in enumerate(board.get_vias(), 1)
        ],
        "tracks": [
            (f"track {i}", item) for i, item in enumerate(board.get_tracks(), 1)
        ],
        "zones": zones,
        "shapes": [
            (f"board graphic {i}", item)
            for i, item in enumerate(board.get_shapes(), 1)
            if item.layer != BoardLayer.BL_Edge_Cuts
        ],
    }


def run(options: ModuleOptions) -> int:
    """Create safe perimeter vias on the open board and return zero."""
    validate_options(options)
    _client, board = connect_board()
    nets = {net.name: net for net in board.get_nets()}
    if options.net_name not in nets:
        raise RuntimeError(f'board has no net named "{options.net_name}"')

    edge_items = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")
    contours = edge_contours(edge_items)
    if not contours:
        raise RuntimeError("board has no closed Edge.Cuts contour")
    outer = max(contours, key=lambda contour: abs(signed_area(contour)))
    holes = [contour for contour in contours if contour is not outer]

    envelope_radius_nm = from_mm(options.via_diameter / 2 + options.clearance)
    obstacles = collect_obstacles(board, options.net_name)
    accepted = []
    skipped = Counter()
    for point in candidate_points(
        outer,
        holes,
        from_mm(options.edge_offset),
        from_mm(options.spacing),
    ):
        reason = collision_reason(board, point, envelope_radius_nm, obstacles)
        if reason is not None:
            skipped[reason.split(" ", 1)[0]] += 1
            continue
        # Protect spacing against rounding and against an unusually small
        # requested pitch relative to the via clearance envelope.
        if any(
            math.hypot(point.x - prior.x, point.y - prior.y) < 2 * envelope_radius_nm
            for prior in accepted
        ):
            skipped["new-via"] += 1
            continue
        accepted.append(point)

    if not accepted:
        details = ", ".join(
            f"{count} {kind}" for kind, count in sorted(skipped.items())
        )
        print(
            f"No safe {options.net_name} via positions found"
            + (f" ({details})." if details else ".")
        )
        return 0

    created = []
    for point in accepted:
        via = Via()
        via.type = ViaType.VT_THROUGH
        via.net = nets[options.net_name]
        via.position = point
        via.diameter = from_mm(options.via_diameter)
        via.drill_diameter = from_mm(options.drill_diameter)
        created.append(via)

    action = f"Stitch {options.net_name} vias around board edge"
    with editor_commit(board, action, refill_zones=True):
        board.create_items(created)

    skipped_total = sum(skipped.values())
    print(
        f"Created {len(created)} {options.net_name} edge-stitching via(s); "
        f"skipped {skipped_total} conflicting candidate(s) "
        f"(undo: {action})."
    )
    if skipped:
        print(
            "Skipped by obstacle type: "
            + ", ".join(f"{kind}={count}" for kind, count in sorted(skipped.items()))
        )
    print("Live board changes are left unsaved for review in KiCad.")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse command-line settings exposed by the KiCad tools application."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--edge-offset",
        type=float,
        default=0.60,
        help="via-centre distance inward from Edge.Cuts, in mm",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=2.50,
        help="target distance between vias along the perimeter, in mm",
    )
    parser.add_argument(
        "--clearance",
        type=float,
        default=0.25,
        help="minimum edge-to-edge clearance from other items, in mm",
    )
    parser.add_argument(
        "--via-diameter",
        type=float,
        default=0.60,
        help="finished via copper diameter, in mm",
    )
    parser.add_argument(
        "--drill-diameter", type=float, default=0.30, help="via drill diameter, in mm"
    )
    parser.add_argument(
        "--net-name", default="GND", help="net assigned to the stitching vias"
    )
    values = parser.parse_args(argv)
    return ModuleOptions(
        edge_offset=values.edge_offset,
        spacing=values.spacing,
        clearance=values.clearance,
        via_diameter=values.via_diameter,
        drill_diameter=values.drill_diameter,
        net_name=values.net_name,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse settings and place edge-stitching vias."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
