#!/usr/bin/env python3
"""Centre all footprints within the Edge.Cuts bounds using KiCad's IPC API.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/center_components.py

All footprints move by one shared offset, preserving their relative positions.
The board centre is the centre of the axis-aligned Edge.Cuts bounding rectangle,
not the area centroid of an irregular polygon. Save manually after review.
"""

from kicad_ipc import (
    board_edge_bounds,
    box_edges,
    connect_board,
    editor_commit,
    footprint_reference,
    merge_boxes,
    to_mm,
    vector,
)


# User settings: include reference/value text in the component bounds if desired.
INCLUDE_TEXT = False


def main():
    """Translate every footprint together in one PCB Editor undo entry."""
    _client, board = connect_board()
    footprints = list(board.get_footprints())
    if not footprints:
        print("No footprints to center.")
        return

    left, right, top, bottom = board_edge_bounds(board)
    if left == right or top == bottom:
        raise RuntimeError("Edge.Cuts must have non-zero width and height")

    boxes = []
    for footprint in footprints:
        box = board.get_item_bounding_box(footprint, include_text=INCLUDE_TEXT)
        if box is None:
            raise RuntimeError(
                f"KiCad returned no bounding box for {footprint_reference(footprint)}"
            )
        boxes.append(box)

    fp_left, fp_right, fp_top, fp_bottom = box_edges(merge_boxes(boxes))
    # Round the shared translation once to KiCad's integer nanometre grid.
    delta_x = round((left + right - fp_left - fp_right) / 2)
    delta_y = round((top + bottom - fp_top - fp_bottom) / 2)
    if delta_x == 0 and delta_y == 0:
        print("Components are already centered within Edge.Cuts.")
        return

    action = "Center all components within board"
    with editor_commit(board, action, refill_zones=True):
        for footprint in footprints:
            old = footprint.position
            footprint.position = vector(old.x + delta_x, old.y + delta_y)
        board.update_items(footprints)

    print(
        f"Centered {len(footprints)} footprint(s): "
        f"moved X by {to_mm(delta_x):.6f} mm, "
        f"Y by {to_mm(delta_y):.6f} mm (undo: {action})."
    )


if __name__ == "__main__":
    main()
