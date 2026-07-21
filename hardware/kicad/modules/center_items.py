"""Vertically centre configured footprints within the board outline.

Execution:
    Open a board in KiCad's PCB Editor, adjust ``REFERENCES`` and the tolerance
    below, then run this file from the PCB Editor scripting console with::

        import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/center_items.py")

Review the result in the editor and save the board manually.
"""

import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pcbnew_helpers import get_current_board, iu_to_mm, mm_to_iu  # noqa: E402


# ============================================================
# User settings
# ============================================================
REFERENCES = ["J1", "J2"]
HORIZONTAL_TOLERANCE_MM = 0.01
DEBUG = True


def is_horizontal_edge(shape, tol_iu):
    """Return whether an item is a horizontal Edge.Cuts segment."""
    try:
        if shape.GetLayer() != pcbnew.Edge_Cuts:
            return False
    except Exception:
        return False

    try:
        if shape.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            return False
    except Exception:
        pass

    try:
        a = shape.GetStart()
        b = shape.GetEnd()
    except Exception:
        return False

    return abs(a.y - b.y) <= tol_iu


def find_board_vertical_center(board, tol_iu):
    """Return the board centre and extreme horizontal edge coordinates."""
    ys = []

    for item in board.GetDrawings():
        if is_horizontal_edge(item, tol_iu):
            a = item.GetStart()
            b = item.GetEnd()
            ys.append((a.y + b.y) // 2)

    if len(ys) < 2:
        raise RuntimeError("Need at least two horizontal Edge.Cuts segments")

    ys.sort()
    bottom_y = ys[0]
    top_y = ys[-1]
    return (bottom_y + top_y) // 2, bottom_y, top_y


def get_footprint_by_reference(board, reference):
    """Return a footprint by reference or raise a useful error."""
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise RuntimeError(f"Footprint {reference} not found")
    return footprint


def center_items(board):
    """Vertically centre configured footprints and return board coordinates."""
    tolerance_iu = mm_to_iu(HORIZONTAL_TOLERANCE_MM)
    target_center_y, bottom_y, top_y = find_board_vertical_center(
        board,
        tolerance_iu,
    )

    for reference in REFERENCES:
        footprint = get_footprint_by_reference(board, reference)
        old_anchor = footprint.GetPosition()
        bbox = footprint.GetBoundingBox()
        bbox_center_y = bbox.GetY() + bbox.GetHeight() // 2
        delta_y = target_center_y - bbox_center_y
        new_anchor = pcbnew.VECTOR2I(old_anchor.x, old_anchor.y + delta_y)
        footprint.SetPosition(new_anchor)

        if DEBUG:
            print(reference)
            print(f"  anchor old Y   : {iu_to_mm(old_anchor.y):.3f} mm")
            print(f"  bbox center old: {iu_to_mm(bbox_center_y):.3f} mm")
            print(f"  target center Y: {iu_to_mm(target_center_y):.3f} mm")
            print(f"  move delta Y   : {iu_to_mm(delta_y):.3f} mm")
            print(f"  anchor new Y   : {iu_to_mm(new_anchor.y):.3f} mm")

    return target_center_y, bottom_y, top_y


board = get_current_board()

if board is None:
    print("Error: no board is currently open.")
else:
    try:
        target_center_y, bottom_y, top_y = center_items(board)
        pcbnew.Refresh()

        if DEBUG:
            print(f"Bottom edge Y: {iu_to_mm(bottom_y):.3f} mm")
            print(f"Top edge Y:    {iu_to_mm(top_y):.3f} mm")
            print(f"Board center Y:{iu_to_mm(target_center_y):.3f} mm")
    except Exception as error:
        print(f"Error: {error}")
