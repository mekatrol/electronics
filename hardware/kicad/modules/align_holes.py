"""Place four mounting-hole footprints at configured board-edge offsets.

Execution:
    Open a board in KiCad's PCB Editor, adjust the references and offsets
    below, then run this file from the PCB Editor scripting console with::

        import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/align_holes.py")

Review the result in the editor and save the board manually.
"""

import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pcbnew_helpers import (  # noqa: E402
    board_edge_bounds,
    get_current_board,
    iu_to_mm,
    mm_to_iu,
)


# =========================
# Hole references
# =========================
TOP_LEFT_HOLE_REF = "H1"
TOP_RIGHT_HOLE_REF = "H2"
BOTTOM_LEFT_HOLE_REF = "H3"
BOTTOM_RIGHT_HOLE_REF = "H4"


# =========================
# Offsets from board edges
# =========================
# Hole-centre distances from their corresponding board edges.
LEFT_OFFSET_MM = 3.55
RIGHT_OFFSET_MM = 3.55
TOP_OFFSET_MM = 3.55
BOTTOM_OFFSET_MM = 3.55

DEBUG = True


def get_footprint_by_ref(board, reference):
    """Find a configured mounting-hole footprint, warning when absent."""
    footprint = board.FindFootprintByReference(reference)

    if footprint is None:
        print(f"Warning: footprint {reference} was not found; skipping it.")
        return None

    return footprint


def move_hole_to(board, reference, target_x, target_y):
    """Move one mounting-hole anchor to a target board coordinate."""
    footprint = get_footprint_by_ref(board, reference)

    if footprint is None:
        return False

    old_position = footprint.GetPosition()
    new_position = pcbnew.VECTOR2I(target_x, target_y)

    footprint.SetPosition(new_position)

    if DEBUG:
        print(reference)
        print(f"  old X: {iu_to_mm(old_position.x):.3f} mm")
        print(f"  old Y: {iu_to_mm(old_position.y):.3f} mm")
        print(f"  new X: {iu_to_mm(new_position.x):.3f} mm")
        print(f"  new Y: {iu_to_mm(new_position.y):.3f} mm")
        print(f"  dx   : {iu_to_mm(new_position.x - old_position.x):.3f} mm")
        print(f"  dy   : {iu_to_mm(new_position.y - old_position.y):.3f} mm")

    return True


board = get_current_board()

if board is None:
    print("Error: no board is currently open.")
else:
    left_x, right_x, top_y, bottom_y = board_edge_bounds(board)

    left_offset_iu = mm_to_iu(LEFT_OFFSET_MM)
    right_offset_iu = mm_to_iu(RIGHT_OFFSET_MM)
    top_offset_iu = mm_to_iu(TOP_OFFSET_MM)
    bottom_offset_iu = mm_to_iu(BOTTOM_OFFSET_MM)

    targets = {
        TOP_LEFT_HOLE_REF: (
            left_x + left_offset_iu,
            top_y + top_offset_iu,
        ),
        TOP_RIGHT_HOLE_REF: (
            right_x - right_offset_iu,
            top_y + top_offset_iu,
        ),
        BOTTOM_LEFT_HOLE_REF: (
            left_x + left_offset_iu,
            bottom_y - bottom_offset_iu,
        ),
        BOTTOM_RIGHT_HOLE_REF: (
            right_x - right_offset_iu,
            bottom_y - bottom_offset_iu,
        ),
    }

    moved_count = 0

    for reference, target_position in targets.items():
        target_x, target_y = target_position

        if move_hole_to(board, reference, target_x, target_y):
            moved_count += 1

    pcbnew.Refresh()

    if DEBUG:
        print()
        print("Board edges")
        print(f"  left   : {iu_to_mm(left_x):.3f} mm")
        print(f"  right  : {iu_to_mm(right_x):.3f} mm")
        print(f"  top    : {iu_to_mm(top_y):.3f} mm")
        print(f"  bottom : {iu_to_mm(bottom_y):.3f} mm")

        print()
        print("Targets")

        for reference, target_position in targets.items():
            target_x, target_y = target_position

            print(
                f"  {reference}: "
                f"X={iu_to_mm(target_x):.3f} mm, "
                f"Y={iu_to_mm(target_y):.3f} mm"
            )

        print()
        print(f"Moved {moved_count} of {len(targets)} holes.")
