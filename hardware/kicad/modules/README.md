# KiCad scripts

This directory contains PCB Editor automation scripts, a command-line
manufacturing-file generator, and its support modules.

## KiCad IPC API setup

KiCad's SWIG-based `pcbnew` Python interface is deprecated and is scheduled for
removal in KiCad 11. New and migrated automation should use KiCad's official
`kicad-python` (`kipy`) IPC client. The IPC client runs in an external Python
process and communicates with a running KiCad application.

### Enable the API server

In KiCad 10:

1. Start KiCad and select **Preferences → Preferences…**.
2. Select **Plugins** in the left pane.
3. Check **Enable API server**, then select **OK**.
4. Close and restart KiCad after changing the option.
5. Open the required `.kicad_pcb` in PCB Editor and leave PCB Editor running
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

The following scripts use the supported `kipy` IPC API. After completing the
setup above, edit the script's **User settings** section as needed, then run it
from a terminal at the repository root:

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
| `component_reference_text.py` | Update component references |
| `align_connector_pin_text.py` | Align connector pin labels |
| `align_holes.py` | Align mounting holes |
| `center_and_distribute_items.py` | Center and optionally distribute footprints |
| `center_edge_around_components.py` | Center Edge.Cuts around all components |
| `check_fiducials.py` | Align and check fiducials |
| `pcb_edge.py` | Replace board outline and ground zones |
| `resize_matching_text.py` | Resize matching board text |
| `zone_outline_perp.py` | Orthogonalize zone outlines |

`report_board_dimensions.py` is read-only and creates no history entry.

### `panelize_pcb.py`

Creates a separate V-scored KiCad 10 panel from a saved `.kicad_pcb`; it never
opens the source for writing. Configure the grid on the command line:

```sh
python kicad/modules/panelize_pcb.py power_rail_mosfet_switch/power_rail_mosfet_switch.kicad_pcb -x 4 -y 3
```

The output defaults to `<board>_panel_<X>x<Y>.kicad_pcb`. It has one continuous
rectangular `Edge.Cuts` outline, a 5 mm rail on all four sides, a 2 mm scrap gap
between boards, three asymmetric global 1 mm copper / 2 mm mask fiducials on
the rail loaded directly from KiCad 10's installed
`Fiducial:Fiducial_1mm_Mask2mm` library footprint, and V-score lines on
`User.Drawings` at both sides of every PCB row
and column. The gap prevents edge copper such as castellations from touching
the next PCB. Each PCB copy receives unique UUIDs and private net
names to prevent cross-panel ratsnest connections. The script asks KiCad 10's
`kicad-cli pcb drc --refill-zones --save-board` to parse and normalize the
generated board and persist fresh zone fills; pass `--no-kicad-check` only when
the CLI is unavailable.

V-scoring makes each finished PCB the rectangular envelope of its original
outline. In particular, rounded corners become square. Use routed tabs instead
if the finished PCB must retain a non-rectangular outline. Always confirm the
score lines, gap, rail width, fiducial construction, and panel limits with the
PCB fabricator before ordering. Use `--gap 0` only for designs whose board-edge
copper and fabrication process explicitly permit directly abutted PCBs.
The standard footprint library is auto-detected; use `--fiducial-footprint`
only for a nonstandard KiCad installation.

### `panelize_routed_pcb.py`

Creates a routed mouse-bite panel for castellated or non-rectangular boards,
preserving the source `Edge.Cuts` so the router crosses castellated drills:

```sh
python kicad/modules/panelize_routed_pcb.py power_rail_mosfet_switch/power_rail_mosfet_switch.kicad_pcb -x 4 -y 3 --gap 2
```

The routing gap is configurable but must be at least 2 mm. Defaults follow
JLCPCB's published mouse-bite guidance: 5 mm tabs on the non-castellated top
and bottom edges, 0.6 mm NPTH holes with
0.25 mm between hole edges, 5 mm rails, four 1 mm library fiducials whose
centres are 3.85 mm from the panel edges, and four 2 mm NPTH tooling holes in
the rail corners. Use `--tab-width`,
`--mouse-bite-diameter`, and `--mouse-bite-clearance` only within the limits
printed by `--help`. Select **Castellated Holes** and customer-supplied
panelization when ordering, and have JLCPCB review the routed tab layout before
production.

KiCad internally identifies each deliberate opening in a routed outline as
`invalid_outline`; these openings are the solid breakaway tabs, not accidental
geometry errors. The script captures those expected markers and reports them
as validated routing features rather than DRC violations. Any other DRC
violation or any unconnected item rejects and removes the output.

### `component_reference_text.py`

Positions each visible footprint reference outside its component courtyard.
It independently replaces matching label widths and heights using
`MATCH_WIDTH_MM`/`NEW_WIDTH_MM` and `MATCH_HEIGHT_MM`/`NEW_HEIGHT_MM`; set both
values for an axis to `None` to leave that dimension unchanged. For example,
`MATCH_HEIGHT_MM = 1.0` and `NEW_HEIGHT_MM = 0.8` changes only labels whose
current height is 1 mm. Width matching is independent of height matching.
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

### `center_edge_around_components.py`

Centres the area centroid of the actual Edge.Cuts polygon around the bounds of
all footprints. Concave and curved outlines and internal cut-outs are supported.
The routed design remains fixed, so pads cannot be separated from tracks or
vias. Board-spanning zones move with the outline and are refilled; localized
zones stay fixed. Reference/value text is excluded from the component bounds by
default; set `INCLUDE_TEXT = True` to include it. The entire outline move is one
undo entry; save manually after review.

### `check_fiducials.py`

Checks that every PCB side containing populated components has at least three
fiducials, and verifies each fiducial's copper and solder-mask opening against
the configured dimensions. It snaps fiducial coordinates to the nearest 0.5 mm
grid (configurable with `POSITION_GRID_MM`) only when the resulting clearance
envelope remains inside Edge.Cuts and clear of other footprints, tracks, and
vias. Unsafe moves are reported and skipped. The standard 1 mm copper / 2 mm
mask opening uses a 0.5 mm solder-mask margin on every side. Run PCB Editor's
full DRC after review and save the board manually when satisfied. After the
undoable position transaction is published, the script performs a blocking
refill of every copper zone through the shared IPC utility.

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

`User.Drawings` is exported as `<project>-User_Drawings.gbr` and included in
the Gerber ZIP. Panel files produced by `panelize_pcb.py` use this Gerber for
their V-score centre lines. Explicitly identify it as the V-score drawing in
the fabrication order notes; it is intentionally separate from `Edge.Cuts`.

The BOM includes populated components with a non-empty `LCSC Part #` field.

### Generated-panel PCB-only exporter

`generate_jlcpcb_panel.py` is the separate exporter for generated panelized PCB
files. It intentionally requires a filename containing `panel`, needs only a
`.kicad_pcb`, performs no schematic ERC/parity check, and produces no BOM:

```powershell
.\.venv-kicad-ipc\Scripts\python.exe kicad\modules\generate_jlcpcb_panel.py `
  power_rail_mosfet_switch\power_rail_mosfet_switch_routed_panel_4x3.kicad_pcb
```

Output goes to `<panel-name>-jlcpcb/` beside the panel and includes Gerbers,
Excellon drills, a positions CSV, and `<panel-name>-gerbers.zip`. Routed-panel
DRC permits only the intentional open-outline markers at mouse-bite tabs; any
other violation or unconnected item stops export. The original
`generate_jlcpcb.py` schematic/project workflow is unchanged.

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
