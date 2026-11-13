"""Centre one footprint between Edge.Cuts at its current cross-section.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/align_component_edge_center.py

For horizontal alignment, the footprint moves along X to the midpoint of the
two board-edge crossings at its current Y centre.  Vertical alignment uses the
two crossings at its current X centre and moves along Y.  The move is grouped
into one PCB Editor undo/redo transaction.  Save manually after review.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from kicad_ipc import (
    BoardLayer,
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    to_mm,
    vector,
)
from kicad_utils import edge_contours


@dataclass(frozen=True)
class ModuleOptions:
    """Validated settings for centring one footprint between board edges.

    ``reference`` is the exact PCB footprint reference, ``alignment`` selects
    the coordinate to move, and ``include_text`` controls whether reference and
    value text contribute to the footprint centre. Instances do not access or
    modify KiCad until passed to :func:`run`.
    """

    reference: str
    alignment: str = "horizontal"
    include_text: bool = False


def scanline_crossings(contours, fixed_coordinate, alignment):
    """Return outline crossings on a horizontal or vertical scanline.

    A half-open endpoint rule counts a contour vertex only once.  Segments
    lying along the scanline do not represent a discrete board-edge crossing
    and are ignored.
    """
    crossings = []
    horizontal = alignment == "horizontal"
    for contour in contours:
        for first, second in zip(contour, contour[1:], strict=False):
            first_fixed = first.y if horizontal else first.x
            second_fixed = second.y if horizontal else second.x
            if first_fixed == second_fixed:
                continue
            if not (
                first_fixed <= fixed_coordinate < second_fixed
                or second_fixed <= fixed_coordinate < first_fixed
            ):
                continue
            first_moving = first.x if horizontal else first.y
            second_moving = second.x if horizontal else second.y
            fraction = (fixed_coordinate - first_fixed) / (second_fixed - first_fixed)
            crossings.append(
                round(first_moving + fraction * (second_moving - first_moving))
            )
    return sorted(set(crossings))


def bracketing_edges(crossings, component_coordinate):
    """Return the nearest scanline crossings on either side of a component."""
    before = [value for value in crossings if value <= component_coordinate]
    after = [value for value in crossings if value >= component_coordinate]
    if not before or not after:
        raise RuntimeError(
            "component centre is not bracketed by two Edge.Cuts crossings"
        )
    first, second = max(before), min(after)
    if first == second:
        raise RuntimeError("component centre lies on Edge.Cuts")
    return first, second


def run(options: ModuleOptions) -> int:
    """Centre one footprint in its local board cross-section.

    Args:
        options: Validated footprint reference, alignment, and bounds settings.

    Returns:
        Zero after either a successful move or an already-centred result.

    Raises:
        ValueError: If the reference is blank or the alignment is unsupported.
        RuntimeError: If KiCad, the footprint, its bounds, or suitable board
            edges are unavailable.

    Side Effects:
        Connects to PCB Editor and may publish one undoable footprint move.
    """
    if not options.reference.strip():
        raise ValueError("reference must not be blank")
    if options.alignment not in {"horizontal", "vertical"}:
        raise ValueError('alignment must be "horizontal" or "vertical"')

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    if options.reference not in footprints:
        raise RuntimeError(f"missing footprint: {options.reference}")
    footprint = footprints[options.reference]

    bounding_box = board.get_item_bounding_box(
        footprint,
        include_text=options.include_text,
    )
    if bounding_box is None:
        raise RuntimeError(f"KiCad returned no bounding box for {options.reference}")
    component_center = box_center(bounding_box)

    edge_items = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")

    contours = edge_contours(edge_items)
    fixed_coordinate = (
        component_center.y if options.alignment == "horizontal" else component_center.x
    )
    component_coordinate = (
        component_center.x if options.alignment == "horizontal" else component_center.y
    )
    crossings = scanline_crossings(contours, fixed_coordinate, options.alignment)
    first_edge, second_edge = bracketing_edges(crossings, component_coordinate)
    target_coordinate = (first_edge + second_edge) // 2
    offset = target_coordinate - component_coordinate
    if offset == 0:
        print(
            f"{options.reference} is already centered {options.alignment}ly "
            "between Edge.Cuts."
        )
        return 0

    delta = (
        vector(offset, 0) if options.alignment == "horizontal" else vector(0, offset)
    )
    action = f"Center {options.reference} between board edges {options.alignment}ly"
    with editor_commit(board, action, refill_zones=True):
        footprint.position = vector(
            footprint.position.x + delta.x,
            footprint.position.y + delta.y,
        )
        board.update_items([footprint])

    axis = "X" if options.alignment == "horizontal" else "Y"
    print(
        f"Centered {options.reference} {options.alignment}ly between Edge.Cuts: "
        f"moved {axis} by {to_mm(offset):.6f} mm (undo: {action})."
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse command-line values into explicit module options.

    Args:
        argv: Arguments excluding the executable name, or ``None`` to read the
            process command line.

    Returns:
        A validated immutable :class:`ModuleOptions` instance.

    Raises:
        SystemExit: If argparse rejects a missing or invalid value.

    Side Effects:
        May write argparse usage or errors to the standard streams.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", help="footprint reference, for example J1")
    parser.add_argument(
        "--alignment",
        choices=("horizontal", "vertical"),
        default="horizontal",
        help="axis along which to centre the footprint (default: horizontal)",
    )
    parser.add_argument(
        "--include-text",
        action="store_true",
        help="include reference and value text in the footprint bounds",
    )
    arguments = parser.parse_args(argv)
    return ModuleOptions(
        reference=arguments.reference,
        alignment=arguments.alignment,
        include_text=arguments.include_text,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments, run the board edit, and return its process status."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
