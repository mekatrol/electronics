"""Place mounting holes at configured board-edge offsets using IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/align_holes.py

The complete operation is one entry in PCB Editor's Undo/Redo history.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from kicad_ipc import (
    board_edge_bounds,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    to_mm,
    vector,
)


@dataclass(frozen=True)
class ModuleOptions:
    """Explicit mounting-hole references, direction, and edge offsets."""

    top_left: str = "H1"
    top_right: str = "H2"
    bottom_left: str = "H3"
    bottom_right: str = "H4"
    direction: str = "horizontal"
    left_offset_mm: float = 3.0
    right_offset_mm: float = 3.0
    top_offset_mm: float = 35.5
    bottom_offset_mm: float = 5.5


def run(options: ModuleOptions) -> int:
    """Move configured holes in one undoable transaction and return zero."""
    if options.direction not in {"horizontal", "vertical", "both"}:
        raise ValueError('direction must be "horizontal", "vertical", or "both"')
    references = (
        options.top_left,
        options.top_right,
        options.bottom_left,
        options.bottom_right,
    )
    if any(not reference.strip() for reference in references):
        raise ValueError("hole references must not be blank")
    if len(set(references)) != len(references):
        raise ValueError("hole references must be unique")
    offsets = (
        options.left_offset_mm,
        options.right_offset_mm,
        options.top_offset_mm,
        options.bottom_offset_mm,
    )
    if any(offset < 0 for offset in offsets):
        raise ValueError("edge offsets must not be negative")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    left, right, top, bottom = board_edge_bounds(board)
    targets = {
        options.top_left: vector(
            left + from_mm(options.left_offset_mm), top + from_mm(options.top_offset_mm)
        ),
        options.top_right: vector(
            right - from_mm(options.right_offset_mm),
            top + from_mm(options.top_offset_mm),
        ),
        options.bottom_left: vector(
            left + from_mm(options.left_offset_mm),
            bottom - from_mm(options.bottom_offset_mm),
        ),
        options.bottom_right: vector(
            right - from_mm(options.right_offset_mm),
            bottom - from_mm(options.bottom_offset_mm),
        ),
    }

    changed = []
    with editor_commit(board, "Align mounting holes"):
        for reference, target in targets.items():
            if reference not in footprints:
                continue
            footprint = footprints[reference]
            old = footprint.position
            footprint.position = vector(
                target.x if options.direction in {"horizontal", "both"} else old.x,
                target.y if options.direction in {"vertical", "both"} else old.y,
            )
            changed.append(footprint)
            new = footprint.position
            print(
                f"{reference}: ({to_mm(old.x):.3f}, {to_mm(old.y):.3f}) -> "
                f"({to_mm(new.x):.3f}, {to_mm(new.y):.3f}) mm"
            )
        if changed:
            board.update_items(changed)

    print(f"Aligned {len(changed)} mounting holes (undo: Align mounting holes).")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse explicit CLI values; invalid values terminate through argparse."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in (
        ("top-left", "H1"),
        ("top-right", "H2"),
        ("bottom-left", "H3"),
        ("bottom-right", "H4"),
    ):
        parser.add_argument(f"--{name}", default=default)
    parser.add_argument(
        "--direction", choices=("horizontal", "vertical", "both"), default="horizontal"
    )
    parser.add_argument("--left-offset", type=float, default=3.0)
    parser.add_argument("--right-offset", type=float, default=3.0)
    parser.add_argument("--top-offset", type=float, default=35.5)
    parser.add_argument("--bottom-offset", type=float, default=5.5)
    args = parser.parse_args(argv)
    offsets = (
        args.left_offset,
        args.right_offset,
        args.top_offset,
        args.bottom_offset,
    )
    if any(offset < 0 for offset in offsets):
        parser.error("edge offsets must not be negative")
    return ModuleOptions(
        args.top_left,
        args.top_right,
        args.bottom_left,
        args.bottom_right,
        args.direction,
        args.left_offset,
        args.right_offset,
        args.top_offset,
        args.bottom_offset,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute the mounting-hole alignment."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
