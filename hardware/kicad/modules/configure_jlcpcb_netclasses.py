#!/usr/bin/env python3
"""Configure conservative JLCPCB-oriented routing sizes using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/configure_jlcpcb_netclasses.py

Open ``mek-output-expander.kicad_pcb`` in PCB Editor before running the script.
Net-class changes are made in the live project and left unsaved for review.
KiCad 10 does not expose predefined track and via lists through IPC; those
lists must already be present in the project file and are loaded when PCB
Editor opens it.
"""

from copy import deepcopy

from kicad_ipc import board_document_path, connect_board
from kipy.board_rules import PresetTrackWidth, PresetViaDimension
from kipy.errors import ApiError
from kipy.project_types import NetClass
from kipy.proto.common.types import MapMergeMode
from kipy.util import from_mm

EXPECTED_BOARD = "mek-output-expander.kicad_pcb"

# These values stay comfortably inside JLCPCB's normal rigid-PCB process.
# Fine Signal is intended only for genuinely constrained fan-out.
NET_CLASSES = (
    # name, clearance, track, differential width, differential gap, via, drill
    ("Default", 0.20, 0.20, 0.20, 0.20, 0.60, 0.30),
    ("Fine Signal", 0.15, 0.15, 0.15, 0.15, 0.50, 0.30),
    ("Signal", 0.20, 0.25, 0.20, 0.20, 0.60, 0.30),
    ("Heavy Signal", 0.20, 0.30, 0.25, 0.25, 0.60, 0.30),
    ("Power", 0.20, 0.50, 0.25, 0.25, 0.80, 0.40),
    ("High Power", 0.25, 1.00, 0.30, 0.30, 1.00, 0.50),
    ("Heavy Load", 0.40, 1.50, 0.40, 0.40, 1.20, 0.60),
)

TRACK_PRESETS_MM = (0.15, 0.20, 0.25, 0.30, 0.50, 1.00, 1.50)

VIA_PRESETS_MM = (
    (0.50, 0.30),
    (0.60, 0.30),
    (0.80, 0.40),
    (1.00, 0.50),
    (1.20, 0.60),
)


def configured_class(template, values):
    """Clone a complete API class so optional schematic settings are retained."""
    name, clearance, track, diff_width, diff_gap, via, drill = values
    net_class = NetClass(deepcopy(template.proto))
    net_class.proto.name = name
    net_class.clearance = from_mm(clearance)
    net_class.track_width = from_mm(track)
    net_class.diff_pair_track_width = from_mm(diff_width)
    net_class.diff_pair_gap = from_mm(diff_gap)
    net_class.diff_pair_via_gap = from_mm(diff_gap)
    net_class.via_diameter = from_mm(via)
    net_class.via_drill = from_mm(drill)
    return net_class


def preset_via(diameter_mm, drill_mm):
    via = PresetViaDimension()
    via.diameter = from_mm(diameter_mm)
    via.drill = from_mm(drill_mm)
    return via


def main():
    client, board = connect_board()
    board_path = board_document_path(board.document)
    if board_path.name != EXPECTED_BOARD:
        raise RuntimeError(
            f"expected {EXPECTED_BOARD!r}, but PCB Editor has {board_path.name!r} open"
        )

    project = client.get_project(board.document)
    existing = project.get_net_classes()
    default = next((item for item in existing if item.name == "Default"), None)
    if default is None:
        raise RuntimeError("the project does not contain a Default net class")

    configured = [configured_class(default, values) for values in NET_CLASSES]
    project.set_net_classes(configured, MapMergeMode.MMM_MERGE)

    presets_updated = True
    try:
        rules = board.get_design_rules().rules
        rules.predefined_sizes.tracks = [
            PresetTrackWidth.from_width(from_mm(width)) for width in TRACK_PRESETS_MM
        ]
        rules.predefined_sizes.vias = [
            preset_via(diameter, drill) for diameter, drill in VIA_PRESETS_MM
        ]
        board.set_design_rules(rules)
    except ApiError as error:
        # KiCad 10 has no Get/SetBoardDesignRules handler.  Its preset lists
        # must be placed in the project file and loaded by reopening PCB Editor.
        if "no handler available" not in str(error):
            raise
        presets_updated = False

    actual = {item.name: item for item in project.get_net_classes()}
    missing = [values[0] for values in NET_CLASSES if values[0] not in actual]
    if missing:
        raise RuntimeError(f"KiCad did not create net classes: {', '.join(missing)}")

    print(f"Configured {len(configured)} net classes in {project.name}:")
    for values in NET_CLASSES:
        name, clearance, track, _dw, _dg, via, drill = values
        print(
            f"  {name:12} track {track:.2f} mm, clearance {clearance:.2f} mm, "
            f"via {via:.2f}/{drill:.2f} mm"
        )
    print(
        "Track presets: " + ", ".join(f"{width:.2f} mm" for width in TRACK_PRESETS_MM)
    )
    print(
        "Via presets: "
        + ", ".join(
            f"{diameter:.2f}/{drill:.2f} mm" for diameter, drill in VIA_PRESETS_MM
        )
    )
    if not presets_updated:
        print(
            "KiCad 10 cannot update preset lists through IPC; reopen the patched project."
        )
    print("Project left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
