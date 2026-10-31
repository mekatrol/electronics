#!/usr/bin/env python3
"""Configure conservative JLCPCB-oriented routing sizes using KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/configure_jlcpcb_netclasses.py

Open the PCB to configure in PCB Editor before running the script. Net-class
changes are made in the live project and left unsaved for review.
KiCad 10 does not expose predefined track and via lists through IPC, so the
script waits for PCB Editor to close before writing those lists to the active
project file. Reopen the project after the script finishes.
"""

import json
import os
import tempfile
import time
from copy import deepcopy
from pathlib import Path

from kicad_ipc import board_document_path, connect_board
from kipy.board_rules import PresetTrackWidth, PresetViaDimension
from kipy.errors import ApiError
from kipy.errors import ConnectionError as KiCadConnectionError
from kipy.project_types import NetClass
from kipy.proto.common.types import DocumentType, MapMergeMode
from kipy.util import from_mm

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


def project_file_path(project, board):
    """Return the project settings file associated with the open board."""
    project_path = Path(project.path)
    candidates = []
    if project_path.suffix == ".kicad_pro":
        candidates.append(project_path)
    else:
        candidates.append(project_path / f"{project.name}.kicad_pro")
    candidates.append(board_document_path(board.document).with_suffix(".kicad_pro"))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError(
        "could not find the active project file; tried "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def patch_project_presets(path):
    """Set preset sizes in a .kicad_pro file and replace it atomically."""
    settings = json.loads(path.read_text(encoding="utf-8"))
    try:
        design_settings = settings["board"]["design_settings"]
    except KeyError as error:
        raise RuntimeError(f"{path} has no board design settings") from error

    # KiCad stores a leading zero entry for the "use net class values" choice.
    design_settings["track_widths"] = [0.0, *TRACK_PRESETS_MM]
    design_settings["via_dimensions"] = [
        {"diameter": 0.0, "drill": 0.0},
        *({"diameter": diameter, "drill": drill} for diameter, drill in VIA_PRESETS_MM),
    ]

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            json.dump(settings, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary_path.chmod(path.stat().st_mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def wait_for_board_to_close(client, board_path):
    """Wait until PCB Editor releases this board before patching its project."""
    print(
        "KiCad 10 cannot reload preset lists through IPC. Close this PCB Editor "
        "window now; waiting for the board to close...",
        flush=True,
    )
    while True:
        try:
            open_boards = client.get_open_documents(DocumentType.DOCTYPE_PCB)
        except ApiError as error:
            # After PCB Editor closes, KiCad 10 may leave the project manager's
            # IPC server running. That server has no GetOpenDocuments handler.
            if "no handler available" not in str(error):
                raise
            open_boards = ()
        except (KiCadConnectionError, OSError):
            open_boards = ()
        if all(board_document_path(document) != board_path for document in open_boards):
            # Let PCB Editor finish its final project-file write after removing
            # the document, then make our update the last write.
            time.sleep(1)
            return
        time.sleep(0.25)


def main():
    try:
        client, board = connect_board()
    except KiCadConnectionError as error:
        raise SystemExit(
            "Could not communicate with KiCad. Ensure PCB Editor is open in the "
            "single running KiCad instance. If more than one instance is open, exit "
            "all of them and relaunch KiCad once. Modal dialogs can also block IPC.\n"
            f"KiCad IPC error: {error}"
        ) from None
    project = client.get_project(board.document)
    existing = project.get_net_classes()
    default = next((item for item in existing if item.name == "Default"), None)
    if default is None:
        raise RuntimeError("the project does not contain a Default net class")

    configured = [configured_class(default, values) for values in NET_CLASSES]
    project.set_net_classes(configured, MapMergeMode.MMM_MERGE)

    actual = {item.name: item for item in project.get_net_classes()}
    missing = [values[0] for values in NET_CLASSES if values[0] not in actual]
    if missing:
        raise RuntimeError(f"KiCad did not create net classes: {', '.join(missing)}")

    presets_updated_via_ipc = True
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
        presets_updated_via_ipc = False
        path = project_file_path(project, board)
        wait_for_board_to_close(client, board_document_path(board.document))
        patch_project_presets(path)

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
    if not presets_updated_via_ipc:
        print(
            "The active project file was patched after PCB Editor closed. "
            "Reopen the project to load the preset sizes."
        )
    else:
        print("Live net-class changes are left unsaved for review in KiCad.")


if __name__ == "__main__":
    main()
