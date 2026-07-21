#!/usr/bin/env python3
"""Report board, mounting-hole and fiducial dimensions through IPC.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/report_board_dimensions.py``.
This script is read-only and therefore creates no undo entry.
"""

from kicad_ipc import board_edge_bounds, connect_board, footprints_by_reference, to_mm


HOLE_REFERENCE_PREFIX = "H"
FIDUCIAL_REFERENCE_PREFIX = "FID"
DECIMAL_PLACES = 3


def consecutive_footprints(footprints, prefix):
    """Return PREFIX1, PREFIX2, ... until the first missing reference."""
    found = []
    number = 1
    while f"{prefix}{number}" in footprints:
        reference = f"{prefix}{number}"
        found.append((reference, footprints[reference]))
        number += 1
    return found


def format_mm(value):
    """Format a nanometre measurement consistently for the report."""
    return f"{to_mm(value):.{DECIMAL_PLACES}f} mm"


def report_offsets(title, items, edges):
    """Print offsets from each footprint anchor to its nearest two edges."""
    left, right, top, bottom = edges
    print(f"\n{title}")
    if not items:
        print("  None found.")
    for reference, footprint in items:
        position = footprint.position
        horizontal = min(("left", position.x-left), ("right", right-position.x), key=lambda x: x[1])
        vertical = min(("top", position.y-top), ("bottom", bottom-position.y), key=lambda x: x[1])
        print(
            f"  {reference}: {horizontal[0]} {format_mm(horizontal[1])}, "
            f"{vertical[0]} {format_mm(vertical[1])}"
        )


def main():
    """Read the open board and print its mechanical-dimension report."""
    _client, board = connect_board()
    # IPC shape bounding boxes describe the geometric Edge.Cuts centreline and
    # do not add the visible stroke width, so no line-width compensation is
    # required (unlike the legacy SWIG GetBoardEdgesBoundingBox result).
    edges = board_edge_bounds(board)
    footprints = footprints_by_reference(board)
    holes = consecutive_footprints(footprints, HOLE_REFERENCE_PREFIX)
    fiducials = consecutive_footprints(footprints, FIDUCIAL_REFERENCE_PREFIX)

    print("Board dimensions")
    print(f"  Width : {format_mm(edges[1] - edges[0])}")
    print(f"  Height: {format_mm(edges[3] - edges[2])}")
    report_offsets("Mounting holes", holes, edges)
    print("\nHole-to-hole spacing")
    for index, (first_ref, first) in enumerate(holes[:-1]):
        for second_ref, second in holes[index + 1:]:
            print(
                f"  {first_ref} to {second_ref}: X "
                f"{format_mm(abs(second.position.x-first.position.x))}, "
                f"Y {format_mm(abs(second.position.y-first.position.y))}"
            )
    report_offsets("Fiducials", fiducials, edges)


if __name__ == "__main__":
    main()
