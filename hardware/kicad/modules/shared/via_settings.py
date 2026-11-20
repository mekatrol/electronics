"""Shared manufacturing settings for ordinary through-vias.

Validation and via-creation modules import these values so a manufacturing
rule change cannot leave newly created vias inconsistent with the validator.
All dimensions are in millimetres.
"""

# These conservative dimensions avoid JLCPCB's surcharge for drills below
# 0.30 mm and agree with this repository's smallest configured net-class via.
MINIMUM_DRILL_MM = 0.30
MINIMUM_DIAMETER_MM = 0.50

# A 0.10 mm ring on each side gives a total copper-to-hole difference of
# 0.20 mm, more conservative than JLCPCB's 0.15 mm preference.
MINIMUM_ANNULAR_RING_MM = 0.10

# Standard rigid-board vias span the complete copper stack.
REQUIRE_THROUGH_VIAS = True


def default_via_diameter_mm(drill_diameter_mm: float = MINIMUM_DRILL_MM) -> float:
    """Return the smallest compliant copper diameter for a drill size."""
    return max(
        MINIMUM_DIAMETER_MM,
        drill_diameter_mm + 2 * MINIMUM_ANNULAR_RING_MM,
    )


DEFAULT_DRILL_DIAMETER_MM = MINIMUM_DRILL_MM
DEFAULT_VIA_DIAMETER_MM = default_via_diameter_mm()


__all__ = [
    "DEFAULT_DRILL_DIAMETER_MM",
    "DEFAULT_VIA_DIAMETER_MM",
    "MINIMUM_ANNULAR_RING_MM",
    "MINIMUM_DIAMETER_MM",
    "MINIMUM_DRILL_MM",
    "REQUIRE_THROUGH_VIAS",
    "default_via_diameter_mm",
]
