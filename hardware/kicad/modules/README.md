# KiCad scripts

This directory contains PCB Editor automation scripts, a command-line
manufacturing-file generator, and its support modules.

## KiCad IPC API setup

KiCad's SWIG-based `pcbnew` Python interface is deprecated and is scheduled for
removal in KiCad 11. New and migrated automation should use KiCad's official
`kicad-python` (`kipy`) IPC client. The IPC client runs in an external Python
process and communicates with a running KiCad application.

### Enable the API server

For the KiCad 10 Flatpak:

1. Start KiCad and open **Preferences → Plugins**.
2. Enable the **API server** option.
3. Close and restart KiCad after changing the option.
4. Open the required `.kicad_pcb` in PCB Editor and leave PCB Editor running
   while an IPC script executes.

The project manager alone is insufficient. Board requests such as
`GetOpenDocuments` are available only while PCB Editor is open and has
registered its IPC request handlers.

No `flatpak override` was needed on this system. The existing Flatpak
permissions already include home-directory access and shared IPC:

```text
shared=network;ipc;
filesystems=home;/media;/run/media;
```

The Flatpak places its API socket at:

```text
~/.var/app/org.kicad.KiCad/cache/tmp/kicad/api.sock
```

The official client detects that path automatically. Do not change the socket
permissions or expose additional host directories merely to use the API. A
`Permission denied` error from a containerized development tool can come from
that tool's own sandbox; it does not imply that a normal terminal process
needs a Flatpak override.

### Install the external Python client

Create a virtual environment once from the repository root and install the
official binding:

```sh
python3 -m venv .venv-kicad-ipc
.venv-kicad-ipc/bin/pip install kicad-python==0.7.1
```

Activate it for an interactive terminal session if desired:

```sh
source .venv-kicad-ipc/bin/activate
```

KiCad 10.0.4 was tested with the latest available `kicad-python` release,
0.7.1. That binding identifies its generated API definitions as KiCad 10.0.1,
so `KiCad.check_version()` emits a strict patch-version warning against
10.0.4. Direct IPC ping and read operations were nevertheless verified:

```text
Open board: led_controller.kicad_pcb
Footprints: 31
Board text items: 28
Zones: 2
```

### Troubleshooting

- **Connection refused or no socket:** confirm the API server is enabled, then
  restart KiCad.
- **`no handler available for ... GetOpenDocuments`:** PCB Editor is not open,
  or the client connected to another running KiCad instance. Close redundant
  KiCad instances, open the board from the remaining project manager, and try
  again.
- **Multiple KiCad instances:** the default client connects to the first API
  socket it discovers. Keep one project-manager/PCB-Editor instance running
  when invoking scripts manually.
- **Flatpak socket check:** run
  `ls -l ~/.var/app/org.kicad.KiCad/cache/tmp/kicad/api.sock`.

## PCB Editor scripts

The following scripts use the supported `kipy` IPC API. Open the board to
modify in PCB Editor, edit the script's **User settings** section as needed,
then run it from a terminal at the repository root:

```sh
.venv-kicad-ipc/bin/python hardware/kicad/modules/SCRIPT_NAME.py
```

Replace `SCRIPT_NAME.py` with the desired filename. Do not use KiCad PyShell:
it loads the deprecated SWIG interface, whereas IPC clients are external
processes. Every mutating script opens a named editor commit and pushes all its
changes as one PCB Editor Undo/Redo entry. If an exception occurs, the script
drops the commit so partial changes are not retained. Inspect the result, use
Undo if necessary, and save the board manually when satisfied.

The editor history labels are:

| Script | Undo/Redo entry |
| --- | --- |
| `align_component_reference_text.py` | Align component references |
| `align_connector_pin_text.py` | Align connector pin labels |
| `align_holes.py` | Align mounting holes |
| `center_and_distribute_items.py` | Center and optionally distribute footprints |
| `pcb_edge.py` | Replace board outline and ground zones |
| `resize_matching_text.py` | Resize matching board text |
| `zone_outline_perp.py` | Orthogonalize zone outlines |

`report_board_dimensions.py` is read-only and creates no history entry.

### `align_component_reference_text.py`

Positions each visible footprint reference outside its component courtyard.
It retains the reference's current side and existing position along that side:
top/bottom references move only vertically, while left/right references move
only horizontally. It applies the configured clearance and skips placements
that would collide with another courtyard on the same PCB side. Set
`IGNORE_REFERENCES` for manually positioned labels and review
`REFERENCE_OFFSET_MM`, `OTHER_COURTYARD_CLEARANCE_MM`, and
`CENTRED_REFERENCE_SIDE`. It deliberately leaves saving to PCB Editor.

### `align_connector_pin_text.py`

Matches free-standing board labels to connected connector pads and aligns them
outside the connector courtyard. Configure `CONNECTOR_REFERENCES` and the
label, clearance, proximity, row, and angle tolerances. Labels are matched by
position and orientation; unmatched or ambiguous connectors are reported and
skipped. Save the board manually after checking the result.

### `align_holes.py`

Moves four mounting-hole footprints to fixed offsets from the board edges.
Configure the four `*_HOLE_REF` values and the four `*_OFFSET_MM` distances.
The board must have a valid `Edge.Cuts` outline. Save manually after review.

### `center_and_distribute_items.py`

Centres the footprints in `REFERENCES` to the first component in that list.
`ALIGNMENT = "vertical"` aligns their vertical (Y) centres and `"horizontal"`
aligns their horizontal (X) centres. Set `DISTRIBUTE_SPACING` to `True` with
three or more references to create equal edge-to-edge gaps on the perpendicular
axis; the two outer footprints remain fixed on that axis. Save manually after
review.

### `pcb_edge.py`

Creates a rectangular `Edge.Cuts` outline using the configured size, origin,
corner radius, and line width. By default it deletes the existing outline and
replaces front/back GND zones, so carefully review
`DELETE_EXISTING_EDGE_CUTS`, `REPLACE_GROUND_ZONES`, and `GROUND_NET_NAME`
before execution. After publishing the rebuilt Edge.Cuts transaction, it runs a
blocking refill of every board zone—even when GND-zone replacement is disabled.
The refill must occur after the IPC commit because staged geometry is not yet
visible to KiCad's zone filler. Save manually after review.

### `report_board_dimensions.py`

Prints the board width and height, mounting-hole and fiducial edge offsets, and
pairwise hole spacing. IPC reports Edge.Cuts centreline geometry directly, so
no visible line-width compensation is needed. References are discovered
consecutively (`H1`, `H2`, ... and `FID1`, `FID2`, ...); discovery stops at the
first gap. This script is read-only.

### `resize_matching_text.py`

Changes the size and stroke thickness of free-standing board text whose full
text exactly matches an entry in `TEXT_STRINGS`. Configure the target strings
and the three `TEXT_*_MM` dimensions. Footprint fields and footprint graphical
text are intentionally excluded. Save manually after review.

### `zone_outline_perp.py`

Replaces every diagonal edge in a matching copper-zone outline with two
orthogonal segments, then refills the zones. Set `ZONE_NAME` to an exact zone
name; leaving it empty processes all zones. `PREFER_HORIZONTAL_FIRST` chooses
the inserted corner orientation. Only the first outer contour is retained:
zone holes/cutouts are not preserved. Save manually after careful review.

Set `DEBUG = False` in scripts that provide it to reduce console output.

## JLCPCB command-line generator

`generate_jlcpcb.py` generates fabrication and assembly outputs from a KiCad
project. Run it from the repository root with Python 3:

```sh
python3 hardware/kicad/modules/generate_jlcpcb.py led_controller
python3 hardware/kicad/modules/generate_jlcpcb.py hardware/led_controller/led_controller.kicad_pro
python3 hardware/kicad/modules/generate_jlcpcb.py --help
```

The positional argument can be a project name below `hardware/`, a project or
board file, or a directory containing exactly one `.kicad_pcb` file. The
script requires KiCad 10 or newer and `kicad-cli`; it does not use `pcbnew` or
require an open editor. A native KiCad installation and the official KiCad
Flatpak are detected automatically; use
`--kicad-cli /path/to/kicad-cli` to override detection.

Before generating output, the script runs ERC and DRC as release gates. DRC
uses `--refill-zones --save-board` to persist zone fills without Python
bindings. When the IPC environment and PCB Editor are available, it compares
the live board with the saved file and immediately rejects unsaved changes. It
also refuses to continue when a newer KiCad autosave exists, which remains the
fallback when IPC is unavailable and covers schematic autosaves. Successful
output is written to the project's `gerber/`
directory:

- Gerber and Excellon drill files
- `<project>-gerbers.zip`
- `<project>-bom.csv`
- `<project>-positions.csv`

The BOM includes populated components with a non-empty `LCSC Part #` field.

## Support modules

`kicad_ipc.py` centralizes IPC connection handling, nanometre/millimetre
geometry, board and courtyard bounds, text placement, atomic editor commits,
blocking all-zone refills, and reliable live-versus-saved board comparison.
Scripts can call `board_has_unsaved_changes(board)` before operations that
require a saved PCB. Scripts request a post-commit refill with
`editor_commit(..., refill_zones=True)`, which guarantees staged geometry is
published before KiCad rebuilds every zone. The module has no project settings
and makes no board changes when imported.

`kicad_netlist_reader.py` is the legacy KiCad generic-netlist parser used to
build the BOM, and `kicad_utils.py` contains a legacy output-file helper. They
are imported by generator code and are not executable scripts. Their legacy
API and formatting are intentionally retained for compatibility.
