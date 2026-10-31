#!/usr/bin/env python3
"""Centre one footprint between Edge.Cuts at its current cross-section.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/align_component_edge_center.py

For horizontal alignment, the footprint moves along X to the midpoint of the
two board-edge crossings at its current Y centre.  Vertical alignment uses the
two crossings at its current X centre and moves along Y.  The move is grouped
into one PCB Editor undo/redo transaction.  Save manually after review.
"""

from kicad_ipc import (
    BoardLayer,
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    to_mm,
    vector,
)
from kicad_utils import edge_contours

# User settings
COMPONENT_REFERENCE = "J1"
ALIGNMENT = "horizontal"  # "horizontal" moves along X; "vertical" moves along Y.
INCLUDE_TEXT = False


def scanline_crossings(contours, fixed_coordinate, alignment):
    """Return outline crossings on a horizontal or vertical scanline.

    A half-open endpoint rule counts a contour vertex only once.  Segments
    lying along the scanline do not represent a discrete board-edge crossing
    and are ignored.
    """
    crossings = []
    horizontal = alignment == "horizontal"
    for contour in contours:
        for first, second in zip(contour, contour[1:]):
            first_fixed = first.y if horizontal else first.x
            second_fixed = second.y if horizontal else second.x
            if first_fixed == second_fixed:
                continue
            if not (
                first_fixed <= fixed_coordinate < second_fixed
                or second_fixed <= fixed_coordinate < first_fixed
            ):
                continue
            first_moving = first.x if horizontal else first.y
            second_moving = second.x if horizontal else second.y
            fraction = (fixed_coordinate - first_fixed) / (second_fixed - first_fixed)
            crossings.append(
                round(first_moving + fraction * (second_moving - first_moving))
            )
    return sorted(set(crossings))


def bracketing_edges(crossings, component_coordinate):
    """Return the nearest scanline crossings on either side of a component."""
    before = [value for value in crossings if value <= component_coordinate]
    after = [value for value in crossings if value >= component_coordinate]
    if not before or not after:
        raise RuntimeError(
            "component centre is not bracketed by two Edge.Cuts crossings"
        )
    first, second = max(before), min(after)
    if first == second:
        raise RuntimeError("component centre lies on Edge.Cuts")
    return first, second


def main():
    """Move the configured footprint to its local board cross-section centre."""
    if ALIGNMENT not in {"horizontal", "vertical"}:
        raise ValueError('ALIGNMENT must be "horizontal" or "vertical"')

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    if COMPONENT_REFERENCE not in footprints:
        raise RuntimeError(f"missing footprint: {COMPONENT_REFERENCE}")
    footprint = footprints[COMPONENT_REFERENCE]

    bounding_box = board.get_item_bounding_box(
        footprint,
        include_text=INCLUDE_TEXT,
    )
    if bounding_box is None:
        raise RuntimeError(f"KiCad returned no bounding box for {COMPONENT_REFERENCE}")
    component_center = box_center(bounding_box)

    edge_items = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")

    contours = edge_contours(edge_items)
    fixed_coordinate = (
        component_center.y if ALIGNMENT == "horizontal" else component_center.x
    )
    component_coordinate = (
        component_center.x if ALIGNMENT == "horizontal" else component_center.y
    )
    crossings = scanline_crossings(contours, fixed_coordinate, ALIGNMENT)
    first_edge, second_edge = bracketing_edges(crossings, component_coordinate)
    target_coordinate = (first_edge + second_edge) // 2
    offset = target_coordinate - component_coordinate
    if offset == 0:
        print(
            f"{COMPONENT_REFERENCE} is already centered {ALIGNMENT}ly "
            "between Edge.Cuts."
        )
        return

    delta = vector(offset, 0) if ALIGNMENT == "horizontal" else vector(0, offset)
    action = f"Center {COMPONENT_REFERENCE} between board edges {ALIGNMENT}ly"
    with editor_commit(board, action, refill_zones=True):
        footprint.position = vector(
            footprint.position.x + delta.x,
            footprint.position.y + delta.y,
        )
        board.update_items([footprint])

    axis = "X" if ALIGNMENT == "horizontal" else "Y"
    print(
        f"Centered {COMPONENT_REFERENCE} {ALIGNMENT}ly between Edge.Cuts: "
        f"moved {axis} by {to_mm(offset):.6f} mm (undo: {action})."
    )


if __name__ == "__main__":
    main()
