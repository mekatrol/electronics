"""Lay out the active motherboard's daughter-board interfaces via IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/layout_motherboard_interface.py

Open the motherboard in PCB Editor before running this script.  The default
layout places four daughter boards down the left edge and four down the right
edge, rotated toward the board interior.  The optional bottom layout retains
the original single horizontal row.  In either mode, adjacent daughter-board
outlines use the configured clearance and the complete group is centred on
the applicable motherboard edge.

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
    INTERFACE_TOLERANCE_MM,
    LEFT_HOLE_LEFT_MM,
    MOUNTING_HOLE_TOP_MM,
    PRIMARY_CONNECTOR_TOP_MM,
    RIGHT_HOLE_LEFT_MM,
)

# ============================================================
# User settings: motherboard schematic references
# ============================================================
# References are deliberately explicit.  In bottom mode they are ordered
# left-to-right.  In left-right mode the first half is ordered top-to-bottom on
# the left edge and the second half top-to-bottom on the right edge.  Change
# these tuples here if a future schematic annotation assigns different names;
# the placement code below never guesses relationships from reference numbers.
CONNECTOR_REFERENCES = ("J4", "J5", "J6", "J7", "J8", "J9", "J10", "J11")
LEFT_HOLE_REFERENCES = ("H5", "H7", "H9", "H11", "H13", "H15", "H17", "H19")
RIGHT_HOLE_REFERENCES = ("H6", "H8", "H10", "H12", "H14", "H16", "H18", "H20")

# Select ``"left-right"`` for equal groups on the two vertical edges, or
# ``"bottom"`` for one horizontal row along the bottom edge.
LAYOUT_MODE = "left-right"

# Clear space between adjacent daughter-board Edge.Cuts.  This is added only
# between slots, not outside the first and last boards.  The gap keeps board
# outlines apart and leaves additional space around mounting hardware.
DAUGHTER_BOARD_GAP_MM = 3.0

# J1 on each daughter board is a horizontal four-pin row, represented by a
# footprint rotation of +90 degrees in KiCad.
CONNECTOR_ROTATION_DEGREES = 90.0

# The daughter header is fitted on the bottom of the daughter board and mates
# face-to-face with the motherboard socket.  The mating view reverses the pin
# row, so the motherboard connector requires this additional half turn to put
# each supply and signal pin over its electrically corresponding daughter pin.
MOTHERBOARD_CONNECTOR_FLIP_DEGREES = 180.0


def footprint_pads(footprint):
    """Return the live, board-coordinate pads belonging to a footprint."""
    definition = getattr(footprint, "definition", footprint)
    pads = list(definition.pads)
    if not pads:
        reference = footprint.reference_field.text.value
        raise RuntimeError(f"footprint {reference} has no pads")
    return pads


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
    if LAYOUT_MODE not in {"bottom", "left-right"}:
        raise ValueError('LAYOUT_MODE must be "bottom" or "left-right"')
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
    if LAYOUT_MODE == "left-right" and len(CONNECTOR_REFERENCES) % 2:
        raise ValueError("left-right layout requires an even number of interfaces")


def transformed_point(edge, anchor_x, anchor_y, local_x_mm, local_y_mm):
    """Map one daughter-board-local point into the selected edge slot.

    ``anchor_x`` and ``anchor_y`` identify the motherboard-edge end of the
    slot.  KiCad's Y axis increases downward, so the formulas explicitly
    encode the screen-clockwise left-edge and screen-counter-clockwise
    right-edge rotations.  KiCad footprint angles use the opposite signs for
    those visual rotations; the caller accounts for that when rotating the
    connector footprint.
    """
    local_x = from_mm(local_x_mm)
    local_y = from_mm(local_y_mm)
    if edge == "bottom":
        return vector(anchor_x + local_x, anchor_y + local_y)
    if edge == "left":
        return vector(
            anchor_x + from_mm(DAUGHTER_BOARD_HEIGHT_MM) - local_y,
            anchor_y + local_x,
        )
    if edge == "right":
        return vector(
            anchor_x - from_mm(DAUGHTER_BOARD_HEIGHT_MM) + local_y,
            anchor_y + from_mm(DAUGHTER_BOARD_WIDTH_MM) - local_x,
        )
    raise ValueError(f"unsupported motherboard edge: {edge}")


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

    left, right, top, bottom = board_edge_bounds(board)
    slot_count = len(CONNECTOR_REFERENCES)
    slot_pitch_mm = DAUGHTER_BOARD_WIDTH_MM + DAUGHTER_BOARD_GAP_MM
    slots_per_edge = slot_count if LAYOUT_MODE == "bottom" else slot_count // 2
    layout_span_mm = (
        slots_per_edge * DAUGHTER_BOARD_WIDTH_MM
        + (slots_per_edge - 1) * DAUGHTER_BOARD_GAP_MM
    )
    layout_span = from_mm(layout_span_mm)

    # Each group is centred even when its span exceeds the applicable current
    # motherboard dimension.  This keeps every slot deterministic and makes an
    # undersized outline visible instead of silently violating the configured
    # daughter-board pitch.
    bottom_row_left = (left + right - layout_span) // 2
    bottom_daughter_top = bottom - from_mm(DAUGHTER_BOARD_HEIGHT_MM)
    side_row_top = (top + bottom - layout_span) // 2
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
            if LAYOUT_MODE == "bottom":
                edge = "bottom"
                edge_slot_index = slot_index
                anchor_x = bottom_row_left + from_mm(edge_slot_index * slot_pitch_mm)
                anchor_y = bottom_daughter_top
                board_rotation_degrees = 0.0
            elif slot_index < slots_per_edge:
                edge = "left"
                edge_slot_index = slot_index
                anchor_x = left
                anchor_y = side_row_top + from_mm(edge_slot_index * slot_pitch_mm)
                board_rotation_degrees = -90.0
            else:
                edge = "right"
                edge_slot_index = slot_index - slots_per_edge
                anchor_x = right
                anchor_y = side_row_top + from_mm(edge_slot_index * slot_pitch_mm)
                board_rotation_degrees = 90.0

            connector = footprints[connector_reference]
            connector.orientation = Angle.from_degrees(
                CONNECTOR_ROTATION_DEGREES
                + board_rotation_degrees
                + MOTHERBOARD_CONNECTOR_FLIP_DEGREES
            )

            # Position the socket by the centre of its complete pin row.  The
            # shared connector pin group is horizontally centred on the
            # daughter board.  A centre datum is invariant under the required
            # 180-degree mating flip.
            connector_target = transformed_point(
                edge,
                anchor_x,
                anchor_y,
                DAUGHTER_BOARD_WIDTH_MM / 2,
                PRIMARY_CONNECTOR_TOP_MM,
            )
            translate_datum_to(
                connector,
                pad_center(connector),
                connector_target,
            )

            left_hole = footprints[left_hole_reference]
            left_hole_target = transformed_point(
                edge,
                anchor_x,
                anchor_y,
                LEFT_HOLE_LEFT_MM,
                MOUNTING_HOLE_TOP_MM,
            )
            translate_datum_to(left_hole, pad_center(left_hole), left_hole_target)

            right_hole = footprints[right_hole_reference]
            right_hole_target = transformed_point(
                edge,
                anchor_x,
                anchor_y,
                RIGHT_HOLE_LEFT_MM,
                MOUNTING_HOLE_TOP_MM,
            )
            translate_datum_to(right_hole, pad_center(right_hole), right_hole_target)

            # The centre of the four connector pins must remain on the line
            # halfway between the two holes.  Bottom slots share X; rotated
            # side slots share Y.  Check this invariant before sending any
            # items to KiCad so a footprint numbering or rotation change can
            # never silently reproduce a mechanically shifted connector.
            connector_center = pad_center(connector)
            hole_midpoint = vector(
                (left_hole_target.x + right_hole_target.x) // 2,
                (left_hole_target.y + right_hole_target.y) // 2,
            )
            alignment_error = (
                connector_center.x - hole_midpoint.x
                if edge == "bottom"
                else connector_center.y - hole_midpoint.y
            )
            if abs(alignment_error) > from_mm(INTERFACE_TOLERANCE_MM):
                raise RuntimeError(
                    f"{connector_reference} is not centred between "
                    f"{left_hole_reference} and {right_hole_reference}; "
                    f"alignment error {to_mm(alignment_error):+.3f} mm"
                )
            changed.extend((connector, left_hole, right_hole))

            print(
                f"Slot {slot_index + 1}: {connector_reference}, "
                f"{left_hole_reference}, {right_hole_reference}; {edge} edge, "
                f"edge slot {edge_slot_index + 1}, rotation "
                f"{board_rotation_degrees:+.0f} degrees"
            )

        board.update_items(changed)

    board_dimension = right - left if LAYOUT_MODE == "bottom" else bottom - top
    dimension_name = "width" if LAYOUT_MODE == "bottom" else "height"
    print(f"Active PCB: {board_document_path(board.document)}")
    print(
        f"Laid out {slot_count} interfaces in {LAYOUT_MODE} mode; each edge "
        f"group spans {to_mm(layout_span):.3f} mm with "
        f"{DAUGHTER_BOARD_GAP_MM:.3f} mm gaps, centred on the motherboard's "
        f"{to_mm(board_dimension):.3f} mm {dimension_name} "
        f"(undo: {action})."
    )
    if layout_span > board_dimension:
        print(
            "WARNING: an interface group is longer than the applicable "
            "motherboard edge; enlarge the board or reduce the slot count."
        )
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
