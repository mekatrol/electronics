#!/usr/bin/env python3
"""Resize exactly matching free board text through KiCad's IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/resize_matching_text.py``.
The update appears as one item in PCB Editor's Undo/Redo history.
"""

from kipy.board_types import BoardText
from kipy.geometry import Vector2

from kicad_ipc import connect_board, editor_commit, from_mm


TEXT_STRINGS = ["GND", "5V", "D", "JLCJLCJLCJLC"]
TEXT_WIDTH_MM = 0.8
TEXT_HEIGHT_MM = 0.8
TEXT_THICKNESS_MM = 0.1


def main():
    """Resize matching text and push one undoable editor transaction."""
    _client, board = connect_board()
    targets = [
        text for text in board.get_text()
        if isinstance(text, BoardText) and text.value in set(TEXT_STRINGS)
    ]
    if not targets:
        print("No matching board text was found; no undo entry was created.")
        return

    with editor_commit(board, "Resize matching board text"):
        for text in targets:
            attributes = text.attributes
            attributes.size = Vector2.from_xy(
                from_mm(TEXT_WIDTH_MM),
                from_mm(TEXT_HEIGHT_MM),
            )
            attributes.stroke_width = from_mm(TEXT_THICKNESS_MM)
            text.attributes = attributes
        board.update_items(targets)

    print(
        f"Resized {len(targets)} text item(s) to {TEXT_WIDTH_MM:.3f} x "
        f"{TEXT_HEIGHT_MM:.3f} mm, stroke {TEXT_THICKNESS_MM:.3f} mm "
        "(undo: Resize matching board text)."
    )


if __name__ == "__main__":
    main()
