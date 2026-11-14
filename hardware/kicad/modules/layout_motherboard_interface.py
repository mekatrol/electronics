"""Lay out the active motherboard's daughter-board interfaces via IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/layout_motherboard_interface.py

Open the motherboard in PCB Editor before running this script.  It arranges
the configured connector and mounting-hole references as eight daughter-board
slots, separated by the configured clearance and centred across the
motherboard's bottom edge.  Every slot represents a daughter board with its
bottom edge aligned to the motherboard's bottom edge; the connector pins and
hole centres consequently land at exactly the offsets checked by
``check_motherboard_interface.py``.

All rotations and moves form one PCB Editor Undo/Redo entry.  Changes are left
unsaved so the complete result can be inspected before saving manually.
"""

from kicad_ipc import (
    board_document_path,
    board_edge_bounds,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    to_mm,
    vector,
)
from kipy.geometry import Angle
from motherboard_interface import (
    DAUGHTER_BOARD_HEIGHT_MM,
    DAUGHTER_BOARD_WIDTH_MM,
    LEFT_HOLE_LEFT_MM,
    MOUNTING_HOLE_TOP_MM,
    PRIMARY_CONNECTOR_LEFT_MM,
    PRIMARY_CONNECTOR_TOP_MM,
    RIGHT_HOLE_LEFT_MM,
)

# ============================================================
# User settings: motherboard schematic references
# ============================================================
# References are deliberately explicit and ordered left-to-right.  Change
# these tuples here if a future schematic annotation assigns different names;
# the placement code below never guesses relationships from reference numbers.
CONNECTOR_REFERENCES = ("J4", "J5", "J6", "J7", "J8", "J9", "J10", "J11")
LEFT_HOLE_REFERENCES = ("H5", "H7", "H9", "H11", "H13", "H15", "H17", "H19")
RIGHT_HOLE_REFERENCES = ("H6", "H8", "H10", "H12", "H14", "H16", "H18", "H20")

# Clear space between adjacent daughter-board Edge.Cuts.  This is added only
# between slots, not outside the first and last boards.  A 2 mm gap keeps the
# board outlines apart and leaves additional space around mounting hardware.
DAUGHTER_BOARD_GAP_MM = 3.0

# J1 on each daughter board is a horizontal four-pin row, represented by a
# footprint rotation of +90 degrees in KiCad.  Applying the same rotation to
# the motherboard socket makes like-numbered pads occupy the same coordinates.
CONNECTOR_ROTATION_DEGREES = 90.0


def footprint_pads(footprint):
    """Return the live, board-coordinate pads belonging to a footprint."""
    definition = getattr(footprint, "definition", footprint)
    pads = list(definition.pads)
    if not pads:
        reference = footprint.reference_field.text.value
        raise RuntimeError(f"footprint {reference} has no pads")
    return pads


def top_left_pin_position(footprint):
    """Return the position of the pin nearest the footprint's top-left."""
    pin = min(
        footprint_pads(footprint),
        key=lambda pad: (pad.position.y, pad.position.x),
    )
    return pin.position


def pad_center(footprint):
    """Return the centre of all pad centres, used as a mounting-hole datum."""
    pads = footprint_pads(footprint)
    return vector(
        (min(pad.position.x for pad in pads) + max(pad.position.x for pad in pads))
        // 2,
        (min(pad.position.y for pad in pads) + max(pad.position.y for pad in pads))
        // 2,
    )


def translate_datum_to(footprint, datum, target):
    """Translate a footprint so its measured datum reaches ``target``."""
    footprint.position = vector(
        footprint.position.x + target.x - datum.x,
        footprint.position.y + target.y - datum.y,
    )


def validate_reference_settings():
    """Reject incomplete or ambiguous slot mappings before opening a commit."""
    if DAUGHTER_BOARD_GAP_MM < 0:
        raise ValueError("DAUGHTER_BOARD_GAP_MM must not be negative")
    counts = {
        len(CONNECTOR_REFERENCES),
        len(LEFT_HOLE_REFERENCES),
        len(RIGHT_HOLE_REFERENCES),
    }
    if len(counts) != 1 or not CONNECTOR_REFERENCES:
        raise ValueError(
            "connector, left-hole, and right-hole reference tuples must have "
            "the same non-zero length"
        )
    references = (
        *CONNECTOR_REFERENCES,
        *LEFT_HOLE_REFERENCES,
        *RIGHT_HOLE_REFERENCES,
    )
    if any(not reference.strip() for reference in references):
        raise ValueError("interface references must not be blank")
    if len(set(references)) != len(references):
        raise ValueError("every interface reference must be unique")


def main():
    """Arrange every configured motherboard interface in one transaction."""
    validate_reference_settings()
    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    references = (
        *CONNECTOR_REFERENCES,
        *LEFT_HOLE_REFERENCES,
        *RIGHT_HOLE_REFERENCES,
    )
    missing = [reference for reference in references if reference not in footprints]
    if missing:
        raise SystemExit(
            "Cannot lay out the motherboard interface because footprint(s) "
            f"are missing: {', '.join(missing)}."
        )

    left, right, _top, bottom = board_edge_bounds(board)
    slot_count = len(CONNECTOR_REFERENCES)
    slot_pitch_mm = DAUGHTER_BOARD_WIDTH_MM + DAUGHTER_BOARD_GAP_MM
    row_width_mm = (
        slot_count * DAUGHTER_BOARD_WIDTH_MM + (slot_count - 1) * DAUGHTER_BOARD_GAP_MM
    )
    row_width = from_mm(row_width_mm)

    # The row is centred even when its configured width exceeds the current
    # motherboard.  This keeps all slots deterministic and makes an undersized
    # outline immediately visible rather than silently compressing the pitch
    # and violating the daughter-board envelope.
    row_left = (left + right - row_width) // 2
    daughter_top = bottom - from_mm(DAUGHTER_BOARD_HEIGHT_MM)
    changed = []
    action = "Lay out motherboard daughter-board interfaces"

    with editor_commit(board, action, refill_zones=True):
        for slot_index, references_for_slot in enumerate(
            zip(
                CONNECTOR_REFERENCES,
                LEFT_HOLE_REFERENCES,
                RIGHT_HOLE_REFERENCES,
                strict=True,
            )
        ):
            connector_reference, left_hole_reference, right_hole_reference = (
                references_for_slot
            )
            slot_left = row_left + from_mm(slot_index * slot_pitch_mm)

            connector = footprints[connector_reference]
            connector.orientation = Angle.from_degrees(CONNECTOR_ROTATION_DEGREES)
            connector_target = vector(
                slot_left + from_mm(PRIMARY_CONNECTOR_LEFT_MM),
                daughter_top + from_mm(PRIMARY_CONNECTOR_TOP_MM),
            )
            translate_datum_to(
                connector,
                top_left_pin_position(connector),
                connector_target,
            )

            left_hole = footprints[left_hole_reference]
            left_hole_target = vector(
                slot_left + from_mm(LEFT_HOLE_LEFT_MM),
                daughter_top + from_mm(MOUNTING_HOLE_TOP_MM),
            )
            translate_datum_to(left_hole, pad_center(left_hole), left_hole_target)

            right_hole = footprints[right_hole_reference]
            right_hole_target = vector(
                slot_left + from_mm(RIGHT_HOLE_LEFT_MM),
                daughter_top + from_mm(MOUNTING_HOLE_TOP_MM),
            )
            translate_datum_to(right_hole, pad_center(right_hole), right_hole_target)
            changed.extend((connector, left_hole, right_hole))

            print(
                f"Slot {slot_index + 1}: {connector_reference}, "
                f"{left_hole_reference}, {right_hole_reference}; envelope left "
                f"{to_mm(slot_left):.3f} mm"
            )

        board.update_items(changed)

    board_width = right - left
    print(f"Active PCB: {board_document_path(board.document)}")
    print(
        f"Laid out {slot_count} interfaces in a {to_mm(row_width):.3f} mm row "
        f"with {DAUGHTER_BOARD_GAP_MM:.3f} mm gaps, centred on the "
        f"{to_mm(board_width):.3f} mm motherboard "
        f"(undo: {action})."
    )
    if row_width > board_width:
        print(
            "WARNING: the interface row is wider than the current motherboard "
            "outline; enlarge the board or reduce the configured slot count."
        )
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
