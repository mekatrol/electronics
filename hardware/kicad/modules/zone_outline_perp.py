#!/usr/bin/env python3
"""Orthogonalize copper-zone outlines through KiCad's IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/zone_outline_perp.py``.
Each run is one PCB Editor undo/redo transaction.  The first outer contour is
rebuilt and existing zone holes/cutouts are deliberately not preserved.
"""

from kipy.geometry import PolyLine, PolyLineNode, PolygonWithHoles

from kicad_ipc import (
    connect_board, editor_commit, is_horizontal, is_vertical, same_point,
    to_mm, vector,
)


ZONE_NAME = ""  # Exact name; empty processes every zone.
PREFER_HORIZONTAL_FIRST = True
DEBUG = True


def compress(points):
    """Remove adjacent duplicates and a repeated closing vertex."""
    result = []
    for point in points:
        if not result or not same_point(result[-1], point):
            result.append(vector(point.x, point.y))
    if len(result) > 1 and same_point(result[0], result[-1]):
        result.pop()
    return result


def merge_collinear(points):
    """Remove vertices lying between two collinear axis-aligned edges."""
    points = compress(points)
    changed = True
    while changed and len(points) >= 3:
        changed = False
        output = []
        for index, current in enumerate(points):
            previous = points[index - 1]
            following = points[(index + 1) % len(points)]
            if ((is_horizontal(previous, current) and is_horizontal(current, following)) or
                    (is_vertical(previous, current) and is_vertical(current, following))):
                changed = True
            else:
                output.append(current)
        points = compress(output)
    return points


def orthogonalize(points):
    """Replace every diagonal edge with two perpendicular segments."""
    points = compress(points)
    output = []
    for index, first in enumerate(points):
        second = points[(index + 1) % len(points)]
        if not output or not same_point(output[-1], first):
            output.append(first)
        if not is_horizontal(first, second) and not is_vertical(first, second):
            corner = (
                vector(second.x, first.y)
                if PREFER_HORIZONTAL_FIRST
                else vector(first.x, second.y)
            )
            if not same_point(corner, first) and not same_point(corner, second):
                output.append(corner)
    return merge_collinear(output)


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
    _client, board = connect_board()
    zones = [zone for zone in board.get_zones() if not ZONE_NAME or zone.name == ZONE_NAME]
    if not zones:
        raise RuntimeError(f'no zones found with name "{ZONE_NAME}"')

    with editor_commit(
        board,
        "Orthogonalize zone outlines",
        refill_zones=True,
    ):
        for index, zone in enumerate(zones, start=1):
            nodes = zone.outline.outline.nodes
            if any(not node.has_point for node in nodes):
                raise RuntimeError(f"zone {index} contains arc nodes; cannot orthogonalize safely")
            original = [node.point for node in nodes]
            final = orthogonalize(original)
            if len(final) < 3:
                raise RuntimeError(f"zone {index} would have fewer than three vertices")
            zone.outline = polygon_from_points(final)
            if DEBUG:
                print(f'Zone {index} "{zone.name}": {len(original)} -> {len(final)} vertices')
                for point in final:
                    print(f"  ({to_mm(point.x):.3f}, {to_mm(point.y):.3f}) mm")
        board.update_items(zones)

    print(f"Updated {len(zones)} zone(s) (undo: Orthogonalize zone outlines).")


if __name__ == "__main__":
    main()
