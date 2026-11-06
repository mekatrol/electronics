"""Check or set JLCPCB-oriented thermal relief settings using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/thermal_releifs.py

Open the PCB to check in PCB Editor before running the script. By default this
script checks every copper zone assigned to the GND or +5V net. Set
``SET_RELIEFS`` to ``True`` to write the configured settings to every matching
zone in one undoable PCB Editor transaction and refill all zones. Changes are
left unsaved for review. Pad-level and custom-rule overrides are outside the
scope of this zone-level check, so run KiCad's Design Rules Checker afterwards.
"""

from dataclasses import dataclass

from kicad_ipc import connect_board, editor_commit, from_mm, to_mm
from kipy.proto.board.board_types_pb2 import (
    IslandRemovalMode,
    ZoneConnectionStyle,
    ZoneCornerSmoothingMode,
)

# ============================================================
# User settings
# ============================================================
# False checks and reports without changing the board. True writes the exact
# configured values to every matching zone and leaves the result unsaved.
SET_RELIEFS = True

# Only copper zones on these nets are checked. Net matching is case-sensitive,
# just as it is in KiCad.
ZONE_NET_NAMES = ["GND", "+5V"]

# Conservative values for an ordinary JLCPCB 2-layer, 1 oz copper board.
# Numeric settings are minimums: a larger existing value passes the check.
CLEARANCE_MM = 0.20
MINIMUM_WIDTH_MM = 0.25
THERMAL_RELIEF_GAP_MM = 0.25
THERMAL_SPOKE_WIDTH_MM = 0.30

# These settings must match exactly rather than merely meet a minimum.
PAD_CONNECTION = ZoneConnectionStyle.ZCS_THERMAL
CORNER_SMOOTHING = ZoneCornerSmoothingMode.ZCSM_NONE
ISLAND_REMOVAL = IslandRemovalMode.IRM_ALWAYS


@dataclass(frozen=True)
class Problem:
    setting: str
    actual: str
    required: str


def zone_label(zone, index):
    """Return a stable, readable label even when the zone has no name."""
    name = f' "{zone.name}"' if zone.name else ""
    return f"Zone {index}{name} ({zone.net.name})"


def minimum_problem(setting, actual_nm, required_mm):
    """Return a problem when a dimension is below its configured minimum."""
    required_nm = from_mm(required_mm)
    if actual_nm is not None and actual_nm >= required_nm:
        return None
    actual = "not set" if actual_nm is None else f"{to_mm(actual_nm):.3f} mm"
    return Problem(setting, actual, f"at least {required_mm:.3f} mm")


def zone_problems(zone):
    """Return every JLCPCB thermal-relief setting problem for one zone."""
    connection = zone.connection
    checks = [
        minimum_problem("clearance", zone.clearance, CLEARANCE_MM),
        minimum_problem("minimum width", zone.min_thickness, MINIMUM_WIDTH_MM),
        minimum_problem(
            "thermal relief gap",
            connection.thermal_spokes.gap,
            THERMAL_RELIEF_GAP_MM,
        ),
        minimum_problem(
            "thermal spoke width",
            connection.thermal_spokes.width,
            THERMAL_SPOKE_WIDTH_MM,
        ),
    ]
    if connection.zone_connection != PAD_CONNECTION:
        checks.append(
            Problem(
                "pad connections",
                ZoneConnectionStyle.Name(connection.zone_connection),
                "thermal reliefs",
            )
        )
    if zone.corner_smoothing != CORNER_SMOOTHING:
        checks.append(
            Problem(
                "corner smoothing",
                ZoneCornerSmoothingMode.Name(zone.corner_smoothing),
                "none",
            )
        )
    if zone.island_mode != ISLAND_REMOVAL:
        checks.append(
            Problem(
                "island removal",
                IslandRemovalMode.Name(zone.island_mode),
                "always",
            )
        )
    return [problem for problem in checks if problem is not None]


def configure_zone(zone):
    """Apply the exact configured zone-level thermal relief values."""
    zone.clearance = from_mm(CLEARANCE_MM)
    zone.min_thickness = from_mm(MINIMUM_WIDTH_MM)
    zone.connection.zone_connection = PAD_CONNECTION
    spokes = zone.connection.thermal_spokes
    spokes.gap = from_mm(THERMAL_RELIEF_GAP_MM)
    spokes.width = from_mm(THERMAL_SPOKE_WIDTH_MM)
    zone.corner_smoothing = CORNER_SMOOTHING
    zone.island_mode = ISLAND_REMOVAL


def matching_zones(board):
    """Return copper zones assigned to any configured net."""
    return [
        zone
        for zone in board.get_zones()
        if not zone.is_rule_area()
        and zone.net is not None
        and zone.net.name in ZONE_NET_NAMES
    ]


def print_problems(zones):
    """Print problems and return the number of non-compliant zones."""
    failed = 0
    for index, zone in enumerate(zones, start=1):
        problems = zone_problems(zone)
        label = zone_label(zone, index)
        if not problems:
            print(f"PASS: {label}")
            continue
        failed += 1
        print(f"FAIL: {label}")
        for problem in problems:
            print(f"  {problem.setting}: {problem.actual}; required {problem.required}")
    return failed


def main():
    """Check matching zones and optionally correct their settings."""
    _client, board = connect_board()
    zones = matching_zones(board)
    if not zones:
        names = ", ".join(f'"{name}"' for name in ZONE_NET_NAMES)
        raise SystemExit(f"No copper zones found on configured nets: {names}.")

    failed_before = print_problems(zones)
    if not SET_RELIEFS:
        if failed_before:
            raise SystemExit(
                f"{failed_before} of {len(zones)} matching zone(s) "
                "do not meet the configured thermal relief settings."
            )
        print(f"All {len(zones)} matching zone(s) meet the requirements.")
        return

    with editor_commit(board, "Set zone thermal reliefs", refill_zones=True):
        for zone in zones:
            configure_zone(zone)
        board.update_items(zones)

    remaining = sum(bool(zone_problems(zone)) for zone in zones)
    if remaining:
        raise RuntimeError(f"{remaining} updated zone(s) failed verification")
    print(
        f"Updated all {len(zones)} matching zone(s) "
        "(undo: Set zone thermal reliefs)."
    )
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
