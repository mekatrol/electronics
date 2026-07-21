#!/usr/bin/env python3
"""Validate and grid-align PCB fiducials using KiCad's IPC API.

Execution:
    1. Enable KiCad's API server and open the target board in PCB Editor.
    2. Review the values in the ``User settings`` section below.
    3. From the repository root, run::

        .venv-kicad-ipc/bin/python hardware/kicad/modules/check_fiducials.py

The script regards a side as populated when it contains at least one footprint
that is not a fiducial and is not marked Do Not Populate. Each populated side
must have the configured minimum number of fiducials. An unpopulated side does
not need fiducials.

Fiducials are recognized by a reference beginning with ``FID``, a footprint
library identifier containing ``fiducial``, or a value exactly equal to
``Fiducial``. Their pad diameter and resulting solder-mask opening are checked
against the configured values. The mask opening diameter is the copper pad
diameter plus twice the pad's solder-mask margin; for example, the standard
1 mm copper / 2 mm mask footprint has a 0.5 mm margin on every side.

Each coordinate is rounded independently to the nearest configured grid mark.
A move is skipped if its expanded footprint envelope would cross Edge.Cuts or
overlap a footprint, track, via, or another fiducial on the same side. Tracks
use KiCad's geometry-aware hit test so empty space inside a diagonal track's
rectangular bounding box is not mistaken for copper. This is a conservative
pre-move safety check; run KiCad's full Design Rules Checker afterwards because
the IPC API does not expose the complete DRC engine.

Accepted moves form one ``Align and check fiducials`` entry in PCB Editor's
Undo/Redo history. The script changes the live PCB Editor board but does not
save it. After the transaction is published, the shared IPC utility performs
a blocking refill of every copper zone so fills and fiducial clearances match
the new pad locations. Validation failures are printed as errors and produce
exit status 1; unsafe moves are warnings and are left unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from kipy.board_types import PSS_CIRCLE

from kicad_ipc import (
    BoardLayer,
    board_edge_bounds,
    box_edges,
    connect_board,
    editor_commit,
    footprint_reference,
    from_mm,
    to_mm,
    vector,
)


# ============================================================
# User settings: required fiducials and coordinate alignment
# ============================================================
# Require this many fiducials independently on every side that has populated
# components. Three per populated assembly side is the normal global-fiducial
# arrangement. A board populated on both sides therefore needs three on each.
MIN_FIDUCIALS_PER_POPULATED_SIDE = 3

# Round both the X and Y coordinate to the nearest multiple of this value in
# KiCad's absolute board coordinate system. For example, 136.3 becomes 136.5
# when this is 0.5 mm. This value must be greater than zero.
POSITION_GRID_MM = 0.5


# ============================================================
# User settings: expected fiducial construction
# ============================================================
# Expected bare-copper target diameter. Fiducial pads must be circular, so the
# script checks both the pad's X and Y sizes against this value.
COPPER_DIAMETER_MM = 1.0

# Expected diameter of the solder-mask opening. KiCad stores a mask margin per
# side, so the script calculates: pad diameter + (2 * solder-mask margin).
MASK_OPENING_DIAMETER_MM = 2.0

# Maximum accepted difference when comparing the stored dimensions. The
# default permits one micrometre of serialization/rounding variation.
DIMENSION_TOLERANCE_MM = 0.001


# ============================================================
# User settings: placement safety and discovery
# ============================================================
# Extra space added around KiCad's complete fiducial footprint bounding box
# while testing a snapped location. The resulting envelope must stay inside
# Edge.Cuts and must not overlap the bounds of same-side placement obstacles.
PLACEMENT_CLEARANCE_MM = 0.25

# References beginning with this text are treated as fiducials even if their
# footprint library name or value does not contain the word "fiducial".
FIDUCIAL_REFERENCE_PREFIX = "FID"

# True prints the old and new coordinate for every accepted move.
DEBUG = True


@dataclass(frozen=True)
class Bounds:
    left: int
    right: int
    top: int
    bottom: int

    def moved(self, dx: int, dy: int) -> "Bounds":
        return Bounds(self.left + dx, self.right + dx, self.top + dy, self.bottom + dy)

    def expanded(self, amount: int) -> "Bounds":
        return Bounds(
            self.left - amount,
            self.right + amount,
            self.top - amount,
            self.bottom + amount,
        )

    def overlaps(self, other: "Bounds") -> bool:
        return not (
            self.right <= other.left
            or other.right <= self.left
            or self.bottom <= other.top
            or other.bottom <= self.top
        )


def snap_coordinate(value: int, grid: int) -> int:
    """Round an integer nanometre coordinate to its nearest grid point."""
    return int(round(value / grid)) * grid


def bounds_of(box) -> Bounds:
    """Convert a KiCad IPC box into consistently ordered edge coordinates."""
    return Bounds(*box_edges(box))


def side_name(layer) -> str:
    """Return a human-readable name for an outer copper footprint layer."""
    return "back" if layer == BoardLayer.BL_B_Cu else "front"


def is_fiducial(footprint) -> bool:
    """Identify a fiducial by reference, library identifier, or value."""
    reference = footprint_reference(footprint).upper()
    library_id = str(footprint.definition.id).lower()
    value = footprint.value_field.text.value.lower()
    return (
        reference.startswith(FIDUCIAL_REFERENCE_PREFIX.upper())
        or "fiducial" in library_id
        or value == "fiducial"
    )


def populated_sides(footprints) -> set:
    """Return assembly sides containing at least one populated component."""
    return {
        footprint.layer
        for footprint in footprints
        if not is_fiducial(footprint) and not footprint.attributes.do_not_populate
    }


def validate_dimensions(footprint) -> list[str]:
    """Return construction errors for one fiducial footprint."""
    reference = footprint_reference(footprint)
    pads = list(footprint.definition.pads)
    if len(pads) != 1:
        return [f"{reference}: expected exactly one pad, found {len(pads)}"]

    pad = pads[0]
    copper = pad.padstack.copper_layer(footprint.layer)
    if copper is None:
        return [f"{reference}: pad has no copper on its footprint side"]

    problems = []
    if copper.shape != PSS_CIRCLE:
        problems.append(f"{reference}: copper pad is not circular")

    diameter_x = to_mm(copper.size.x)
    diameter_y = to_mm(copper.size.y)
    outer = (
        pad.padstack.back_outer_layers
        if footprint.layer == BoardLayer.BL_B_Cu
        else pad.padstack.front_outer_layers
    )
    margin = to_mm(outer.solder_mask_settings.solder_mask_margin)
    mask_x = diameter_x + 2 * margin
    mask_y = diameter_y + 2 * margin
    tolerance = DIMENSION_TOLERANCE_MM
    if abs(diameter_x - COPPER_DIAMETER_MM) > tolerance or abs(
        diameter_y - COPPER_DIAMETER_MM
    ) > tolerance:
        problems.append(
            f"{reference}: copper is {diameter_x:.3f} x {diameter_y:.3f} mm; "
            f"expected {COPPER_DIAMETER_MM:.3f} mm diameter"
        )
    if abs(mask_x - MASK_OPENING_DIAMETER_MM) > tolerance or abs(
        mask_y - MASK_OPENING_DIAMETER_MM
    ) > tolerance:
        problems.append(
            f"{reference}: mask opening is {mask_x:.3f} x {mask_y:.3f} mm; "
            f"expected {MASK_OPENING_DIAMETER_MM:.3f} mm diameter"
        )
    return problems


def safe_target(
    board, footprint, target, board_bounds, obstacles, track_obstacles
) -> tuple[bool, str]:
    """Reject targets whose clearance envelope leaves or overlaps geometry."""
    current_box = board.get_item_bounding_box(footprint, include_text=False)
    if current_box is None:
        return False, "KiCad supplied no footprint bounding box"
    dx = target.x - footprint.position.x
    dy = target.y - footprint.position.y
    envelope = bounds_of(current_box).moved(dx, dy).expanded(from_mm(PLACEMENT_CLEARANCE_MM))
    if (
        envelope.left < board_bounds.left
        or envelope.right > board_bounds.right
        or envelope.top < board_bounds.top
        or envelope.bottom > board_bounds.bottom
    ):
        return False, "clearance envelope would cross Edge.Cuts"
    for item_id, label, obstacle in obstacles:
        if item_id == footprint.id.value:
            continue
        if envelope.overlaps(obstacle):
            return False, f"clearance envelope would overlap {label}"
    # A track's axis-aligned bounding box contains substantial empty space when
    # the track is diagonal. Ask KiCad to test the actual track geometry against
    # a circle enclosing the proposed fiducial envelope instead.
    track_tolerance = max(
        envelope.right - envelope.left,
        envelope.bottom - envelope.top,
    ) // 2
    for label, track in track_obstacles:
        if board.hit_test(track, target, tolerance=track_tolerance):
            return False, f"clearance envelope would overlap {label}"
    return True, ""


def main() -> int:
    """Check the open board and publish every safe alignment as one edit."""
    if POSITION_GRID_MM <= 0:
        raise ValueError("POSITION_GRID_MM must be greater than zero")

    _client, board = connect_board()
    footprints = list(board.get_footprints())
    fiducials = [footprint for footprint in footprints if is_fiducial(footprint)]
    populated = populated_sides(footprints)
    errors = []

    for layer in sorted(populated):
        count = sum(footprint.layer == layer for footprint in fiducials)
        if count < MIN_FIDUCIALS_PER_POPULATED_SIDE:
            errors.append(
                f"{side_name(layer)}: found {count} fiducial(s), need at least "
                f"{MIN_FIDUCIALS_PER_POPULATED_SIDE} because the side has components"
            )
    for footprint in fiducials:
        errors.extend(validate_dimensions(footprint))

    edge_bounds = Bounds(*board_edge_bounds(board))
    obstacle_by_side = {}
    tracks_by_side = {}
    for layer in populated:
        side_obstacles = []
        for footprint in footprints:
            if footprint.layer != layer:
                continue
            box = board.get_item_bounding_box(footprint, include_text=False)
            if box is not None:
                side_obstacles.append(
                    (footprint.id.value, footprint_reference(footprint), bounds_of(box))
                )
        for index, via in enumerate(board.get_vias(), start=1):
            box = board.get_item_bounding_box(via)
            if box is not None:
                side_obstacles.append((via.id.value, f"via {index}", bounds_of(box)))
        obstacle_by_side[layer] = side_obstacles
        tracks_by_side[layer] = [
            (f"track {index}", track)
            for index, track in enumerate(board.get_tracks(), start=1)
            if track.layer == layer
        ]

    grid = from_mm(POSITION_GRID_MM)
    changed = []
    skipped = []
    # Zone refill is requested through the shared transaction helper. It runs
    # only after push_commit publishes the moved pads, because KiCad's zone
    # filler cannot see footprint geometry while it is still staged.
    with editor_commit(board, "Align and check fiducials", refill_zones=True):
        for footprint in fiducials:
            old = footprint.position
            target = vector(snap_coordinate(old.x, grid), snap_coordinate(old.y, grid))
            if target.x == old.x and target.y == old.y:
                continue
            safe, reason = safe_target(
                board,
                footprint,
                target,
                edge_bounds,
                obstacle_by_side.get(footprint.layer, []),
                tracks_by_side.get(footprint.layer, []),
            )
            reference = footprint_reference(footprint)
            if not safe:
                skipped.append(f"{reference}: not moved: {reason}")
                continue
            footprint.position = target
            changed.append(footprint)
            if DEBUG:
                print(
                    f"{reference}: ({to_mm(old.x):.3f}, {to_mm(old.y):.3f}) -> "
                    f"({to_mm(target.x):.3f}, {to_mm(target.y):.3f}) mm"
                )
        if changed:
            board.update_items(changed)

    for message in skipped:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    print(
        f"Checked {len(fiducials)} fiducial(s) on {len(populated)} populated side(s); "
        f"aligned {len(changed)}, skipped {len(skipped)}."
    )
    if changed:
        print("Review the result in PCB Editor and run the full DRC before saving.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
