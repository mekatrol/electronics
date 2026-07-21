#!/usr/bin/env python3
"""Align visible footprint references outside courtyards using KiCad IPC.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/align_component_reference_text.py``.
All moved references form one PCB Editor undo/redo transaction.  The board is
left unsaved so the editor remains the authority for Undo, Redo, and Save.
"""

from kicad_ipc import (
    box_center, box_edges, connect_board, courtyard_box,
    editor_commit, footprint_reference, from_mm, move_text_center, text_box,
    to_mm, vector,
)


IGNORE_REFERENCES = []
REFERENCE_OFFSET_MM = 0.0
OTHER_COURTYARD_CLEARANCE_MM = 0.1
CENTRED_REFERENCE_SIDE = "top"
DEBUG = True


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
    """Align references and push the successful batch as one editor commit."""
    client, board = connect_board()
    records = []
    for footprint in board.get_footprints():
        reference = footprint_reference(footprint)
        try:
            records.append((footprint, reference, courtyard_box(footprint)))
        except RuntimeError as error:
            print(f"Warning: {reference}: {error}; skipped")

    changed = []
    clearance = from_mm(OTHER_COURTYARD_CLEARANCE_MM)
    with editor_commit(board, "Align component references"):
        for footprint, reference, courtyard in records:
            if reference in IGNORE_REFERENCES or not footprint.reference_field.visible:
                continue
            text = footprint.reference_field.text
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
                print(f"Warning: {reference}: would overlap {', '.join(collisions)}; skipped")
                continue
            move_text_center(client, text, destination)
            footprint.reference_field.text = text
            changed.append(footprint)
            if DEBUG:
                print(
                    f"{reference}: {side} at ({to_mm(destination.x):.3f}, "
                    f"{to_mm(destination.y):.3f}) mm"
                )
        board.update_items(changed)

    print(f"Aligned {len(changed)} reference(s) (undo: Align component references).")


if __name__ == "__main__":
    main()
