"""Snap zone-outline edges to 45-degree or axis-aligned paths via KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/zone_outline_45_90.py

Each run is one PCB Editor undo/redo transaction.  The first outer contour is
rebuilt and existing zone holes/cutouts are deliberately not preserved.
"""

import math

from kicad_ipc import (
    connect_board,
    editor_commit,
    same_point,
    to_mm,
    vector,
)
from kipy.geometry import PolygonWithHoles, PolyLine, PolyLineNode
from kipy.proto.board.board_types_pb2 import ZoneType

# Updating a broad list of zones through KiCad IPC can rewrite unrelated zone
# metadata (for example, a copper zone's net assignment). Always name one zone
# explicitly so only the intended object is sent back to PCB Editor.
ZONE_NAME = "24VAC PWR"
# Edges in this inclusive range are kept as diagonal paths, but made exactly
# 45 degrees. Shallower and steeper edges are replaced by perpendicular paths.
MIN_DIAGONAL_ANGLE_DEGREES = 25.0
MAX_DIAGONAL_ANGLE_DEGREES = 65.0
DEBUG = True


def is_supported_zone(zone):
    """Return whether a zone is copper or a keep-out/rule area."""
    return zone.type in (ZoneType.ZT_COPPER, ZoneType.ZT_RULE_AREA)


def zone_kind(zone):
    """Return a human-readable zone kind for diagnostics."""
    return "keep-out" if zone.type == ZoneType.ZT_RULE_AREA else "copper zone"


def compress(points):
    """Remove adjacent duplicates and a repeated closing vertex."""
    result = []
    for point in points:
        if not result or not same_point(result[-1], point):
            result.append(vector(point.x, point.y))
    if len(result) > 1 and same_point(result[0], result[-1]):
        result.pop()
    return result


def angle_from_horizontal(first, second):
    """Return an edge's unsigned angle from horizontal in the 0..90 range."""
    delta_x = abs(second.x - first.x)
    delta_y = abs(second.y - first.y)
    return math.degrees(math.atan2(delta_y, delta_x))


def snapped_direction(first, second):
    """Classify an existing edge without creating or removing any segments.

    The returned value is ``horizontal``, ``vertical``, ``diagonal_up`` (equal
    X/Y changes), or ``diagonal_down`` (equal and opposite X/Y changes).
    """
    angle = angle_from_horizontal(first, second)
    if angle < MIN_DIAGONAL_ANGLE_DEGREES:
        return "horizontal"
    if angle > MAX_DIAGONAL_ANGLE_DEGREES:
        return "vertical"
    same_sign = (second.x - first.x) * (second.y - first.y) >= 0
    return "diagonal_up" if same_sign else "diagonal_down"


def project_edge(first, second, direction):
    """Move both endpoints minimally toward one requested edge direction.

    Moving each endpoint by half the error preserves the edge midpoint. Repeated
    projection around the closed outline lets every shared corner settle at a
    position satisfying both of its neighbouring edges.
    """
    if direction == "horizontal":
        error = second[1] - first[1]
        first[1] += error / 2
        second[1] -= error / 2
    elif direction == "vertical":
        error = second[0] - first[0]
        first[0] += error / 2
        second[0] -= error / 2
    else:
        slope = 1 if direction == "diagonal_up" else -1
        error = (second[1] - first[1]) - slope * (second[0] - first[0])
        first[0] -= slope * error / 4
        first[1] += error / 4
        second[0] += slope * error / 4
        second[1] -= error / 4
    return abs(error)


def snap_outline(points):
    """Snap a closed outline by moving corners, never by adding segments.

    Each original edge is classified once from its original angle. Iterative
    orthogonal projection then finds nearby corner positions that satisfy all
    edge directions together, including the closing edge of the polygon. The
    input and output always contain exactly the same number of vertices.
    """
    points = compress(points)
    if len(points) < 3:
        raise RuntimeError("zone outline has fewer than three unique vertices")

    directions = [
        snapped_direction(point, points[(index + 1) % len(points)])
        for index, point in enumerate(points)
    ]
    adjusted = [[float(point.x), float(point.y)] for point in points]

    # Alternating projections converge quickly for these linear constraints.
    # The generous limit protects unusual outlines without affecting normal ones.
    for _iteration in range(10_000):
        largest_error = 0.0
        for index, direction in enumerate(directions):
            error = project_edge(
                adjusted[index], adjusted[(index + 1) % len(adjusted)], direction
            )
            largest_error = max(largest_error, error)
        if largest_error < 0.1:  # one tenth of an IPC nanometre
            break
    else:
        raise RuntimeError("outline corner adjustment did not converge")

    output = [vector(round(x), round(y)) for x, y in adjusted]
    if any(
        same_point(point, output[(index + 1) % len(output)])
        for index, point in enumerate(output)
    ):
        raise RuntimeError("corner adjustment collapsed an outline segment")
    return output


def polygon_from_points(points):
    """Build the closed IPC polygon required by a zone outline."""
    line = PolyLine()
    for point in points:
        line.append(PolyLineNode.from_point(point))
    line.closed = True
    polygon = PolygonWithHoles()
    polygon.outline = line
    return polygon


def main():
    """Update matching zones, refill them, and push one editor transaction."""
    if not ZONE_NAME:
        raise RuntimeError(
            "ZONE_NAME must contain the exact name of one zone; bulk zone "
            "updates are disabled because they can damage unrelated metadata"
        )

    _client, board = connect_board()
    zones = [
        zone
        for zone in board.get_zones()
        if is_supported_zone(zone) and zone.name == ZONE_NAME
    ]
    if not zones:
        raise RuntimeError(f'no copper or keep-out zones found with name "{ZONE_NAME}"')
    if len(zones) > 1:
        raise RuntimeError(
            f'found {len(zones)} zones named "{ZONE_NAME}"; zone names must be '
            "unique so unrelated zones are not modified"
        )

    with editor_commit(
        board,
        "Snap zone outlines to 45/90 degrees",
        refill_zones=True,
    ):
        for index, zone in enumerate(zones, start=1):
            nodes = zone.outline.outline.nodes
            if any(not node.has_point for node in nodes):
                raise RuntimeError(
                    f"{zone_kind(zone)} {index} contains arc nodes; "
                    "cannot snap outline safely"
                )
            original = compress([node.point for node in nodes])
            final = snap_outline(original)
            if len(final) < 3:
                raise RuntimeError(
                    f"{zone_kind(zone)} {index} would have fewer than three vertices"
                )
            if len(final) != len(original):
                raise RuntimeError(
                    f"{zone_kind(zone)} {index} changed vertex count "
                    f"from {len(original)} to {len(final)}"
                )
            zone.outline = polygon_from_points(final)
            if DEBUG:
                print(
                    f'{zone_kind(zone).title()} {index} "{zone.name}": '
                    f"{len(original)} -> {len(final)} vertices"
                )
                for point in final:
                    print(f"  ({to_mm(point.x):.3f}, {to_mm(point.y):.3f}) mm")
        board.update_items(zones)

    print(
        f"Updated {len(zones)} copper/keep-out zone(s) "
        "(undo: Snap zone outlines to 45/90 degrees)."
    )


if __name__ == "__main__":
    main()
