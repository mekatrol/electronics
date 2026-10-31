#!/usr/bin/env python3
"""Set the centre-to-centre spacing between two footprints.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/space_components.py

The anchor footprint remains fixed.  The moving footprint is translated along
the configured axis until its bounding-box centre is the requested distance
from the anchor's centre.  Its current side of the anchor is preserved.  The
move is grouped into one PCB Editor undo/redo transaction.  Save manually
after review.
"""

from kicad_ipc import (
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    to_mm,
    vector,
)

# User settings
ANCHOR_REFERENCE = "J1"
MOVING_REFERENCE = "H1"
ALIGNMENT = "vertical"  # "horizontal" spaces X centres; "vertical" spaces Y centres.
SPACING_MM = 20.0
INCLUDE_TEXT = False


def main():
    """Move one footprint to the configured spacing from the fixed footprint."""
    if ALIGNMENT not in {"horizontal", "vertical"}:
        raise ValueError('ALIGNMENT must be "horizontal" or "vertical"')
    if SPACING_MM < 0:
        raise ValueError("SPACING_MM must not be negative")
    if ANCHOR_REFERENCE == MOVING_REFERENCE:
        raise ValueError("ANCHOR_REFERENCE and MOVING_REFERENCE must differ")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    missing = [
        reference
        for reference in (ANCHOR_REFERENCE, MOVING_REFERENCE)
        if reference not in footprints
    ]
    if missing:
        raise RuntimeError(f"missing footprint(s): {', '.join(missing)}")

    centers = {}
    for reference in (ANCHOR_REFERENCE, MOVING_REFERENCE):
        bounding_box = board.get_item_bounding_box(
            footprints[reference],
            include_text=INCLUDE_TEXT,
        )
        if bounding_box is None:
            raise RuntimeError(f"KiCad returned no bounding box for {reference}")
        centers[reference] = box_center(bounding_box)

    anchor_center = centers[ANCHOR_REFERENCE]
    moving_center = centers[MOVING_REFERENCE]
    if ALIGNMENT == "horizontal":
        current_difference = moving_center.x - anchor_center.x
    else:
        current_difference = moving_center.y - anchor_center.y

    if current_difference == 0 and SPACING_MM != 0:
        raise RuntimeError(
            f"{ANCHOR_REFERENCE} and {MOVING_REFERENCE} have the same "
            f"{ALIGNMENT} centre; move {MOVING_REFERENCE} to the desired side first"
        )

    spacing = from_mm(SPACING_MM)
    direction = -1 if current_difference < 0 else 1
    target_difference = direction * spacing
    offset = target_difference - current_difference
    if offset == 0:
        print(
            f"{ANCHOR_REFERENCE} and {MOVING_REFERENCE} already have "
            f"{SPACING_MM:.6f} mm {ALIGNMENT} centre spacing."
        )
        return

    delta = vector(offset, 0) if ALIGNMENT == "horizontal" else vector(0, offset)
    moving = footprints[MOVING_REFERENCE]
    action = f"Space {MOVING_REFERENCE} from {ANCHOR_REFERENCE} {ALIGNMENT}ly"
    with editor_commit(board, action, refill_zones=True):
        moving.position = vector(
            moving.position.x + delta.x,
            moving.position.y + delta.y,
        )
        board.update_items([moving])

    axis = "X" if ALIGNMENT == "horizontal" else "Y"
    print(
        f"Set {MOVING_REFERENCE} {axis}-centre {SPACING_MM:.6f} mm from "
        f"{ANCHOR_REFERENCE}: moved {axis} by {to_mm(offset):.6f} mm "
        f"(undo: {action})."
    )


if __name__ == "__main__":
    main()
