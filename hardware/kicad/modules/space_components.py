"""Set the centre-to-centre spacing between two footprints.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/space_components.py

The anchor footprint remains fixed.  The moving footprint is translated along
the configured axis until its bounding-box centre is the requested distance
from the anchor's centre.  Its current side of the anchor is preserved.  The
move is grouped into one PCB Editor undo/redo transaction.  Save manually
after review.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from kicad_ipc import (
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    to_mm,
    vector,
)


@dataclass(frozen=True)
class ModuleOptions:
    """Explicit footprint pair, axis, spacing, and bounds choice."""

    anchor: str
    moving: str
    alignment: str = "vertical"
    spacing_mm: float = 35.0
    include_text: bool = False


def run(options: ModuleOptions) -> int:
    """Move one footprint to the requested spacing and return zero."""
    if options.alignment not in {"horizontal", "vertical"}:
        raise ValueError('alignment must be "horizontal" or "vertical"')
    if options.spacing_mm < 0:
        raise ValueError("spacing must not be negative")
    if not options.anchor.strip() or not options.moving.strip():
        raise ValueError("footprint references must not be blank")
    if options.anchor == options.moving:
        raise ValueError("anchor and moving references must differ")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    missing = [
        reference
        for reference in (options.anchor, options.moving)
        if reference not in footprints
    ]
    if missing:
        raise RuntimeError(f"missing footprint(s): {', '.join(missing)}")

    centers = {}
    for reference in (options.anchor, options.moving):
        bounding_box = board.get_item_bounding_box(
            footprints[reference],
            include_text=options.include_text,
        )
        if bounding_box is None:
            raise RuntimeError(f"KiCad returned no bounding box for {reference}")
        centers[reference] = box_center(bounding_box)

    anchor_center = centers[options.anchor]
    moving_center = centers[options.moving]
    if options.alignment == "horizontal":
        current_difference = moving_center.x - anchor_center.x
    else:
        current_difference = moving_center.y - anchor_center.y

    if current_difference == 0 and options.spacing_mm != 0:
        raise RuntimeError(
            f"{options.anchor} and {options.moving} have the same "
            f"{options.alignment} centre; move {options.moving} to the desired "
            "side first"
        )

    spacing = from_mm(options.spacing_mm)
    direction = -1 if current_difference < 0 else 1
    target_difference = direction * spacing
    offset = target_difference - current_difference
    if offset == 0:
        print(
            f"{options.anchor} and {options.moving} already have "
            f"{options.spacing_mm:.6f} mm {options.alignment} centre spacing."
        )
        return 0

    delta = (
        vector(offset, 0) if options.alignment == "horizontal" else vector(0, offset)
    )
    moving = footprints[options.moving]
    action = f"Space {options.moving} from {options.anchor} {options.alignment}ly"
    with editor_commit(board, action, refill_zones=True):
        moving.position = vector(
            moving.position.x + delta.x,
            moving.position.y + delta.y,
        )
        board.update_items([moving])

    axis = "X" if options.alignment == "horizontal" else "Y"
    print(
        f"Set {options.moving} {axis}-centre {options.spacing_mm:.6f} mm from "
        f"{options.anchor}: moved {axis} by {to_mm(offset):.6f} mm "
        f"(undo: {action})."
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse the footprint pair and constrained spacing settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("anchor")
    parser.add_argument("moving")
    parser.add_argument(
        "--alignment", choices=("horizontal", "vertical"), default="vertical"
    )
    parser.add_argument("--spacing", type=float, default=35.0)
    parser.add_argument("--include-text", action="store_true")
    args = parser.parse_args(argv)
    if args.spacing < 0:
        parser.error("--spacing must not be negative")
    return ModuleOptions(
        args.anchor, args.moving, args.alignment, args.spacing, args.include_text
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute the spacing operation."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
