"""Centre every footprint as a group inside the board outline.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/center_components_inside_edge.py

All footprints receive the same translation, preserving their relative layout.
Tracks and vias stay fixed. The move is one PCB Editor undo/redo transaction;
save manually after reviewing the result.
"""

from kicad_ipc import (
    BoardLayer,
    box_center,
    connect_board,
    editor_commit,
    footprint_reference,
    merge_boxes,
    to_mm,
    vector,
)
from kicad_utils import centering_delta, edge_cuts_centroid

# Reference and value text can make a footprint's bounds much larger than its
# physical body. Keep it excluded by default when centring the component group.
INCLUDE_TEXT = False


def main():
    """Translate all footprints so their combined bounds centre on Edge.Cuts."""
    _client, board = connect_board()
    footprints = list(board.get_footprints())
    if not footprints:
        print("No footprints to center.")
        return

    edge_items = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")

    footprint_boxes = []
    for footprint in footprints:
        box = board.get_item_bounding_box(footprint, include_text=INCLUDE_TEXT)
        if box is None:
            raise RuntimeError(
                f"KiCad returned no bounding box for {footprint_reference(footprint)}"
            )
        footprint_boxes.append(box)

    component_center = box_center(merge_boxes(footprint_boxes))
    board_center = edge_cuts_centroid(edge_items)
    delta = centering_delta(component_center, board_center)
    delta_x, delta_y = delta.x, delta.y
    if delta_x == 0 and delta_y == 0:
        print("All footprints are already centered inside Edge.Cuts.")
        return

    action = "Center all footprints inside board outline"
    with editor_commit(board, action, refill_zones=True):
        for footprint in footprints:
            old = footprint.position
            footprint.position = vector(old.x + delta_x, old.y + delta_y)
        board.update_items(footprints)

    print(
        f"Centered {len(footprints)} footprint(s) inside Edge.Cuts: "
        f"moved X by {to_mm(delta_x):.6f} mm and "
        f"Y by {to_mm(delta_y):.6f} mm (undo: {action})."
    )
    if list(board.get_tracks()):
        print(
            "Warning: tracks and vias were not moved; inspect routed connections "
            "and run DRC before saving."
        )


if __name__ == "__main__":
    main()
