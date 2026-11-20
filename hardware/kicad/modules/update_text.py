"""Resize board text or resize and align footprint references using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/update_text.py

All changes form one PCB Editor undo/redo transaction. The board is left
unsaved so the editor remains the authority for Undo, Redo, and Save.
"""

from kicad_ipc import (
    box_center,
    box_edges,
    connect_board,
    courtyard_box,
    editor_commit,
    footprint_reference,
    from_mm,
    move_text_center,
    text_box,
    to_mm,
    vector,
)
from kipy.board_types import BoardText
from kipy.geometry import Vector2

# "component_reference" or "board_text"
# TEXT_TYPE = "component_reference"
TEXT_TYPE = "board_text"

IGNORE_TEXT = ["A", "B"]
MATCH_WIDTH_MM = 1
NEW_WIDTH_MM = 0.8
MATCH_HEIGHT_MM = 1
NEW_HEIGHT_MM = 0.8
MATCH_THICKNESS_MM = 0.1
NEW_THICKNESS_MM = 0.15
TEXT_OFFSET_MM = 0.0
OTHER_COURTYARD_CLEARANCE_MM = 0.1


CENTRED_TEXT_SIDE = "top"
DEBUG = True


def resize_matching_axes(text):
    """Replace matching text dimensions and set the configured thickness."""
    attributes = text.attributes
    width, height = attributes.size.x, attributes.size.y
    new_width, new_height = width, height
    thickness = attributes.stroke_width
    new_thickness = thickness

    if MATCH_WIDTH_MM is not None and width == from_mm(MATCH_WIDTH_MM):
        new_width = from_mm(NEW_WIDTH_MM)
    if MATCH_HEIGHT_MM is not None and height == from_mm(MATCH_HEIGHT_MM):
        new_height = from_mm(NEW_HEIGHT_MM)
    if MATCH_THICKNESS_MM is not None and thickness == from_mm(MATCH_THICKNESS_MM):
        new_thickness = from_mm(NEW_THICKNESS_MM)

    if (new_width, new_height) == (width, height) and thickness == new_thickness:
        return False
    attributes.size = Vector2.from_xy(new_width, new_height)
    attributes.stroke_width = new_thickness
    text.attributes = attributes
    return True


def validate_resize_settings():
    """Require complete, positive match/replacement pairs."""
    if TEXT_TYPE not in {"component_reference", "board_text"}:
        raise ValueError("TEXT_TYPE must be 'component_reference' or 'board_text'")
    for attribute, match, replacement in (
        ("width", MATCH_WIDTH_MM, NEW_WIDTH_MM),
        ("height", MATCH_HEIGHT_MM, NEW_HEIGHT_MM),
        ("thickness", MATCH_THICKNESS_MM, NEW_THICKNESS_MM),
    ):
        if (match is None) != (replacement is None):
            raise ValueError(
                f"MATCH_{attribute.upper()}_MM and NEW_{attribute.upper()}_MM must "
                "both be numbers or both be None"
            )
        if match is not None and (match <= 0 or replacement <= 0):
            raise ValueError(f"configured {attribute} values must be positive")


def current_side(text_bounds, courtyard):
    """Choose the side using displacement normalized by courtyard dimensions.

    Normalizing prevents a long rectangular footprint from selecting its long
    axis merely because the raw coordinate displacement is numerically larger.
    """
    text_center = box_center(text_bounds)
    court_center = box_center(courtyard)
    dx, dy = text_center.x - court_center.x, text_center.y - court_center.y
    if dx == 0 and dy == 0:
        return CENTRED_TEXT_SIDE
    left, right, top, bottom = box_edges(courtyard)
    half_width = max((right - left) / 2.0, 1.0)
    half_height = max((bottom - top) / 2.0, 1.0)
    if abs(dx / half_width) > abs(dy / half_height):
        return "right" if dx > 0 else "left"
    return "bottom" if dy > 0 else "top"


def target_center(text_bounds, courtyard, side):
    """Move only the axis perpendicular to the selected courtyard side.

    A left/right placement changes X but preserves the text's current Y. A
    top/bottom placement changes Y but preserves its current X. Preserving the
    parallel axis avoids unexpectedly centering manually offset text.
    """
    left, right, top, bottom = box_edges(courtyard)
    text_left, text_right, text_top, text_bottom = box_edges(text_bounds)
    half_width = (text_right - text_left) // 2
    half_height = (text_bottom - text_top) // 2
    current = box_center(text_bounds)
    gap = from_mm(TEXT_OFFSET_MM)
    if side == "left":
        return vector(left - gap - half_width, current.y)
    if side == "right":
        return vector(right + gap + half_width, current.y)
    if side == "top":
        return vector(current.x, top - gap - half_height)
    if side == "bottom":
        return vector(current.x, bottom + gap + half_height)
    raise ValueError(f"invalid text side: {side}")


def moved_edges(text_bounds, destination):
    """Return text bounds translated to a proposed centre point."""
    current = box_center(text_bounds)
    left, right, top, bottom = box_edges(text_bounds)
    dx, dy = destination.x - current.x, destination.y - current.y
    return left + dx, right + dx, top + dy, bottom + dy


def intersects(proposed, courtyard, clearance):
    """Test an axis-aligned proposed text box against an inflated courtyard."""
    left, right, top, bottom = proposed
    c_left, c_right, c_top, c_bottom = box_edges(courtyard)
    return not (
        right < c_left - clearance
        or left > c_right + clearance
        or bottom < c_top - clearance
        or top > c_bottom + clearance
    )


def update_board_text(board):
    """Resize matching free-standing board text without moving it."""
    footprint_ids = [footprint.id for footprint in board.get_footprints()]
    targets = [
        text
        for text in board.get_text()
        if isinstance(text, BoardText)
        and text.parent not in footprint_ids
        and text.value not in IGNORE_TEXT
    ]
    changed = []
    with editor_commit(board, "Update board text"):
        for text in targets:
            if resize_matching_axes(text):
                changed.append(text)
        board.update_items(changed)

    if not changed:
        print("No matching board text was changed.")
        return
    print(
        f"Updated {len(changed)} of {len(targets)} board text item(s) "
        "(undo: Update board text)."
    )


def update_component_text(client, board):
    """Resize/align component text and push one editor commit."""
    records = []
    for footprint in board.get_footprints():
        text_value = footprint_reference(footprint)
        try:
            records.append((footprint, text_value, courtyard_box(footprint)))
        except RuntimeError as error:
            print(f"Warning: {text_value}: {error}; skipped")

    changed = []
    resized_count = 0
    aligned_count = 0
    clearance = from_mm(OTHER_COURTYARD_CLEARANCE_MM)
    with editor_commit(board, "Update component text"):
        for footprint, text_value, courtyard in records:
            if text_value in IGNORE_TEXT or not footprint.reference_field.visible:
                continue
            text = footprint.reference_field.text
            resized = resize_matching_axes(text)
            if resized:
                footprint.reference_field.text = text
                resized_count += 1
            bounds = text_box(client, text)
            side = current_side(bounds, courtyard)
            destination = target_center(bounds, courtyard, side)
            proposed = moved_edges(bounds, destination)
            same_board_side = footprint.layer
            collisions = [
                other_text_value
                for other, other_text_value, other_courtyard in records
                if other is not footprint
                and other.layer == same_board_side
                and intersects(proposed, other_courtyard, clearance)
            ]
            if collisions:
                print(
                    f"Warning: {text_value}: would overlap "
                    f"{', '.join(collisions)}; alignment skipped"
                )
                if resized:
                    changed.append(footprint)
                continue
            move_text_center(client, text, destination)
            footprint.reference_field.text = text
            changed.append(footprint)
            aligned_count += 1
            if DEBUG:
                print(
                    f"{text_value}: {side} at ({to_mm(destination.x):.3f}, "
                    f"{to_mm(destination.y):.3f}) mm"
                    f"{' (resized)' if resized else ''}"
                )
        board.update_items(changed)

    print(
        f"Resized {resized_count} and aligned {aligned_count} component text "
        "item(s) (undo: Update component text)."
    )


def main():
    """Update the configured text type through one editor commit."""
    validate_resize_settings()
    client, board = connect_board()
    if TEXT_TYPE == "board_text":
        update_board_text(board)
    else:
        update_component_text(client, board)


if __name__ == "__main__":
    main()
