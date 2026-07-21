"""Report board dimensions and mounting-hole/fiducial offsets.

Execution:
    Open a board in KiCad's PCB Editor, adjust the settings below, then run
    this file from the PCB Editor scripting console with::

        exec(open("/home/dad/repos/electronics/hardware/kicad/modules/report_board_dimensions.py").read())

This script only reads the board and prints its report to the console.
"""

import pcbnew


# ============================================================
# Report settings
# ============================================================
# References are checked consecutively from 1. The first missing reference
# ends that group, so references should not contain gaps (for example, H1,
# H2, H3 and FID1, FID2).
HOLE_REFERENCE_PREFIX = "H"
FIDUCIAL_REFERENCE_PREFIX = "FID"
DECIMAL_PLACES = 3

# GetBoardEdgesBoundingBox() includes the visible Edge.Cuts stroke. This must
# match the line width used to create the outline so the report measures from
# the fabrication centreline rather than from the outside of the drawn line.
EDGE_CUT_LINE_WIDTH_MM = 0.10


def iu_to_mm(value_iu):
    """Convert KiCad internal units to millimetres."""
    return pcbnew.ToMM(value_iu)


def get_board_edges(board):
    """Return the Edge.Cuts centreline boundaries in KiCad units."""
    bbox = board.GetBoardEdgesBoundingBox()

    if bbox.GetWidth() <= 0 or bbox.GetHeight() <= 0:
        raise RuntimeError("The board needs a valid Edge.Cuts outline.")

    half_line_width = pcbnew.FromMM(EDGE_CUT_LINE_WIDTH_MM / 2.0)

    return (
        bbox.GetLeft() + half_line_width,
        bbox.GetRight() - half_line_width,
        bbox.GetTop() + half_line_width,
        bbox.GetBottom() - half_line_width,
    )


def find_consecutive_footprints(board, reference_prefix):
    """Find PREFIX1, PREFIX2, ... until the first reference not present."""
    footprints = []
    number = 1

    while True:
        reference = f"{reference_prefix}{number}"
        footprint = board.FindFootprintByReference(reference)

        if footprint is None:
            break

        footprints.append((reference, footprint))
        number += 1

    return footprints


def nearest_edge_distances(position, left_x, right_x, top_y, bottom_y):
    """
    Return the nearest vertical and horizontal board edges and distances.

    KiCad's Y coordinate increases downwards, hence top is subtracted from
    the footprint Y while the footprint Y is subtracted from bottom.
    """
    horizontal_distances = (
        ("left", position.x - left_x),
        ("right", right_x - position.x),
    )
    vertical_distances = (
        ("top", position.y - top_y),
        ("bottom", bottom_y - position.y),
    )

    nearest_horizontal = min(horizontal_distances, key=lambda item: item[1])
    nearest_vertical = min(vertical_distances, key=lambda item: item[1])
    return nearest_horizontal, nearest_vertical


def format_mm(value_iu):
    return f"{iu_to_mm(value_iu):.{DECIMAL_PLACES}f} mm"


def report_footprint_group(
    title,
    footprints,
    left_x,
    right_x,
    top_y,
    bottom_y,
):
    """Print each footprint's offsets from its two nearest board edges."""
    print()
    print(title)

    if not footprints:
        print("  None found.")
        return

    for reference, footprint in footprints:
        position = footprint.GetPosition()
        horizontal, vertical = nearest_edge_distances(
            position,
            left_x,
            right_x,
            top_y,
            bottom_y,
        )
        horizontal_name, horizontal_distance = horizontal
        vertical_name, vertical_distance = vertical

        print(f"  {reference}")
        print(f"    {horizontal_name:<6}: {format_mm(horizontal_distance)}")
        print(f"    {vertical_name:<6}: {format_mm(vertical_distance)}")


def report_hole_spacing(holes):
    """
    Print X and Y separation for every unique pair of mounting holes.

    These are axis-aligned measurements, not the diagonal distance between
    hole centres. Absolute values keep the result independent of reference
    order and board orientation.
    """
    print()
    print("Hole-to-hole spacing")

    if len(holes) < 2:
        print("  Need at least two holes.")
        return

    for first_index in range(len(holes) - 1):
        first_reference, first_footprint = holes[first_index]
        first_position = first_footprint.GetPosition()

        for second_reference, second_footprint in holes[first_index + 1 :]:
            second_position = second_footprint.GetPosition()
            horizontal_distance = abs(second_position.x - first_position.x)
            vertical_distance = abs(second_position.y - first_position.y)

            print(f"  {first_reference} to {second_reference}")
            print(f"    horizontal: {format_mm(horizontal_distance)}")
            print(f"    vertical  : {format_mm(vertical_distance)}")


def report_board(board):
    left_x, right_x, top_y, bottom_y = get_board_edges(board)
    width = right_x - left_x
    height = bottom_y - top_y

    print("Board dimensions")
    print(f"  width : {format_mm(width)}")
    print(f"  height: {format_mm(height)}")

    holes = find_consecutive_footprints(board, HOLE_REFERENCE_PREFIX)
    fiducials = find_consecutive_footprints(board, FIDUCIAL_REFERENCE_PREFIX)

    report_footprint_group(
        "Mounting holes",
        holes,
        left_x,
        right_x,
        top_y,
        bottom_y,
    )
    report_hole_spacing(holes)
    report_footprint_group(
        "Fiducials",
        fiducials,
        left_x,
        right_x,
        top_y,
        bottom_y,
    )


board = pcbnew.GetBoard()

if board is None:
    print("Error: no board is currently open.")
else:
    try:
        report_board(board)
    except Exception as error:
        print(f"Error: {error}")
