"""Check or set JLCPCB-oriented via settings using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/vias.py

Open the PCB to check in PCB Editor before running the script. By default this
script validates every via without changing the board. Set ``SET_VIAS`` to
``True`` to enlarge undersized vias and convert unsupported blind, buried, or
microvias to through-vias in one undoable PCB Editor transaction. After
applying settings, the script runs KiCad DRC on an isolated copy of the updated
live board, reports every finding, and leaves the real board unsaved for review.
"""

from dataclasses import dataclass

from kicad_ipc import (
    connect_board,
    editor_commit,
    from_mm,
    run_live_board_drc,
    to_mm,
)
from kipy.proto.board.board_types_pb2 import ViaType

# ============================================================
# User settings
# ============================================================
# False validates and reports without changing the board. True repairs every
# non-compliant via and leaves the live board unsaved for inspection.
SET_VIAS = False

# Run the full KiCad DRC after settings are applied. DRC uses an isolated copy
# of the live board, so the real board remains open and unsaved for review.
RUN_DRC_AFTER_SET = True

# These conservative dimensions avoid JLCPCB's surcharge for drills below
# 0.30 mm and agree with this repository's smallest configured net-class via.
# Values are minimums, so intentionally larger signal or power vias pass.
MINIMUM_DRILL_MM = 0.30
MINIMUM_DIAMETER_MM = 0.50

# JLCPCB prefers the diameter to be at least 0.15 mm larger than the hole. A
# 0.10 mm ring on each side is more conservative and gives a total difference
# of 0.20 mm between the via and drill diameters.
MINIMUM_ANNULAR_RING_MM = 0.10

# JLCPCB's standard rigid-PCB service supports through-vias, not blind, buried,
# or microvias. Disable this only for a board using a separately confirmed
# special process.
REQUIRE_THROUGH_VIAS = True


@dataclass(frozen=True)
class Problem:
    """Describe one setting that does not meet the configured requirements."""

    setting: str
    actual: str
    required: str


def via_label(via, index):
    """Return a stable, readable label containing the net and board position."""
    net_name = via.net.name or "no net"
    x_mm = to_mm(via.position.x)
    y_mm = to_mm(via.position.y)
    return f'Via {index} on "{net_name}" at ({x_mm:.3f}, {y_mm:.3f}) mm'


def minimum_problem(setting, actual_nm, required_mm):
    """Return a problem when a dimension is below its configured minimum."""
    if actual_nm >= from_mm(required_mm):
        return None
    return Problem(
        setting,
        f"{to_mm(actual_nm):.3f} mm",
        f"at least {required_mm:.3f} mm",
    )


def via_problems(via):
    """Return every configured JLCPCB manufacturing problem for one via."""
    # Check the two absolute dimensions independently so the report says which
    # part of an undersized via must change.
    checks = [
        minimum_problem("drill diameter", via.drill_diameter, MINIMUM_DRILL_MM),
        minimum_problem("via diameter", via.diameter, MINIMUM_DIAMETER_MM),
    ]

    # The annular ring is half the difference between copper and drill sizes.
    # Checking it separately also catches a large drill inside a large but
    # insufficiently larger copper diameter.
    ring_nm = (via.diameter - via.drill_diameter) / 2
    checks.append(
        minimum_problem("annular ring", ring_nm, MINIMUM_ANNULAR_RING_MM)
    )

    # JLCPCB's ordinary rigid-board process accepts only vias spanning the full
    # copper stack. Report any advanced via type explicitly rather than hiding
    # it behind a generic dimensional failure.
    if REQUIRE_THROUGH_VIAS and via.type != ViaType.VT_THROUGH:
        checks.append(
            Problem(
                "via type",
                ViaType.Name(via.type),
                "through-via (VT_THROUGH)",
            )
        )
    return [problem for problem in checks if problem is not None]


def configure_via(via):
    """Enlarge one via as needed and apply the supported through-via type."""
    # Never reduce an existing drill. Larger holes may be intentional for
    # current capacity, thermal transfer, or a particular finished-hole size.
    drill_nm = max(via.drill_diameter, from_mm(MINIMUM_DRILL_MM))

    # Preserve a larger existing copper diameter while ensuring both the
    # absolute diameter and the annular ring remain large enough for the final
    # drill size.
    minimum_ring_diameter_nm = drill_nm + 2 * from_mm(MINIMUM_ANNULAR_RING_MM)
    diameter_nm = max(
        via.diameter,
        from_mm(MINIMUM_DIAMETER_MM),
        minimum_ring_diameter_nm,
    )

    # Setting the type also updates the drill span to F.Cu--B.Cu in KiCad's IPC
    # model. Do this before assigning geometry so the final values are explicit.
    if REQUIRE_THROUGH_VIAS:
        via.type = ViaType.VT_THROUGH
    via.drill_diameter = drill_nm
    via.diameter = diameter_nm


def print_problems(vias):
    """Print validation results and return the number of failing vias."""
    failed = 0
    for index, via in enumerate(vias, start=1):
        problems = via_problems(via)
        label = via_label(via, index)
        if not problems:
            print(f"PASS: {label}")
            continue
        failed += 1
        print(f"FAIL: {label}")
        for problem in problems:
            print(f"  {problem.setting}: {problem.actual}; required {problem.required}")
    return failed


def main():
    """Validate every board via and optionally repair non-compliant settings."""
    _client, board = connect_board()
    vias = list(board.get_vias())
    if not vias:
        raise SystemExit("No vias found on the open board.")

    failed_before = print_problems(vias)
    if not SET_VIAS:
        if failed_before:
            raise SystemExit(
                f"{failed_before} of {len(vias)} via(s) do not meet the "
                "configured JLCPCB requirements."
            )
        print(f"All {len(vias)} via(s) meet the requirements.")
        return

    # Update only failed vias, keeping the undo transaction and IPC traffic as
    # small as possible. No zone refill is needed for via geometry changes.
    changed = [via for via in vias if via_problems(via)]
    with editor_commit(board, "Set JLCPCB via sizes"):
        for via in changed:
            configure_via(via)
        board.update_items(changed)

    # Verify the in-memory objects immediately so an API or conversion mistake
    # fails loudly instead of reporting success.
    remaining = sum(bool(via_problems(via)) for via in vias)
    if remaining:
        raise RuntimeError(f"{remaining} updated via(s) failed verification")
    print(
        f"Updated {len(changed)} of {len(vias)} via(s) "
        "(undo: Set JLCPCB via sizes)."
    )
    if RUN_DRC_AFTER_SET:
        drc_errors = run_live_board_drc(board)
        if drc_errors:
            raise SystemExit(f"Updated board has {drc_errors} DRC error(s).")
    print("Live board changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
