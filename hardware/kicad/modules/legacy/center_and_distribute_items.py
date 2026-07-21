"""Centre and optionally distribute configured footprints using legacy pcbnew.

Execution:
    Open a board in KiCad's PCB Editor, adjust the settings below, then run
    this file from the PCB Editor scripting console with::

        import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/legacy/center_and_distribute_items.py")

Review the result in the editor and save the board manually.
"""

import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pcbnew_helpers import (  # noqa: E402
    bounding_box_center,
    get_current_board,
    iu_to_mm,
    vector,
)


# ============================================================
# User settings
# ============================================================
# Centre all footprints to the first component listed in REFERENCES.
# Optional distribution occurs on the axis perpendicular to the alignment.
REFERENCES = ["J1", "J2", "J3", "J4"]
ALIGNMENT = "horizontal"  # "vertical" aligns Y centres; "horizontal" aligns X centres.
DISTRIBUTE_SPACING = True
DEBUG = True


def distribution_offsets(items):
    """Return equal edge-to-edge spacing offsets for axis-sorted items.

    ``items`` contains ``(reference, start, end)`` tuples. The first and last
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


def get_footprint_by_reference(board, reference):
    """Return a footprint by reference or raise a useful error."""
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Footprint {reference} not found")
    return footprint


def center_and_distribute_items(board):
    """Centre footprints on the first reference and optionally distribute them."""
    if not REFERENCES:
        raise ValueError("REFERENCES must contain at least one component")
    if ALIGNMENT not in {"vertical", "horizontal"}:
        raise ValueError('ALIGNMENT must be "vertical" or "horizontal"')
    if DISTRIBUTE_SPACING and len(REFERENCES) < 3:
        raise ValueError("DISTRIBUTE_SPACING requires at least three references")

    footprints = {
        reference: get_footprint_by_reference(board, reference)
        for reference in REFERENCES
    }
    boxes = {
        reference: footprint.GetBoundingBox()
        for reference, footprint in footprints.items()
    }
    anchor_center = bounding_box_center(boxes[REFERENCES[0]])

    distribute_offsets = {reference: 0 for reference in REFERENCES}
    if DISTRIBUTE_SPACING:
        if ALIGNMENT == "vertical":
            axis_items = [
                (reference, boxes[reference].GetLeft(), boxes[reference].GetRight())
                for reference in REFERENCES
            ]
        else:
            axis_items = [
                (reference, boxes[reference].GetTop(), boxes[reference].GetBottom())
                for reference in REFERENCES
            ]
        axis_items = [
            (reference, min(start, end), max(start, end))
            for reference, start, end in axis_items
        ]
        distribute_offsets = distribution_offsets(axis_items)

    for reference in REFERENCES:
        footprint = footprints[reference]
        center = bounding_box_center(boxes[reference])
        old = footprint.GetPosition()
        if ALIGNMENT == "vertical":
            delta_x = distribute_offsets[reference]
            delta_y = anchor_center.y - center.y
        else:
            delta_x = anchor_center.x - center.x
            delta_y = distribute_offsets[reference]
        footprint.SetPosition(vector(old.x + delta_x, old.y + delta_y))

        if DEBUG:
            print(
                f"{reference}: moved X by {iu_to_mm(delta_x):.3f} mm, "
                f"Y by {iu_to_mm(delta_y):.3f} mm"
            )

    return len(REFERENCES)


board = get_current_board()

if board is None:
    print("Error: no board is currently open.")
else:
    try:
        changed = center_and_distribute_items(board)
        pcbnew.Refresh()
        action = f"Centered {changed} footprint(s) {ALIGNMENT}ly"
        if DISTRIBUTE_SPACING:
            action += " and distributed items"
        print(action + ". Save the board manually after review.")
    except Exception as error:
        print(f"Error: {error}")
