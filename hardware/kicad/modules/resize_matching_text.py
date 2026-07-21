# Run with:
# exec(open("/home/dad/repos/electronics/hardware/kicad/modules/resize_matching_text.py").read())

import pcbnew


# ============================================================
# User settings
# ============================================================
# Only board text whose complete text exactly matches one of these strings is
# changed. Add or remove entries here to alter the set of text to resize.
TEXT_STRINGS = ["GND", "5V", "D", "JLCJLCJLCJLC"]

TEXT_WIDTH_MM = 0.8
TEXT_HEIGHT_MM = 0.8
TEXT_THICKNESS_MM = 0.1


def is_board_text(item):
    """Return True for board text while remaining compatible across KiCad versions."""
    return all(
        hasattr(item, method_name)
        for method_name in ("GetText", "SetTextSize", "SetTextThickness")
    )


def resize_matching_text(board):
    """Resize board text with an exact match in TEXT_STRINGS."""
    target_strings = set(TEXT_STRINGS)
    text_size = pcbnew.VECTOR2I(
        pcbnew.FromMM(TEXT_WIDTH_MM),
        pcbnew.FromMM(TEXT_HEIGHT_MM),
    )
    text_thickness = pcbnew.FromMM(TEXT_THICKNESS_MM)
    changed_count = 0

    # Free-standing text placed on a PCB is stored in the board drawings.
    # Footprint fields and footprint graphical text are intentionally excluded.
    for item in board.GetDrawings():
        if not is_board_text(item) or item.GetText() not in target_strings:
            continue

        item.SetTextSize(text_size)
        item.SetTextThickness(text_thickness)
        changed_count += 1

    return changed_count


board = pcbnew.GetBoard()

if board is None:
    print("Error: no board is currently open.")
else:
    changed_count = resize_matching_text(board)
    pcbnew.Refresh()

    print(
        f"Updated {changed_count} matching board text item(s) to "
        f"{TEXT_WIDTH_MM:.3f} mm wide, {TEXT_HEIGHT_MM:.3f} mm high, "
        f"with {TEXT_THICKNESS_MM:.3f} mm line thickness."
    )
