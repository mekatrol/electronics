"""Check or set JLCPCB-oriented thermal relief settings using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python \
        hardware/kicad/modules/design/rules/validate_thermal_reliefs.py

Open the PCB to check in PCB Editor before running the script. By default this
script only validates every copper zone assigned to a configured net. Pass
``--fix`` to write the configured settings to every matching zone in one
undoable PCB Editor transaction before refilling all zones. Pads inherit these
zone settings; their footprint definitions are deliberately left unchanged so
the board footprints continue to match their library copies. After applying
settings, the script runs KiCad DRC on an isolated copy of the updated live
board, reports every finding, ignores expected unconnected-item findings on a
partially routed board, and leaves the real board unsaved for review.
"""

import argparse
import sys
from dataclasses import dataclass

from kipy.errors import ApiError
from kipy.proto.board.board_types_pb2 import (
    IslandRemovalMode,
    ZoneConnectionStyle,
    ZoneCornerSmoothingMode,
)

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

from modules.shared.kicad_ipc import (
    connect_board,
    editor_commit,
    from_mm,
    retry_when_kicad_busy,
    run_live_board_drc,
    to_mm,
)

# ============================================================
# User settings
# ============================================================
# Run the full KiCad DRC after settings are applied. DRC uses an isolated copy
# of the live board, so the real board remains open and unsaved for review.
RUN_DRC_AFTER_SET = True

# Only copper zones on these nets are checked. Net matching is case-sensitive,
# just as it is in KiCad.
ZONE_NET_NAMES = ["GND", "+5V", "+3.3V"]

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


def missing_zone_net_names(zones):
    """Return configured net names that have no matching copper zone."""
    present_names = {zone.net.name for zone in zones}
    return [name for name in ZONE_NET_NAMES if name not in present_names]


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


def parse_args():
    """Parse the explicit opt-in for changing the live board."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="correct thermal-relief settings, refill zones, and run DRC",
    )
    return parser.parse_args()


def main():
    """Check matching zones and optionally correct their settings."""
    args = parse_args()
    _client, board = connect_board()
    try:
        zones = retry_when_kicad_busy(lambda: matching_zones(board))
    except ApiError as error:
        if "busy and cannot respond" not in str(error).lower():
            raise
        raise SystemExit(
            "PCB Editor remained busy for 30 seconds. Finish or cancel any "
            "active tool, close modal dialogs, and wait for zone filling to "
            "finish before running Validate Thermal Reliefs again."
        ) from None
    missing_names = missing_zone_net_names(zones)
    for name in missing_names:
        print(
            f'ERROR: No copper zone found on configured net "{name}"; ignoring it.',
            file=sys.stderr,
        )
    if not zones:
        raise SystemExit("No configured copper zones exist on the open board.")

    failed_before = print_problems(zones)
    if not args.fix:
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
    if RUN_DRC_AFTER_SET:
        try:
            # This check is useful while routing is still in progress. Report
            # ratsnest/unconnected findings for visibility, but only make
            # actual DRC violations fail the thermal-relief update.
            drc_errors = run_live_board_drc(board, fail_on_unconnected=False)
        except RuntimeError as error:
            raise SystemExit(f"DRC could not be completed: {error}") from None
        if drc_errors:
            raise SystemExit(f"Updated board has {drc_errors} DRC error(s).")
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
