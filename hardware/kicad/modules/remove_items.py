#!/usr/bin/env python3
"""Remove every track, via, and copper zone from the active PCB using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/remove_items.py

All tracks (including curved tracks), vias, and zones on every layer are
removed in one PCB Editor undo/redo transaction. Save the board manually after
reviewing the result.
"""

from kicad_ipc import connect_board, editor_commit

REMOVE_TRACKS = False
REMOVE_VIAS = False
REMOVE_ZONES = True


def main():
    """Remove all tracks, vias, and zones from the board open in PCB Editor."""
    _client, board = connect_board()
    tracks = list(board.get_tracks()) if REMOVE_TRACKS else []
    vias = list(board.get_vias()) if REMOVE_VIAS else []
    zones = list(board.get_zones()) if REMOVE_ZONES else []

    if not tracks and not vias and not zones:
        print("There were no tracks, vias, or zones selected to remove.")
        return

    action = "Remove all tracks, vias, and zones"
    with editor_commit(board, action):
        if tracks:
            board.remove_items(tracks)
        if vias:
            board.remove_items(vias)
        if zones:
            board.remove_items(zones)

    print(
        f"Removed {len(tracks)} track(s), {len(vias)} via(s), and "
        f"{len(zones)} zone(s) "
        f"(undo: {action})."
    )


if __name__ == "__main__":
    main()
