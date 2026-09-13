#!/usr/bin/env python3
"""Centre Edge.Cuts around all footprints using KiCad's IPC API.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/center_edge_around_components.py

The routed design stays fixed. Edge.Cuts moves around it, so tracks, vias, and
pads cannot be separated. Zones spanning the whole board move with the outline;
localized zones remain fixed. Save manually after review.
"""

from kicad_ipc import (
    BoardLayer,
    box_center,
    box_edges,
    connect_board,
    editor_commit,
    footprint_reference,
    from_mm,
    merge_boxes,
    to_mm,
)
from kicad_utils import centering_delta, edge_cuts_centroid


# User settings: include reference/value text in the component bounds if desired.
INCLUDE_TEXT = False
BOARD_ZONE_EDGE_TOLERANCE_MM = 0.2


def spans_board(zone, edges):
    """Return whether a zone outline follows the current board bounds."""
    zone_edges = box_edges(zone.bounding_box())
    tolerance = from_mm(BOARD_ZONE_EDGE_TOLERANCE_MM)
    return all(
        abs(zone_edge - board_edge) <= tolerance
        for zone_edge, board_edge in zip(zone_edges, edges)
    )


def main():
    """Translate the board outline around fixed footprints and routing."""
    _client, board = connect_board()
    footprints = list(board.get_footprints())
    if not footprints:
        print("No footprints to center.")
        return

    edge_items = [
        shape
        for shape in board.get_shapes()
        if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")

    boxes = []
    for footprint in footprints:
        box = board.get_item_bounding_box(footprint, include_text=INCLUDE_TEXT)
        if box is None:
            raise RuntimeError(
                f"KiCad returned no bounding box for {footprint_reference(footprint)}"
            )
        boxes.append(box)

    footprint_center = box_center(merge_boxes(boxes))
    edge_center = edge_cuts_centroid(edge_items)
    delta = centering_delta(edge_center, footprint_center)
    delta_x, delta_y = delta.x, delta.y
    if delta_x == 0 and delta_y == 0:
        print("Edge.Cuts is already centered around the components.")
        return

    edge_bounds = box_edges(merge_boxes(shape.bounding_box() for shape in edge_items))
    board_zones = [
        zone for zone in board.get_zones() if spans_board(zone, edge_bounds)
    ]
    action = "Center board outline around components"
    with editor_commit(board, action, refill_zones=True):
        for edge in edge_items:
            edge.move(delta)
        for zone in board_zones:
            zone.move(delta)
        board.update_items([*edge_items, *board_zones])

    print(
        f"Centered Edge.Cuts around {len(footprints)} footprint(s): "
        f"moved outline X by {to_mm(delta_x):.6f} mm and "
        f"Y by {to_mm(delta_y):.6f} mm; moved {len(board_zones)} "
        f"board-spanning zone(s) with it (undo: {action})."
    )


if __name__ == "__main__":
    main()
