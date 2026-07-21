#!/usr/bin/env python3
"""Centre and optionally distribute configured footprints using KiCad's IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/center_and_distribute_items.py``.
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


# Centre all footprints to the first component listed in REFERENCES.
# Optional distribution occurs on the axis perpendicular to the alignment.
REFERENCES = ["J1", "J2", "J3", "J4"]
ALIGNMENT = "horizontal"  # "vertical" aligns Y centres; "horizontal" aligns X centres.
DISTRIBUTE_SPACING = True
DEBUG = True


def distribution_offsets(items):
    """Return equal edge-to-edge spacing offsets for axis-sorted items.

    ``items`` contains ``(reference, start, end)`` tuples.  The first and last
    items remain fixed and the intervening items are positioned so every gap
    is equal. Negative gaps intentionally support overlapping outer anchors.
    """
    ordered = sorted(items, key=lambda item: (item[1] + item[2], item[0]))
    first_end = ordered[0][2]
    last_start = ordered[-1][1]
    inner_width = sum(end - start for _reference, start, end in ordered[1:-1])
    gap = (last_start - first_end - inner_width) / (len(ordered) - 1)
    offsets = {ordered[0][0]: 0, ordered[-1][0]: 0}
    next_start = first_end + gap
    for reference, start, end in ordered[1:-1]:
        offsets[reference] = round(next_start - start)
        next_start += end - start + gap
    return offsets


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
            old = footprint.position
            if ALIGNMENT == "vertical":
                delta_x = distribute_offsets[reference]
                delta_y = anchor_center.y - center.y
            else:
                delta_x = anchor_center.x - center.x
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
