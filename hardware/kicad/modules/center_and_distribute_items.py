#!/usr/bin/env python3
"""Centre and optionally distribute configured footprints using KiCad's IPC API.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/center_and_distribute_items.py

All moves are grouped into one PCB Editor undo/redo transaction.
"""

from kicad_ipc import (
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    to_mm,
    vector,
)
from kicad_utils import centering_delta, distribution_offsets


# Centre all footprints to the first component listed in REFERENCES.
# Optional distribution occurs on the axis perpendicular to the alignment.
REFERENCES = ["J1", "J2", "J3", "J4"]
ALIGNMENT = "horizontal"  # "vertical" aligns Y centres; "horizontal" aligns X centres.
DISTRIBUTE_SPACING = True
DEBUG = True


def main():
    """Centre footprints on the first reference and optionally distribute them."""
    if not REFERENCES:
        raise ValueError("REFERENCES must contain at least one component")
    if ALIGNMENT not in {"vertical", "horizontal"}:
        raise ValueError('ALIGNMENT must be "vertical" or "horizontal"')
    if DISTRIBUTE_SPACING and len(REFERENCES) < 3:
        raise ValueError("DISTRIBUTE_SPACING requires at least three references")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    missing = [reference for reference in REFERENCES if reference not in footprints]
    if missing:
        raise RuntimeError(f"missing footprint(s): {', '.join(missing)}")

    boxes = {}
    for reference in REFERENCES:
        bbox = board.get_item_bounding_box(footprints[reference], include_text=True)
        if bbox is None:
            raise RuntimeError(f"KiCad returned no bounding box for {reference}")
        boxes[reference] = bbox

    anchor_center = box_center(boxes[REFERENCES[0]])

    distribute_offsets = {reference: 0 for reference in REFERENCES}
    if DISTRIBUTE_SPACING:
        if ALIGNMENT == "vertical":
            axis_items = [
                (reference, boxes[reference].pos.x,
                 boxes[reference].pos.x + boxes[reference].size.x)
                for reference in REFERENCES
            ]
        else:
            axis_items = [
                (reference, boxes[reference].pos.y,
                 boxes[reference].pos.y + boxes[reference].size.y)
                for reference in REFERENCES
            ]
        # Bounding boxes can have negative sizes; normalise their axis edges.
        axis_items = [
            (reference, min(start, end), max(start, end))
            for reference, start, end in axis_items
        ]
        distribute_offsets = distribution_offsets(axis_items)

    action = f'Center footprints {ALIGNMENT}ly'
    if DISTRIBUTE_SPACING:
        action += " and distribute items"
    changed = []
    with editor_commit(board, action):
        for reference in REFERENCES:
            footprint = footprints[reference]
            center = box_center(boxes[reference])
            alignment_offset = centering_delta(center, anchor_center)
            old = footprint.position
            if ALIGNMENT == "vertical":
                delta_x = distribute_offsets[reference]
                delta_y = alignment_offset.y
            else:
                delta_x = alignment_offset.x
                delta_y = distribute_offsets[reference]
            footprint.position = vector(old.x + delta_x, old.y + delta_y)
            changed.append(footprint)
            if DEBUG:
                print(
                    f"{reference}: moved X by {to_mm(delta_x):.3f} mm, "
                    f"Y by {to_mm(delta_y):.3f} mm"
                )
        board.update_items(changed)

    print(f"Centered {len(changed)} footprint(s) (undo: {action}).")


if __name__ == "__main__":
    main()
