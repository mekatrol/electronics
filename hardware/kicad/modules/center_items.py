#!/usr/bin/env python3
"""Vertically centre configured footprints using KiCad's IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/center_items.py``.
All moves are grouped into one PCB Editor undo/redo transaction.
"""

from kicad_ipc import (
    board_edge_bounds,
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    to_mm,
    vector,
)


REFERENCES = ["J1", "J2"]
DEBUG = True


def main():
    """Centre each configured footprint's full graphical bounding box."""
    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    _left, _right, top, bottom = board_edge_bounds(board)
    target_y = (top + bottom) // 2
    missing = [reference for reference in REFERENCES if reference not in footprints]
    if missing:
        raise RuntimeError(f"missing footprint(s): {', '.join(missing)}")

    changed = []
    with editor_commit(board, "Center footprints vertically"):
        for reference in REFERENCES:
            footprint = footprints[reference]
            bbox = board.get_item_bounding_box(footprint, include_text=True)
            if bbox is None:
                raise RuntimeError(f"KiCad returned no bounding box for {reference}")
            delta_y = target_y - box_center(bbox).y
            old = footprint.position
            footprint.position = vector(old.x, old.y + delta_y)
            changed.append(footprint)
            if DEBUG:
                print(f"{reference}: moved Y by {to_mm(delta_y):.3f} mm")
        board.update_items(changed)

    print(f"Centered {len(changed)} footprint(s) (undo: Center footprints vertically).")


if __name__ == "__main__":
    main()
