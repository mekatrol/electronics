"""Place mounting holes at configured board-edge offsets using IPC.

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

# Axes to align: "horizontal" changes X, "vertical" changes Y, and "both" changes both.
DIRECTION = "horizontal"

# Hole-centre distances from the corresponding fabrication edges.
LEFT_OFFSET_MM = 3.0
RIGHT_OFFSET_MM = 3.0
TOP_OFFSET_MM = 35.50
BOTTOM_OFFSET_MM = 5.50
DEBUG = True


def main():
    """Move configured holes and publish one undoable editor transaction."""
    if DIRECTION not in {"horizontal", "vertical", "both"}:
        raise ValueError('DIRECTION must be "horizontal", "vertical", or "both"')

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    left, right, top, bottom = board_edge_bounds(board)
    targets = {
        TOP_LEFT_HOLE_REF: vector(
            left + from_mm(LEFT_OFFSET_MM), top + from_mm(TOP_OFFSET_MM)
        ),
        TOP_RIGHT_HOLE_REF: vector(
            right - from_mm(RIGHT_OFFSET_MM), top + from_mm(TOP_OFFSET_MM)
        ),
        BOTTOM_LEFT_HOLE_REF: vector(
            left + from_mm(LEFT_OFFSET_MM), bottom - from_mm(BOTTOM_OFFSET_MM)
        ),
        BOTTOM_RIGHT_HOLE_REF: vector(
            right - from_mm(RIGHT_OFFSET_MM), bottom - from_mm(BOTTOM_OFFSET_MM)
        ),
    }

    changed = []
    with editor_commit(board, "Align mounting holes"):
        for reference, target in targets.items():
            if reference not in footprints:
                continue
            footprint = footprints[reference]
            old = footprint.position
            footprint.position = vector(
                target.x if DIRECTION in {"horizontal", "both"} else old.x,
                target.y if DIRECTION in {"vertical", "both"} else old.y,
            )
            changed.append(footprint)
            if DEBUG:
                new = footprint.position
                print(
                    f"{reference}: ({to_mm(old.x):.3f}, {to_mm(old.y):.3f}) -> "
                    f"({to_mm(new.x):.3f}, {to_mm(new.y):.3f}) mm"
                )
        if changed:
            board.update_items(changed)

    print(f"Aligned {len(changed)} mounting holes (undo: Align mounting holes).")


if __name__ == "__main__":
    main()
