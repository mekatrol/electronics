"""Centre Edge.Cuts around all footprints using KiCad's IPC API.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/design/layout/center_outline_around_design.py

The routed design stays fixed. Edge.Cuts moves around it, so tracks, vias, and
pads cannot be separated. Zones spanning the whole board move with the outline;
localized zones remain fixed. Save manually after review.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

# Ruff: noqa: E402
# Support direct path execution from any working directory.
if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    modules_directory = next(
        parent
        for parent in Path(__file__).resolve().parents
        if parent.name == "modules"
    )
    sys.path.insert(0, str(modules_directory.parent))

from modules.shared.kicad_geometry import centering_delta, edge_cuts_centroid
from modules.shared.kicad_ipc import (
    BoardLayer,
    box_center,
    box_edges,
    connect_board,
    editor_commit,
    footprint_reference,
    from_mm,
    merge_boxes,
    to_mm,
)


@dataclass(frozen=True)
class ModuleOptions:
    """Bounds and board-zone matching choices for outline centring."""

    include_text: bool = False
    zone_edge_tolerance_mm: float = 0.2


def spans_board(zone, edges, tolerance_mm):
    """Return whether a zone outline follows the current board bounds."""
    zone_edges = box_edges(zone.bounding_box())
    tolerance = from_mm(tolerance_mm)
    return all(
        abs(zone_edge - board_edge) <= tolerance
        for zone_edge, board_edge in zip(zone_edges, edges, strict=False)
    )


def run(options: ModuleOptions) -> int:
    """Translate the outline around fixed routing and return zero on success."""
    if options.zone_edge_tolerance_mm < 0:
        raise ValueError("zone edge tolerance must not be negative")
    _client, board = connect_board()
    footprints = list(board.get_footprints())
    if not footprints:
        print("No footprints to center.")
        return 0

    edge_items = [
        shape for shape in board.get_shapes() if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    if not edge_items:
        raise RuntimeError("board has no Edge.Cuts graphics")

    boxes = []
    for footprint in footprints:
        box = board.get_item_bounding_box(footprint, include_text=options.include_text)
        if box is None:
            raise RuntimeError(
                f"KiCad returned no bounding box for {footprint_reference(footprint)}"
            )
        boxes.append(box)

    footprint_center = box_center(merge_boxes(boxes))
    edge_center = edge_cuts_centroid(edge_items)
    delta = centering_delta(edge_center, footprint_center)
    delta_x, delta_y = delta.x, delta.y
    if delta_x == 0 and delta_y == 0:
        print("Edge.Cuts is already centered around the components.")
        return 0

    edge_boxes = []
    for shape in edge_items:
        box = board.get_item_bounding_box(shape)
        if box is None:
            raise RuntimeError("KiCad returned no bounding box for an Edge.Cuts item")
        edge_boxes.append(box)
    edge_bounds = box_edges(merge_boxes(edge_boxes))
    board_zones = [
        zone
        for zone in board.get_zones()
        if spans_board(zone, edge_bounds, options.zone_edge_tolerance_mm)
    ]
    action = "Center board outline around components"
    with editor_commit(board, action, refill_zones=True):
        for edge in edge_items:
            edge.move(delta)
        for zone in board_zones:
            zone.move(delta)
        board.update_items([*edge_items, *board_zones])

    print(
        f"Centered Edge.Cuts around {len(footprints)} footprint(s): "
        f"moved outline X by {to_mm(delta_x):.6f} mm and "
        f"Y by {to_mm(delta_y):.6f} mm; moved {len(board_zones)} "
        f"board-spanning zone(s) with it (undo: {action})."
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> ModuleOptions:
    """Parse footprint-bound and non-negative zone-tolerance settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--zone-edge-tolerance", type=float, default=0.2)
    args = parser.parse_args(argv)
    if args.zone_edge_tolerance < 0:
        parser.error("--zone-edge-tolerance must not be negative")
    return ModuleOptions(args.include_text, args.zone_edge_tolerance)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and centre the board outline."""
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
