#!/usr/bin/env python3
"""Create a rectangular board outline and optional copper zones through IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/pcb_edge.py

Review every setting below, especially both replacement switches, before
running the script.

The script changes the live board held by PCB Editor; it does not edit a board
file directly or save automatically. Deletion and creation are grouped into
one ``Replace board outline and fill zones`` entry in PCB Editor's Undo/Redo
history. The blocking zone refill runs immediately after that staged commit is
published, because KiCad cannot fill against geometry that is still staged.
If an edit fails, the IPC transaction is dropped so a partial outline is not
retained.
"""

import math
import re

from kicad_ipc import (
    BoardLayer,
    connect_board,
    editor_commit,
    from_mm,
    point_from_mm,
    to_mm,
)
from kicad_utils import edge_cuts_centroid
from kipy.board_types import BoardArc, BoardSegment, Zone
from kipy.geometry import PolygonWithHoles, PolyLine, PolyLineNode

# ============================================================
# User settings: board geometry
# ============================================================
# Fabrication dimensions are measured along the Edge.Cuts centreline. The
# origin is the top-left point of the finished outline in board coordinates;
# KiCad X increases rightwards and Y increases downwards.
BOARD_WIDTH_MM = 25.0
BOARD_HEIGHT_MM = 45.0
ORIGIN_X_MM = 136.0
ORIGIN_Y_MM = 80.0

# Preserve the area centroid of the current connected Edge.Cuts contour when
# replacing it. If no outline exists, the configured origin above is used.
KEEP_CENTRE = False

# Centre the new PCB on the drawing page. This takes precedence over
# KEEP_CENTRE and the configured origin. The page size and orientation are
# read from the live board (including custom User page sizes).
CENTRE_ON_PAGE = False

# Use 0 for square corners. A positive value creates four tangent quarter-circle
# arcs and must not exceed half of the board's smaller dimension.
CORNER_RADIUS_MM = 1.0

# This affects the visible Edge.Cuts stroke, not the finished board dimensions.
EDGE_LINE_WIDTH_MM = 0.10


# ============================================================
# User settings: destructive replacement behavior
# ============================================================
# True removes every existing Edge.Cuts graphic before adding the new outline.
# False preserves the existing graphics and adds another outline alongside
# them; use False only when that duplication is intentional.
DELETE_EXISTING_EDGE_CUTS = True

# True removes existing zones using the configured nets on enabled copper
# layers and creates one rectangular zone on every copper layer in the stack.
# Names are ordered from F.Cu through the inner layers to B.Cu. Missing entries
# default to GND; entries beyond the board's layer count are ignored. Each name
# must be a net present on the board and is used for both the zone and its net.
# All board zones are refilled after the outline is rebuilt, regardless of this
# setting.
# The zone polygon remains square even when Edge.Cuts has rounded corners;
# KiCad clips its copper fill to the actual board boundary.
REPLACE_GROUND_ZONES = True
GROUND_NET_NAME = "GND"
FILL_ZONE_NAMES = ["GND", "GND", "GND", "GND"]


PAPER_SIZES_MM = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
    "A5": (210.0, 148.0),
    "Letter": (279.4, 215.9),
    "Legal": (355.6, 215.9),
    "Ledger": (431.8, 279.4),
}


def page_centre_mm(board):
    """Return the centre of the board's drawing page in millimetres."""
    contents = board.get_as_string()
    match = re.search(
        r'\(paper\s+"(?P<name>[^"]+)"'
        r"(?:\s+(?P<width>[0-9.]+)\s+(?P<height>[0-9.]+))?"
        r"(?P<portrait>\s+portrait)?\s*\)",
        contents,
    )
    if match is None:
        raise RuntimeError("could not read the drawing page size from the board")

    name = match.group("name")
    if name == "User":
        if match.group("width") is None or match.group("height") is None:
            raise RuntimeError("the board's custom User page has no dimensions")
        width = float(match.group("width"))
        height = float(match.group("height"))
    else:
        try:
            width, height = PAPER_SIZES_MM[name]
        except KeyError as error:
            raise RuntimeError(f'unsupported drawing page size "{name}"') from error

    if match.group("portrait"):
        width, height = height, width
    return width / 2.0, height / 2.0


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


def create_outline_items(origin_x_mm=ORIGIN_X_MM, origin_y_mm=ORIGIN_Y_MM):
    """Build four lines, or four lines and four tangent corner arcs."""
    validate_settings()
    width, height, radius = BOARD_WIDTH_MM, BOARD_HEIGHT_MM, CORNER_RADIUS_MM
    x0, y0 = origin_x_mm, origin_y_mm
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


def rectangular_polygon(origin_x_mm=ORIGIN_X_MM, origin_y_mm=ORIGIN_Y_MM):
    """Build a closed, square-corner polygon matching the board rectangle.

    Zone fills are clipped to Edge.Cuts by KiCad, so keeping this source
    polygon rectangular is intentional even when the board corners are round.
    """
    line = PolyLine()
    for x, y in [
        (origin_x_mm, origin_y_mm),
        (origin_x_mm + BOARD_WIDTH_MM, origin_y_mm),
        (origin_x_mm + BOARD_WIDTH_MM, origin_y_mm + BOARD_HEIGHT_MM),
        (origin_x_mm, origin_y_mm + BOARD_HEIGHT_MM),
    ]:
        line.append(PolyLineNode.from_point(point_from_mm(x, y)))
    line.closed = True
    polygon = PolygonWithHoles()
    polygon.outline = line
    return polygon


def copper_layers(board):
    """Return enabled copper layers in physical top-to-bottom stack order."""
    contents = board.get_as_string()
    match = re.search(r"\(layers\s*\n(?P<body>.*?\n\s*\))", contents, re.DOTALL)
    if match is None:
        raise RuntimeError("could not read the copper layer stack from the board")

    layer_names = re.findall(
        r'^\s*\(\d+\s+"((?:F|B|In\d+)\.Cu)"\s+',
        match.group("body"),
        re.MULTILINE,
    )
    if not layer_names:
        raise RuntimeError("the board has no enabled copper layers")

    layers = []
    for name in layer_names:
        try:
            layers.append(getattr(BoardLayer, f"BL_{name.replace('.', '_')}"))
        except AttributeError as error:
            raise RuntimeError(f'unsupported copper layer "{name}"') from error
    return layers


def configured_zone_names(layer_count):
    """Return exactly one configured net/zone name for each copper layer."""
    return [
        FILL_ZONE_NAMES[index] if index < len(FILL_ZONE_NAMES) else GROUND_NET_NAME
        for index in range(layer_count)
    ]


def fill_zones(board, layers, origin_x_mm=ORIGIN_X_MM, origin_y_mm=ORIGIN_Y_MM):
    """Construct one configured rectangular fill zone per copper layer."""
    nets = {net.name: net for net in board.get_nets()}
    names = configured_zone_names(len(layers))
    missing = sorted({name for name in names if name not in nets})
    if missing:
        quoted = ", ".join(f'"{name}"' for name in missing)
        raise RuntimeError(f"board net(s) not found: {quoted}")

    zones = []
    for layer, name in zip(layers, names):
        zone = Zone()
        zone.name = name
        zone.net = nets[name]
        zone.layers = [layer]
        zone.outline = rectangular_polygon(origin_x_mm, origin_y_mm)
        zones.append(zone)
    return zones


def main():
    """Replace configured items in one atomic PCB Editor transaction."""
    _client, board = connect_board()

    existing_edges = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    origin_x_mm = ORIGIN_X_MM
    origin_y_mm = ORIGIN_Y_MM
    position_description = "using the configured origin"
    if CENTRE_ON_PAGE:
        centre_x_mm, centre_y_mm = page_centre_mm(board)
        origin_x_mm = centre_x_mm - BOARD_WIDTH_MM / 2
        origin_y_mm = centre_y_mm - BOARD_HEIGHT_MM / 2
        position_description = "centred on the drawing page"
    elif KEEP_CENTRE and existing_edges:
        centre = edge_cuts_centroid(existing_edges)
        centre_x_mm, centre_y_mm = to_mm(centre.x), to_mm(centre.y)
        origin_x_mm = centre_x_mm - BOARD_WIDTH_MM / 2
        origin_y_mm = centre_y_mm - BOARD_HEIGHT_MM / 2
        position_description = "while preserving the previous centroid"

    # Construct and validate all replacement objects before starting the editor
    # transaction. Configuration failures therefore cannot remove live items.
    new_outline = create_outline_items(origin_x_mm, origin_y_mm)
    layers = copper_layers(board) if REPLACE_GROUND_ZONES else []
    replacement_names = set(configured_zone_names(len(layers)))
    existing_fill_zones = [
        zone
        for zone in board.get_zones()
        if zone.net is not None
        and zone.net.name in replacement_names
        and any(layer in layers for layer in zone.layers)
    ]
    new_zones = (
        fill_zones(board, layers, origin_x_mm, origin_y_mm)
        if REPLACE_GROUND_ZONES
        else []
    )

    # The shared context manager calls begin_commit/push_commit, producing one
    # named Undo/Redo entry. It calls drop_commit if any IPC request raises.
    with editor_commit(
        board,
        "Replace board outline and fill zones",
        refill_zones=True,
    ):
        if DELETE_EXISTING_EDGE_CUTS and existing_edges:
            board.remove_items(existing_edges)
        if REPLACE_GROUND_ZONES and existing_fill_zones:
            board.remove_items(existing_fill_zones)

        board.create_items(new_outline)

        if new_zones:
            board.create_items(new_zones)

    print(
        f"Created {BOARD_WIDTH_MM:.3f} x {BOARD_HEIGHT_MM:.3f} mm outline with "
        f"{CORNER_RADIUS_MM:.3f} mm corners at "
        f"({origin_x_mm:.3f}, {origin_y_mm:.3f}) mm"
        f" {position_description} "
        f"(undo: Replace board outline and ground zones)."
    )


if __name__ == "__main__":
    main()
