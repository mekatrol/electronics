"""Centre and optionally distribute configured footprints using KiCad's IPC API.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/center_and_distribute_items.py

All moves are grouped into one PCB Editor undo/redo transaction.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from kicad_ipc import (
    box_center,
    connect_board,
    editor_commit,
    footprints_by_reference,
    to_mm,
    vector,
)
from kicad_utils import centering_delta, distribution_offsets


@dataclass(frozen=True)
class ModuleOptions:
    """Footprints and layout choices for the centring operation."""

    references: tuple[str, ...]
    alignment: str = "horizontal"
    distribute_spacing: bool = False


def run(options: ModuleOptions) -> int:
    """Centre footprints on the first reference and return zero on success."""
    if not options.references:
        raise ValueError("references must contain at least one component")
    if any(not reference.strip() for reference in options.references):
        raise ValueError("references must not contain blank values")
    if len(set(options.references)) != len(options.references):
        raise ValueError("references must be unique")
    if options.alignment not in {"vertical", "horizontal"}:
        raise ValueError('alignment must be "vertical" or "horizontal"')
    if options.distribute_spacing and len(options.references) < 3:
        raise ValueError("distribute spacing requires at least three references")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    missing = [
        reference for reference in options.references if reference not in footprints
    ]
    if missing:
        raise RuntimeError(f"missing footprint(s): {', '.join(missing)}")

    boxes = {}
    for reference in options.references:
        bbox = board.get_item_bounding_box(footprints[reference], include_text=True)
        if bbox is None:
            raise RuntimeError(f"KiCad returned no bounding box for {reference}")
        boxes[reference] = bbox

    anchor_center = box_center(boxes[options.references[0]])

    distribute_offsets = {reference: 0 for reference in options.references}
    if options.distribute_spacing:
        if options.alignment == "vertical":
            axis_items = [
                (
                    reference,
                    boxes[reference].pos.x,
                    boxes[reference].pos.x + boxes[reference].size.x,
                )
                for reference in options.references
            ]
        else:
            axis_items = [
                (
                    reference,
                    boxes[reference].pos.y,
                    boxes[reference].pos.y + boxes[reference].size.y,
                )
                for reference in options.references
            ]
        # Bounding boxes can have negative sizes; normalise their axis edges.
        axis_items = [
            (reference, min(start, end), max(start, end))
            for reference, start, end in axis_items
        ]
        distribute_offsets = distribution_offsets(axis_items)

    action = f"Center footprints {options.alignment}ly"
    if options.distribute_spacing:
        action += " and distribute items"
    changed = []
    with editor_commit(board, action):
        for reference in options.references:
            footprint = footprints[reference]
            center = box_center(boxes[reference])
            alignment_offset = centering_delta(center, anchor_center)
            old = footprint.position
            if options.alignment == "vertical":
                delta_x = distribute_offsets[reference]
                delta_y = alignment_offset.y
            else:
                delta_x = alignment_offset.x
                delta_y = distribute_offsets[reference]
            footprint.position = vector(old.x + delta_x, old.y + delta_y)
            changed.append(footprint)
            print(
                f"{reference}: moved X by {to_mm(delta_x):.3f} mm, "
                f"Y by {to_mm(delta_y):.3f} mm"
            )
        board.update_items(changed)

    print(f"Centered {len(changed)} footprint(s) (undo: {action}).")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse footprint references and bounded layout choices from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", nargs="+", required=True)
    parser.add_argument(
        "--alignment", choices=("horizontal", "vertical"), default="horizontal"
    )
    parser.add_argument("--distribute-spacing", action="store_true")
    args = parser.parse_args(argv)
    return ModuleOptions(
        tuple(args.references), args.alignment, args.distribute_spacing
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute the footprint layout operation."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
