"""Validate or fix the active daughter-board mechanical interface via IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/check_motherboard_interface.py

Open the daughter board in PCB Editor before running this script. By default it
only validates the board outline and the J1, optional J2, H1, and H2 positions.
Set ``FIX_MOTHERBOARD_INTERFACE`` to ``True`` to replace a non-matching outline
and move the interface footprints in one undoable PCB Editor transaction.
Changes are left unsaved for review.
"""

import math

from kicad_ipc import (
    BoardLayer,
    board_document_path,
    board_edge_bounds,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    point_from_mm,
    to_mm,
)
from kipy.board_types import BoardArc, BoardSegment
from motherboard_interface import (
    DAUGHTER_BOARD_CORNER_RADIUS_MM,
    DAUGHTER_BOARD_HEIGHT_MM,
    DAUGHTER_BOARD_WIDTH_MM,
    EDGE_CUTS_LINE_WIDTH_MM,
    INTERFACE_TOLERANCE_MM,
    LEFT_HOLE_LEFT_MM,
    MOUNTING_HOLE_TOP_MM,
    OPTIONAL_CONNECTOR_LEFT_MM,
    OPTIONAL_CONNECTOR_TOP_MM,
    PRIMARY_CONNECTOR_LEFT_MM,
    PRIMARY_CONNECTOR_TOP_MM,
    RIGHT_HOLE_LEFT_MM,
)

# ============================================================
# User settings: shared motherboard interface
# ============================================================
# False validates without changing the active board. True repairs the active
# board and leaves the changes unsaved in PCB Editor for inspection.
FIX_MOTHERBOARD_INTERFACE = True

# Finished outline dimensions and construction shared by every daughter board.
# Dimensions are measured along the Edge.Cuts centreline.
BOARD_WIDTH_MM = DAUGHTER_BOARD_WIDTH_MM
BOARD_HEIGHT_MM = DAUGHTER_BOARD_HEIGHT_MM
CORNER_RADIUS_MM = DAUGHTER_BOARD_CORNER_RADIUS_MM
EDGE_LINE_WIDTH_MM = EDGE_CUTS_LINE_WIDTH_MM

# Interface offsets from the finished top and left edges, expressed as
# (reference, left offset, top offset). J1/J2 use the center of their top-left
# pins; H1/H2 use their hole centers. J2 is optional. The right offset is
# derived and also validated.
INTERFACE_FOOTPRINTS_MM = [
    ("J1", PRIMARY_CONNECTOR_LEFT_MM, PRIMARY_CONNECTOR_TOP_MM),
    ("J2", OPTIONAL_CONNECTOR_LEFT_MM, OPTIONAL_CONNECTOR_TOP_MM),
    ("H1", LEFT_HOLE_LEFT_MM, MOUNTING_HOLE_TOP_MM),
    ("H2", RIGHT_HOLE_LEFT_MM, MOUNTING_HOLE_TOP_MM),
]
OPTIONAL_REFERENCES = {"J2"}
PIN_DATUM_REFERENCES = {"J1", "J2"}
HOLE_REFERENCES = {"H1", "H2"}

# IPC dimensions are integral nanometres. This tolerance permits harmless
# serializer rounding while still catching a one-micron mechanical change.
TOLERANCE_MM = INTERFACE_TOLERANCE_MM


def close_mm(actual_nm, expected_mm):
    """Return whether an IPC dimension matches an expected millimetre value."""
    return abs(to_mm(actual_nm) - expected_mm) <= TOLERANCE_MM


def edge_items(board):
    """Return every active-board graphic on Edge.Cuts."""
    return [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]


def pad_vertical_center(footprint):
    """Return the vertical center of a footprint's pin and hole centers."""
    pads = list(footprint.definition.pads)
    if not pads:
        raise RuntimeError(
            f"footprint {footprint.reference_field.text.value} has no pads"
        )
    pad_y = [pad.position.y for pad in pads]
    return (min(pad_y) + max(pad_y)) // 2


def pad_horizontal_center(footprint):
    """Return the horizontal center of a footprint's pin and hole centers."""
    pads = list(footprint.definition.pads)
    if not pads:
        raise RuntimeError(
            f"footprint {footprint.reference_field.text.value} has no pads"
        )
    pad_x = [pad.position.x for pad in pads]
    return (min(pad_x) + max(pad_x)) // 2


def top_left_pin(footprint):
    """Return the pin nearest the footprint's top-left board position."""
    pads = list(footprint.definition.pads)
    if not pads:
        raise RuntimeError(
            f"footprint {footprint.reference_field.text.value} has no pads"
        )
    return min(pads, key=lambda pad: (pad.position.y, pad.position.x))


def horizontal_measurement(reference, footprint):
    """Return the configured horizontal datum for an interface footprint."""
    if reference in PIN_DATUM_REFERENCES:
        return top_left_pin(footprint).position.x
    if reference in HOLE_REFERENCES:
        return pad_horizontal_center(footprint)
    return footprint.position.x


def vertical_measurement(reference, footprint):
    """Return the configured vertical datum for an interface footprint."""
    if reference in PIN_DATUM_REFERENCES:
        return top_left_pin(footprint).position.y
    return pad_vertical_center(footprint)


def create_segment(start, end):
    """Create one configured Edge.Cuts line segment."""
    segment = BoardSegment()
    segment.layer = BoardLayer.BL_Edge_Cuts
    segment.start = start
    segment.end = end
    segment.attributes.stroke.width = from_mm(EDGE_LINE_WIDTH_MM)
    return segment


def create_arc(start, mid, end):
    """Create one configured Edge.Cuts arc from three points."""
    arc = BoardArc()
    arc.layer = BoardLayer.BL_Edge_Cuts
    arc.start = start
    arc.mid = mid
    arc.end = end
    arc.attributes.stroke.width = from_mm(EDGE_LINE_WIDTH_MM)
    return arc


def create_outline(left_mm, top_mm):
    """Create the configured rounded rectangle at the supplied top-left."""
    radius = CORNER_RADIUS_MM
    if radius < 0 or radius > min(BOARD_WIDTH_MM, BOARD_HEIGHT_MM) / 2:
        raise ValueError("CORNER_RADIUS_MM is invalid for the board dimensions")
    if BOARD_WIDTH_MM <= 0 or BOARD_HEIGHT_MM <= 0:
        raise ValueError("board dimensions must be positive")

    right_mm = left_mm + BOARD_WIDTH_MM
    bottom_mm = top_mm + BOARD_HEIGHT_MM
    if radius == 0:
        corners = [
            point_from_mm(left_mm, top_mm),
            point_from_mm(right_mm, top_mm),
            point_from_mm(right_mm, bottom_mm),
            point_from_mm(left_mm, bottom_mm),
        ]
        return [
            create_segment(corners[index], corners[(index + 1) % 4])
            for index in range(4)
        ]

    diagonal = radius / math.sqrt(2)
    top_left = point_from_mm(left_mm + radius, top_mm)
    top_right = point_from_mm(right_mm - radius, top_mm)
    right_top = point_from_mm(right_mm, top_mm + radius)
    right_bottom = point_from_mm(right_mm, bottom_mm - radius)
    bottom_right = point_from_mm(right_mm - radius, bottom_mm)
    bottom_left = point_from_mm(left_mm + radius, bottom_mm)
    left_bottom = point_from_mm(left_mm, bottom_mm - radius)
    left_top = point_from_mm(left_mm, top_mm + radius)
    return [
        create_segment(top_left, top_right),
        create_arc(
            top_right,
            point_from_mm(
                right_mm - radius + diagonal,
                top_mm + radius - diagonal,
            ),
            right_top,
        ),
        create_segment(right_top, right_bottom),
        create_arc(
            right_bottom,
            point_from_mm(
                right_mm - radius + diagonal,
                bottom_mm - radius + diagonal,
            ),
            bottom_right,
        ),
        create_segment(bottom_right, bottom_left),
        create_arc(
            bottom_left,
            point_from_mm(
                left_mm + radius - diagonal,
                bottom_mm - radius + diagonal,
            ),
            left_bottom,
        ),
        create_segment(left_bottom, left_top),
        create_arc(
            left_top,
            point_from_mm(
                left_mm + radius - diagonal,
                top_mm + radius - diagonal,
            ),
            top_left,
        ),
    ]


def collect_problems(board):
    """Return validation problems and the geometry needed to repair them."""
    edges = board_edge_bounds(board)
    left, right, top, bottom = edges
    width = right - left
    height = bottom - top
    footprints = footprints_by_reference(board)
    problems = []

    if not close_mm(width, BOARD_WIDTH_MM):
        problems.append(
            f"outline width is {to_mm(width):.3f} mm; required {BOARD_WIDTH_MM:.3f} mm"
        )
    if not close_mm(height, BOARD_HEIGHT_MM):
        problems.append(
            f"outline height is {to_mm(height):.3f} mm; "
            f"required {BOARD_HEIGHT_MM:.3f} mm"
        )

    for reference, left_mm, top_mm in INTERFACE_FOOTPRINTS_MM:
        footprint = footprints.get(reference)
        if footprint is None:
            if reference in OPTIONAL_REFERENCES:
                continue
            problems.append(f"required footprint {reference} is missing")
            continue
        horizontal = horizontal_measurement(reference, footprint)
        offsets = {
            "left": horizontal - left,
            "right": right - horizontal,
            "top": vertical_measurement(reference, footprint) - top,
        }
        expected = {
            "left": left_mm,
            "right": BOARD_WIDTH_MM - left_mm,
            "top": top_mm,
        }
        for edge_name, actual_nm in offsets.items():
            if not close_mm(actual_nm, expected[edge_name]):
                problems.append(
                    f"{reference} {edge_name} offset is "
                    f"{to_mm(actual_nm):.3f} mm; required "
                    f"{expected[edge_name]:.3f} mm"
                )
        if reference in PIN_DATUM_REFERENCES:
            connector_center = pad_horizontal_center(footprint)
            board_center = (left + right) // 2
            if not close_mm(connector_center - board_center, 0.0):
                problems.append(
                    f"{reference} pin group is horizontally off-center by "
                    f"{to_mm(connector_center - board_center):+.3f} mm"
                )
    return problems, edges, footprints


def print_interface(board):
    """Print the active board's dimensions and interface footprint offsets."""
    left, right, top, bottom = board_edge_bounds(board)
    footprints = footprints_by_reference(board)
    print(f"Active PCB: {board_document_path(board.document)}")
    print(f"Outline: {to_mm(right - left):.3f} x {to_mm(bottom - top):.3f} mm")
    for reference, _left_mm, _top_mm in INTERFACE_FOOTPRINTS_MM:
        footprint = footprints.get(reference)
        if footprint is None:
            if reference in OPTIONAL_REFERENCES:
                print(f"No {reference} found (optional).")
            else:
                print(f"{reference}: missing")
            continue
        horizontal = horizontal_measurement(reference, footprint)
        vertical = vertical_measurement(reference, footprint)
        measurement_label = (
            "hole center" if reference in HOLE_REFERENCES else "top-left pin center"
        )
        print(
            f"{reference}: left "
            f"{to_mm(horizontal - left):.3f} mm, right "
            f"{to_mm(right - horizontal):.3f} mm, top "
            f"{to_mm(vertical - top):.3f} mm ({measurement_label})"
        )
        if reference in PIN_DATUM_REFERENCES:
            center_offset = pad_horizontal_center(footprint) - (left + right) // 2
            status = "PASS" if close_mm(center_offset, 0.0) else "FAIL"
            print(
                f"  Horizontal pin-group centering: {status} "
                f"(offset {to_mm(center_offset):+.3f} mm)"
            )


def main():
    """Validate or repair the active PCB's motherboard interface."""
    _client, board = connect_board()
    try:
        problems, edges, footprints = collect_problems(board)
    except RuntimeError as error:
        raise SystemExit(f"Cannot validate motherboard interface: {error}") from None

    print_interface(board)
    if not problems:
        print("PASS: active PCB matches the motherboard mechanical interface.")
        return

    print("FAIL: active PCB does not match the motherboard interface:")
    for problem in problems:
        print(f"  - {problem}")
    if not FIX_MOTHERBOARD_INTERFACE:
        raise SystemExit(
            "Validation failed. Set FIX_MOTHERBOARD_INTERFACE = True to repair "
            "the active PCB."
        )

    missing = [
        reference
        for reference, _left_mm, _top_mm in INTERFACE_FOOTPRINTS_MM
        if reference not in footprints and reference not in OPTIONAL_REFERENCES
    ]
    if missing:
        raise SystemExit(
            "Cannot fix the interface because required footprint(s) are "
            f"missing: {', '.join(missing)}."
        )

    left, right, top, bottom = edges
    outline_wrong = not close_mm(right - left, BOARD_WIDTH_MM) or not close_mm(
        bottom - top, BOARD_HEIGHT_MM
    )
    existing_edges = edge_items(board)
    replacement_edges = create_outline(to_mm(left), to_mm(top)) if outline_wrong else []
    changed_footprints = []
    for reference, left_mm, top_mm in INTERFACE_FOOTPRINTS_MM:
        footprint = footprints.get(reference)
        if footprint is None:
            continue
        horizontal = horizontal_measurement(reference, footprint)
        vertical = vertical_measurement(reference, footprint)
        target = point_from_mm(
            to_mm(footprint.position.x + from_mm(left_mm) - (horizontal - left)),
            to_mm(footprint.position.y + from_mm(top_mm) - (vertical - top)),
        )
        if footprint.position != target:
            footprint.position = target
            changed_footprints.append(footprint)

    with editor_commit(
        board,
        "Fix motherboard mechanical interface",
        refill_zones=outline_wrong,
    ):
        if outline_wrong:
            board.remove_items(existing_edges)
            board.create_items(replacement_edges)
        if changed_footprints:
            board.update_items(changed_footprints)

    remaining, _edges, _footprints = collect_problems(board)
    if remaining:
        raise RuntimeError(
            "motherboard interface still fails after repair:\n  - "
            + "\n  - ".join(remaining)
        )
    print(
        f"Fixed the outline and/or {len(changed_footprints)} interface "
        "footprint(s) (undo: Fix motherboard mechanical interface)."
    )
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
