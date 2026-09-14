#!/usr/bin/env python3
"""Resize and align visible footprint references using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/component_reference_text.py

All changed references form one PCB Editor undo/redo transaction. The board is
left unsaved so the editor remains the authority for Undo, Redo, and Save.
"""

from kicad_ipc import (
    box_center, box_edges, connect_board, courtyard_box,
    editor_commit, footprint_reference, from_mm, move_text_center, text_box,
    to_mm, vector,
)
from kipy.geometry import Vector2


IGNORE_REFERENCES = []
MATCH_WIDTH_MM = 0.8
NEW_WIDTH_MM = 1.0
MATCH_HEIGHT_MM = 0.8
NEW_HEIGHT_MM = 1.0
REFERENCE_OFFSET_MM = 0.0
OTHER_COURTYARD_CLEARANCE_MM = 0.1
CENTRED_REFERENCE_SIDE = "top"
DEBUG = True


def resize_matching_axes(text):
    """Replace each configured text dimension when that axis matches."""
    attributes = text.attributes
    width, height = attributes.size.x, attributes.size.y
    new_width, new_height = width, height

    if MATCH_WIDTH_MM is not None and width == from_mm(MATCH_WIDTH_MM):
        new_width = from_mm(NEW_WIDTH_MM)
    if MATCH_HEIGHT_MM is not None and height == from_mm(MATCH_HEIGHT_MM):
        new_height = from_mm(NEW_HEIGHT_MM)

    if (new_width, new_height) == (width, height):
        return False
    attributes.size = Vector2.from_xy(new_width, new_height)
    text.attributes = attributes
    return True


def validate_resize_settings():
    """Require complete, positive match/replacement pairs for each axis."""
    for axis, match, replacement in (
        ("width", MATCH_WIDTH_MM, NEW_WIDTH_MM),
        ("height", MATCH_HEIGHT_MM, NEW_HEIGHT_MM),
    ):
        if (match is None) != (replacement is None):
            raise ValueError(
                f"MATCH_{axis.upper()}_MM and NEW_{axis.upper()}_MM must "
                "both be numbers or both be None"
            )
        if match is not None and (match <= 0 or replacement <= 0):
            raise ValueError(f"configured {axis} values must be positive")


def current_side(text_bounds, courtyard):
    """Choose the side using displacement normalized by courtyard dimensions.

    Normalizing prevents a long rectangular footprint from selecting its long
    axis merely because the raw coordinate displacement is numerically larger.
    """
    text_center = box_center(text_bounds)
    court_center = box_center(courtyard)
    dx, dy = text_center.x - court_center.x, text_center.y - court_center.y
    if dx == 0 and dy == 0:
        return CENTRED_REFERENCE_SIDE
    left, right, top, bottom = box_edges(courtyard)
    half_width = max((right - left) / 2.0, 1.0)
    half_height = max((bottom - top) / 2.0, 1.0)
    if abs(dx / half_width) > abs(dy / half_height):
        return "right" if dx > 0 else "left"
    return "bottom" if dy > 0 else "top"


def target_center(text_bounds, courtyard, side):
    """Move only the axis perpendicular to the selected courtyard side.

    A left/right placement changes X but preserves the reference's current Y.
    A top/bottom placement changes Y but preserves its current X.  Preserving
    the parallel axis avoids unexpectedly centering manually offset references.
    """
    left, right, top, bottom = box_edges(courtyard)
    text_left, text_right, text_top, text_bottom = box_edges(text_bounds)
    half_width = (text_right - text_left) // 2
    half_height = (text_bottom - text_top) // 2
    current = box_center(text_bounds)
    gap = from_mm(REFERENCE_OFFSET_MM)
    if side == "left":
        return vector(left - gap - half_width, current.y)
    if side == "right":
        return vector(right + gap + half_width, current.y)
    if side == "top":
        return vector(current.x, top - gap - half_height)
    if side == "bottom":
        return vector(current.x, bottom + gap + half_height)
    raise ValueError(f"invalid reference side: {side}")


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
        right < c_left - clearance or left > c_right + clearance or
        bottom < c_top - clearance or top > c_bottom + clearance
    )


def main():
    """Resize/align references and push one editor commit."""
    validate_resize_settings()
    client, board = connect_board()
    records = []
    for footprint in board.get_footprints():
        reference = footprint_reference(footprint)
        try:
            records.append((footprint, reference, courtyard_box(footprint)))
        except RuntimeError as error:
            print(f"Warning: {reference}: {error}; skipped")

    changed = []
    resized_count = 0
    aligned_count = 0
    clearance = from_mm(OTHER_COURTYARD_CLEARANCE_MM)
    with editor_commit(board, "Update component references"):
        for footprint, reference, courtyard in records:
            if reference in IGNORE_REFERENCES or not footprint.reference_field.visible:
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
                other_reference
                for other, other_reference, other_courtyard in records
                if other is not footprint and other.layer == same_board_side
                and intersects(proposed, other_courtyard, clearance)
            ]
            if collisions:
                print(
                    f"Warning: {reference}: would overlap "
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
                    f"{reference}: {side} at ({to_mm(destination.x):.3f}, "
                    f"{to_mm(destination.y):.3f}) mm"
                    f"{' (resized)' if resized else ''}"
                )
        board.update_items(changed)

    print(
        f"Resized {resized_count} and aligned {aligned_count} reference(s) "
        "(undo: Update component references)."
    )


if __name__ == "__main__":
    main()
