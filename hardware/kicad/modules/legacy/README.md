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

The PCB Editor scripts below have not yet been migrated: they still use the
deprecated SWIG interface and should not be used when SWIG-free operation is a
requirement. Their current instructions are retained only until the IPC
migration is complete.

## PCB Editor scripts

The following scripts use KiCad's `pcbnew` API and must run inside the PCB
Editor's scripting console. Open the board to modify, edit the script's
**User settings** section as needed, and then execute it with `runpy`:

```python
import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/legacy/SCRIPT_NAME.py")
```

Replace `SCRIPT_NAME.py` with the desired filename. If this repository is in a
different location, use that script's absolute path instead. `runpy` supplies
the script filename needed to locate the shared `pcbnew_helpers.py` module.
Assigning its return value to `_result` prevents KiCad's PyShell from printing
the complete script-globals dictionary after execution. Most scripts
modify only the board currently held in memory: inspect the result, undo it if
necessary, and explicitly save the board when satisfied. The one exception is
`align_component_reference_text.py`, which saves by default when it moves
references.

### `align_component_reference_text.py`

Positions each visible footprint reference outside its component courtyard.
It retains the reference's current side, applies the configured clearance, and
skips placements that would collide with another courtyard on the same PCB
side. Set `IGNORE_REFERENCES` for manually positioned labels and review
`REFERENCE_OFFSET_MM`, `OTHER_COURTYARD_CLEARANCE_MM`, and
`CENTRED_REFERENCE_SIDE`. Set `SAVE_BOARD_AFTER_ALIGNMENT` to `False` to
prevent automatic saving.

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

Aligns the bounding-box centres of the footprints in `REFERENCES` to the first
reference. Set `ALIGNMENT` to `"vertical"` to align Y centres or `"horizontal"`
to align X centres. When `DISTRIBUTE_SPACING` is enabled, the first and last
footprints remain fixed on the perpendicular axis and the intervening items
are arranged with equal edge-to-edge gaps. Save manually after review.

### `pcb_edge.py`

Creates a rectangular `Edge.Cuts` outline using the configured size, origin,
corner radius, and line width. By default it deletes the existing outline and
replaces front/back GND zones, so carefully review
`DELETE_EXISTING_EDGE_CUTS`, `REPLACE_GROUND_ZONES`, and `GROUND_NET_NAME`
before execution. Save manually after review.

### `report_board_dimensions.py`

Prints the board width and height, mounting-hole and fiducial edge offsets, and
pairwise hole spacing. Configure the reference prefixes and ensure
`EDGE_CUT_LINE_WIDTH_MM` matches the outline. References are discovered
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
python3 hardware/kicad/modules/legacy/generate_jlcpcb.py led_controller
python3 hardware/kicad/modules/legacy/generate_jlcpcb.py hardware/led_controller/led_controller.kicad_pro
python3 hardware/kicad/modules/legacy/generate_jlcpcb.py --help
```

The positional argument can be a project name below `hardware/`, a project or
board file, or a directory containing exactly one `.kicad_pcb` file. The
script requires KiCad 7 or newer, `kicad-cli`, and a Python environment that
can import the matching `pcbnew` module. A native KiCad installation and the
official KiCad Flatpak are detected automatically; use
`--kicad-cli /path/to/kicad-cli` to override detection.

Before generating output, the script refills and saves board zones and runs
ERC and DRC as release gates. It refuses to continue when a newer KiCad
autosave exists. Successful output is written to the project's `gerber/`
directory:

- Gerber and Excellon drill files
- `<project>-gerbers.zip`
- `<project>-bom.csv`
- `<project>-positions.csv`

The BOM includes populated components with a non-empty `LCSC Part #` field.

## Support modules

`pcbnew_helpers.py` centralizes the PCB Editor scripts' reusable KiCad API and
geometry operations. It provides unit conversions, points and vectors,
bounding-box centres, cross-version text angles and board access, board-edge
bounds, board-text detection, and basic point/segment calculations. It has no
project settings and makes no board changes when imported.

`kicad_netlist_reader.py` is the legacy KiCad generic-netlist parser used to
build the BOM, and `kicad_utils.py` contains a legacy output-file helper. They
are imported by generator code and are not executable scripts. Their legacy
API and formatting are intentionally retained for compatibility.
