#!/usr/bin/env python3
"""Create a rectangular board outline and optional GND zones through IPC.

Execution:
    1. Enable KiCad's API server and open the target board in PCB Editor.
    2. Review every setting below, especially both replacement switches.
    3. From the repository root, run::

        .venv-kicad-ipc/bin/python hardware/kicad/modules/pcb_edge.py

The script changes the live board held by PCB Editor; it does not edit a board
file directly or save automatically. Deletion and creation are grouped into
one ``Replace board outline and ground zones`` entry in PCB Editor's Undo/Redo
history. The blocking zone refill runs immediately after that staged commit is
published, because KiCad cannot fill against geometry that is still staged.
If an edit fails, the IPC transaction is dropped so a partial outline is not
retained.
"""

import math

from kipy.board_types import BoardArc, BoardSegment, Zone
from kipy.geometry import PolyLine, PolyLineNode, PolygonWithHoles

from kicad_ipc import (
    BoardLayer,
    connect_board,
    editor_commit,
    from_mm,
    point_from_mm,
)


# ============================================================
# User settings: board geometry
# ============================================================
# Fabrication dimensions are measured along the Edge.Cuts centreline. The
# origin is the top-left point of the finished outline in board coordinates;
# KiCad X increases rightwards and Y increases downwards.
BOARD_WIDTH_MM = 50.0
BOARD_HEIGHT_MM = 70.0
ORIGIN_X_MM = 120.0
ORIGIN_Y_MM = 50.0

# Use 0 for square corners. A positive value creates four tangent quarter-circle
# arcs and must not exceed half of the board's smaller dimension.
CORNER_RADIUS_MM = 2.0

# This affects the visible Edge.Cuts stroke, not the finished board dimensions.
EDGE_LINE_WIDTH_MM = 0.10


# ============================================================
# User settings: destructive replacement behavior
# ============================================================
# True removes every existing Edge.Cuts graphic before adding the new outline.
# False preserves the existing graphics and adds another outline alongside
# them; use False only when that duplication is intentional.
DELETE_EXISTING_EDGE_CUTS = True

# True removes existing front/back zones assigned to GROUND_NET_NAME and creates
# one rectangular zone on each outer copper layer. All board zones are refilled
# after the outline is rebuilt, regardless of this setting.
# The zone polygon remains square even when Edge.Cuts has rounded corners;
# KiCad clips its copper fill to the actual board boundary.
REPLACE_GROUND_ZONES = True
GROUND_NET_NAME = "GND"


def validate_settings():
    """Reject dimensions that cannot form a valid rectangular outline."""
    if BOARD_WIDTH_MM <= 0 or BOARD_HEIGHT_MM <= 0:
        raise ValueError("board width and height must be positive")
    if EDGE_LINE_WIDTH_MM <= 0:
        raise ValueError("Edge.Cuts line width must be positive")
    if CORNER_RADIUS_MM < 0:
        raise ValueError("corner radius cannot be negative")

    maximum_radius = min(BOARD_WIDTH_MM, BOARD_HEIGHT_MM) / 2.0
    if CORNER_RADIUS_MM > maximum_radius:
        raise ValueError(
            f"corner radius cannot exceed {maximum_radius:.3f} mm for a "
            f"{BOARD_WIDTH_MM:.3f} x {BOARD_HEIGHT_MM:.3f} mm board"
        )


def create_edge_segment(start, end):
    """Construct one straight Edge.Cuts graphic in IPC nanometre units."""
    item = BoardSegment()
    item.layer = BoardLayer.BL_Edge_Cuts
    item.start = start
    item.end = end
    item.attributes.stroke.width = from_mm(EDGE_LINE_WIDTH_MM)
    return item


def create_edge_arc(start, mid, end):
    """Construct an Edge.Cuts arc from three points lying on its curve.

    KiCad's IPC representation stores start, midpoint, and end rather than a
    centre/radius pair. The caller supplies a point at 45 degrees around the
    quarter circle so KiCad resolves the intended 90-degree arc.
    """
    item = BoardArc()
    item.layer = BoardLayer.BL_Edge_Cuts
    item.start = start
    item.mid = mid
    item.end = end
    item.attributes.stroke.width = from_mm(EDGE_LINE_WIDTH_MM)
    return item


def create_outline_items():
    """Build four lines, or four lines and four tangent corner arcs."""
    validate_settings()
    width, height, radius = BOARD_WIDTH_MM, BOARD_HEIGHT_MM, CORNER_RADIUS_MM
    x0, y0 = ORIGIN_X_MM, ORIGIN_Y_MM
    x1, y1 = x0 + width, y0 + height

    if radius == 0:
        corners = [
            point_from_mm(x0, y0),
            point_from_mm(x1, y0),
            point_from_mm(x1, y1),
            point_from_mm(x0, y1),
        ]
        return [
            create_edge_segment(corners[index], corners[(index + 1) % 4])
            for index in range(4)
        ]

    # Each straight edge stops one radius before its nominal rectangle corner.
    top_start = point_from_mm(x0 + radius, y0)
    top_end = point_from_mm(x1 - radius, y0)
    right_start = point_from_mm(x1, y0 + radius)
    right_end = point_from_mm(x1, y1 - radius)
    bottom_start = point_from_mm(x1 - radius, y1)
    bottom_end = point_from_mm(x0 + radius, y1)
    left_start = point_from_mm(x0, y1 - radius)
    left_end = point_from_mm(x0, y0 + radius)

    # A point on a circle at 45 degrees is radius / sqrt(2) from its centre on
    # both axes. These intermediate points disambiguate the four quarter arcs.
    diagonal = radius / math.sqrt(2)
    return [
        create_edge_segment(top_start, top_end),
        create_edge_arc(
            top_end,
            point_from_mm(x1 - radius + diagonal, y0 + radius - diagonal),
            right_start,
        ),
        create_edge_segment(right_start, right_end),
        create_edge_arc(
            right_end,
            point_from_mm(x1 - radius + diagonal, y1 - radius + diagonal),
            bottom_start,
        ),
        create_edge_segment(bottom_start, bottom_end),
        create_edge_arc(
            bottom_end,
            point_from_mm(x0 + radius - diagonal, y1 - radius + diagonal),
            left_start,
        ),
        create_edge_segment(left_start, left_end),
        create_edge_arc(
            left_end,
            point_from_mm(x0 + radius - diagonal, y0 + radius - diagonal),
            top_start,
        ),
    ]


def rectangular_polygon():
    """Build a closed, square-corner polygon matching the board rectangle.

    Zone fills are clipped to Edge.Cuts by KiCad, so keeping this source
    polygon rectangular is intentional even when the board corners are round.
    """
    line = PolyLine()
    for x, y in [
        (ORIGIN_X_MM, ORIGIN_Y_MM),
        (ORIGIN_X_MM + BOARD_WIDTH_MM, ORIGIN_Y_MM),
        (ORIGIN_X_MM + BOARD_WIDTH_MM, ORIGIN_Y_MM + BOARD_HEIGHT_MM),
        (ORIGIN_X_MM, ORIGIN_Y_MM + BOARD_HEIGHT_MM),
    ]:
        line.append(PolyLineNode.from_point(point_from_mm(x, y)))
    line.closed = True
    polygon = PolygonWithHoles()
    polygon.outline = line
    return polygon


def ground_zones(board):
    """Construct one rectangular GND zone for each outer copper layer."""
    net = next((net for net in board.get_nets() if net.name == GROUND_NET_NAME), None)
    if net is None:
        raise RuntimeError(f'net "{GROUND_NET_NAME}" was not found')
    zones = []
    for layer in (BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu):
        zone = Zone()
        zone.name = GROUND_NET_NAME
        zone.net = net
        zone.layers = [layer]
        zone.outline = rectangular_polygon()
        zones.append(zone)
    return zones


def main():
    """Replace configured items in one atomic PCB Editor transaction."""
    _client, board = connect_board()

    # Construct and validate all replacement objects before starting the editor
    # transaction. Configuration failures therefore cannot remove live items.
    new_outline = create_outline_items()
    existing_edges = [
        shape for shape in board.get_shapes()
        if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    existing_ground_zones = [
        zone for zone in board.get_zones()
        if zone.net is not None and zone.net.name == GROUND_NET_NAME
        and any(
            layer in (BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu)
            for layer in zone.layers
        )
    ]
    new_zones = ground_zones(board) if REPLACE_GROUND_ZONES else []

    # The shared context manager calls begin_commit/push_commit, producing one
    # named Undo/Redo entry. It calls drop_commit if any IPC request raises.
    with editor_commit(
        board,
        "Replace board outline and ground zones",
        refill_zones=True,
    ):
        if DELETE_EXISTING_EDGE_CUTS and existing_edges:
            board.remove_items(existing_edges)
        if REPLACE_GROUND_ZONES and existing_ground_zones:
            board.remove_items(existing_ground_zones)

        board.create_items(new_outline)

        if new_zones:
            board.create_items(new_zones)

    print(
        f"Created {BOARD_WIDTH_MM:.3f} x {BOARD_HEIGHT_MM:.3f} mm outline with "
        f"{CORNER_RADIUS_MM:.3f} mm corners (undo: Replace board outline and ground zones)."
    )


if __name__ == "__main__":
    main()
