#!/usr/bin/env python3
"""Place four mounting holes at configured board-edge offsets using IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/align_holes.py

The complete operation is one entry in PCB Editor's Undo/Redo history.
"""

from kicad_ipc import (
    board_edge_bounds,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    to_mm,
    vector,
)


# Footprint references for the four physical corners.
TOP_LEFT_HOLE_REF = "H1"
TOP_RIGHT_HOLE_REF = "H2"
BOTTOM_LEFT_HOLE_REF = "H3"
BOTTOM_RIGHT_HOLE_REF = "H4"

# Hole-centre distances from the corresponding fabrication edges.
LEFT_OFFSET_MM = 3.50
RIGHT_OFFSET_MM = 3.50
TOP_OFFSET_MM = 3.50
BOTTOM_OFFSET_MM = 3.50
DEBUG = True


def main():
    """Move configured holes and publish one undoable editor transaction."""
    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    left, right, top, bottom = board_edge_bounds(board)
    targets = {
        TOP_LEFT_HOLE_REF: vector(left + from_mm(LEFT_OFFSET_MM), top + from_mm(TOP_OFFSET_MM)),
        TOP_RIGHT_HOLE_REF: vector(right - from_mm(RIGHT_OFFSET_MM), top + from_mm(TOP_OFFSET_MM)),
        BOTTOM_LEFT_HOLE_REF: vector(
            left + from_mm(LEFT_OFFSET_MM), bottom - from_mm(BOTTOM_OFFSET_MM)
        ),
        BOTTOM_RIGHT_HOLE_REF: vector(
            right - from_mm(RIGHT_OFFSET_MM), bottom - from_mm(BOTTOM_OFFSET_MM)
        ),
    }

    missing = [reference for reference in targets if reference not in footprints]
    if missing:
        raise RuntimeError(f"missing mounting-hole footprint(s): {', '.join(missing)}")

    changed = []
    with editor_commit(board, "Align mounting holes"):
        for reference, target in targets.items():
            footprint = footprints[reference]
            old = footprint.position
            footprint.position = target
            changed.append(footprint)
            if DEBUG:
                print(
                    f"{reference}: ({to_mm(old.x):.3f}, {to_mm(old.y):.3f}) -> "
                    f"({to_mm(target.x):.3f}, {to_mm(target.y):.3f}) mm"
                )
        board.update_items(changed)

    print(f"Aligned {len(changed)} mounting holes (undo: Align mounting holes).")


if __name__ == "__main__":
    main()
