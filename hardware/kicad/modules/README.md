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
| `align_groups.py` | Align repeated component groups |
| `align_holes.py` | Align mounting holes |
| `center_and_distribute_items.py` | Center and optionally distribute footprints |
| `center_components_inside_edge.py` | Center all footprints inside board outline |
| `center_edge_around_components.py` | Center Edge.Cuts around all components |
| `check_fiducials.py` | Align and check fiducials |
| `check_motherboard_interface.py` | Fix motherboard mechanical interface |
| `pcb_edge.py` | Replace board outline and ground zones |
| `remove_tracks_and_vias.py` | Remove all tracks, vias, and zones |
| `resize_matching_text.py` | Resize matching board text |
| `thermal_reliefs.py` | Set zone thermal reliefs |
| `vias.py` | Validate or set JLCPCB-oriented vias |
| `zone_outline_perp.py` | Orthogonalize zone outlines |

`report_board_dimensions.py` is read-only and creates no history entry.

### `check_motherboard_interface.py`

Validates the daughter board currently open in PCB Editor against the shared
motherboard mechanical interface. It checks the 25 x 42 mm outline and the J1,
J2, H1, and H2 offsets from the top, left, and right edges using pin/hole
centers. J1 and optional J2 are measured from the center of their top-left pin;
H1 and H2 are measured from their hole centers. A missing J2 is reported but
does not fail validation. J1 and J2 are also explicitly checked for horizontal
centering using the center of their complete pin group. The default
`FIX_MOTHERBOARD_INTERFACE = False` only reports mismatches. Set it to
`True` to replace a wrongly sized outline and move the three footprints in one
undoable transaction. The active board remains unsaved for review, and future
daughter boards need only be opened in PCB Editor before running the script.

### `thermal_reliefs.py`

Checks every GND and +5V copper zone against conservative JLCPCB 2-layer, 1 oz
zone settings: 0.20 mm clearance, 0.25 mm minimum width, thermal pad connections,
0.25 mm thermal gap, 0.30 mm spoke width, no corner smoothing, and unconditional
island removal. Numeric values already above these minimums pass in check mode.
Set the script's `SET_RELIEFS` flag to `True` to write the exact configured
values to every matching zone in one undoable transaction and refill all zones.
The setter then runs KiCad DRC on an isolated copy of the updated live board and
reports every violation and unconnected item. Changes remain unsaved for review.

### `vias.py`

Validates every board via against conservative, standard-cost JLCPCB rigid-PCB
settings: a 0.30 mm minimum drill, 0.50 mm minimum diameter, 0.10 mm minimum
annular ring per side, and through-vias only. Validation is the default and
does not modify the board. Set the script's `SET_VIAS` flag to `True` to enlarge
only non-compliant vias and convert unsupported via types in one undoable
transaction. Larger existing vias are preserved and changes remain unsaved for
review. After setting, KiCad DRC runs on an isolated copy of the updated live
board and reports every violation and unconnected item.

### `remove_tracks_and_vias.py`

Removes every copper track (straight or curved), via, and zone on every layer
from the board active in PCB Editor. The removal is one undoable transaction;
the script leaves the board unsaved for inspection.

### `panelize_routed_pcb.py`

Creates a routed mouse-bite panel while preserving the source PCB outline,
including non-rectangular geometry:

```sh
python kicad/modules/panelize_routed_pcb.py power_rail_mosfet_switch/power_rail_mosfet_switch.kicad_pcb -x 4 -y 3 --gap 2
```

The routing gap is configurable but must be at least 2 mm. Defaults follow
JLCPCB's published mouse-bite guidance: 5 mm tabs on a pair of opposite edges
that are long enough to contain them (top/bottom when the PCB width permits,
otherwise left/right),
five 0.6 mm NPTH holes per tab with
0.4 mm between hole edges (1.0 mm pitch), 5 mm rails, four 1 mm library fiducials whose
centres are 3.85 mm from the panel edges, and four 2 mm NPTH tooling holes in
the rail corners. Use `--tab-width`,
`--mouse-bite-diameter`, and `--mouse-bite-clearance` only within the limits
printed by `--help`. Order it as customer-supplied panelization and have JLCPCB
review the routed tab layout before production. The NPTH mouse-bite holes do
not require the **Castellated Holes** option. Select that option only if the
finished source PCB itself has plated half-holes along an edge.

The script constructs the panel substrate from the preserved source outlines,
solid breakaway bridges, and process rails. It then emits one closed exterior
`Edge.Cuts` contour plus closed internal cutouts for every routed channel.
The configurable routing gap is also placed between the PCB array and the
rails, so a 5 mm rail remains a full 5 mm after routing. Any DRC violation,
including `invalid_outline`, or any unconnected item rejects the output.

Each copied footprint reference receives a panel-position suffix (for example,
`D1_X2Y1`) so BOM and pick-and-place rows identify a unique component across
the complete panel. Net names receive their own matching position suffix.

After generation, the script prints a self-contained validation summary with
the source and output paths, array and finished dimensions, routing and rail
geometry, tab and mouse-bite counts, fiducial and tooling-hole construction,
KiCad DRC result, source-integrity result, and ordering intent. Provide this
summary together with the generated panel when requesting an independent
fabrication review.

The complete generated panel is centred on the drawing sheet inherited from
the source board. This changes only its absolute editor coordinates; panel
dimensions, clearances, Gerbers, and drill geometry remain unchanged.

Closed-cutout construction uses the GEOS geometry library (`libgeos_c`). The
script stops with an explicit error if GEOS is unavailable rather than emitting
an invalid or ambiguous routed outline.

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

### `align_groups.py`

Uses the configured OP1 footprint list as a layout template for seven repeated
output groups. It copies each corresponding footprint's relative position and
rotation together with its Reference and Value label positions and text
angles, then places OP2 through OP8 to the right of OP1 in one top-aligned row.
Each destination keeps its own label text. `GROUP_SPACING_MM` controls the clear
gap between adjacent group bounding boxes. `CENTER_GROUPS_HORIZONTALLY` defaults
to `True` and performs a final whole-row move, including OP1, which centres the
combined physical group bounds horizontally within `Edge.Cuts`; disable it to
leave OP1's X position fixed. The explicit `GROUPS` mapping prevents schematic
re-annotation from silently associating unlike components. All copied groups
are updated in one undoable transaction. Tracks (including curved tracks) that
form an endpoint-connected route between two or more OP1 components, without
touching a component outside OP1, are copied with their complete properties
and mapped to each destination's corresponding pad net. Existing routes
internal to OP2--OP8 are replaced; unrelated tracks are left alone. Vias in
those routes are treated as layer-spanning connections and are copied or
replaced when connected to any group component, including on a route that
touches only one component. Localized copper zones enclosing those vias are
also copied, while board-spanning zones are left untouched. The board is left
unsaved for inspection.

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

### `center_components_inside_edge.py`

Centres the combined bounds of every footprint on the area centroid of the
actual Edge.Cuts polygon. All footprints receive the same translation, so their
relative layout remains unchanged. All tracks and vias receive the same
translation, preserving the routed connections, including curved tracks.
Concave and curved outlines and internal cut-outs are supported.
Reference/value text is excluded from component bounds by default; set
`INCLUDE_TEXT = True` to include it. The move is one undo entry; run DRC and
save manually after review.

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
corner radius, and line width. Set `CENTRE_ON_PAGE` to place the centre of the
PCB at the centre of the board's configured drawing page; this overrides both
`KEEP_CENTRE` and the configured origin. By default it deletes the existing
outline and creates a GND zone on every enabled copper layer. Set
`FILL_ZONE_NAMES` in
physical stack order (`F.Cu`, inner layers, `B.Cu`) to use other board nets;
missing entries default to GND and extra entries are ignored. Carefully review
`DELETE_EXISTING_EDGE_CUTS`, `REPLACE_GROUND_ZONES`, and `FILL_ZONE_NAMES`
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
output is written to the project's ignored `manufacture/`
directory:

- Gerber and Excellon drill files
- `<project>-gerbers.zip`
- `<project>-bom.csv`
- `<project>-cpl.csv`

`User.Drawings` is exported as `<project>-User_Drawings.gbr` and included in
the Gerber ZIP when a project contains deliberate documentation geometry.

The BOM includes populated components with a non-empty `LCSC Part #` field.

### Generated-panel PCB-only exporter

`generate_jlcpcb_panel.py` is the separate exporter for generated panelized PCB
files. It intentionally requires a filename containing `panel`, needs only a
`.kicad_pcb`, and performs no schematic ERC/parity check:

```powershell
.\.venv-kicad-ipc\Scripts\python.exe kicad\modules\generate_jlcpcb_panel.py `
  power_rail_mosfet_switch\power_rail_mosfet_switch_routed_panel_4x3.kicad_pcb
```

Output goes to the project's `manufacture/` directory and includes Gerbers,
Excellon drills, a JLCPCB BOM, a JLCPCB CPL CSV, and
`<panel-name>-gerbers.zip`. The BOM is reconstructed from the `Value`,
`Reference`, and `LCSC Part #` properties embedded in each copied footprint;
components marked `board_only` or `exclude_from_bom` and parts whose LCSC field
is blank or `N/A` are omitted. Every BOM designator must appear in the CPL
file. Routed-panel DRC requires closed routing cutouts with no violations or
unconnected items. The original `generate_jlcpcb.py` schematic/project workflow
is unchanged.

### One-command panel manufacturing

`manufacture_jlcpcb.py` runs routed panelization followed by the panel JLCPCB
exporter. Pass only the project directory name and array dimensions; the board
must have the same basename as its directory:

```sh
python3 hardware/kicad/modules/manufacture_jlcpcb.py mek-smd-mag-led -x 4 -y 3
```

The command writes the generated panel PCB, Gerbers, separate plated and NPTH
drill files, fabrication ZIP, BOM, and CPL CSV together under
`hardware/<project>/manufacture/`. Re-running it replaces the matching panel
and release files. ZIP creation is scoped to the selected panel filename, so
outputs for another array size cannot be included accidentally.

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
