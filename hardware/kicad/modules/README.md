# KiCad automation

The modules are organised by the stage of the PCB workflow in which they are
used. They support both module mode from the `hardware/kicad` directory:

```sh
.venv-kicad-ipc/bin/python -m modules.design.layout.center_footprint_between_edges --help
python3 -m modules.manufacturing.generate_jlcpcb_files --help
```

Module mode keeps imports reliable regardless of the script's subdirectory.
Direct paths also work from the parent electronics repository, matching the
existing virtual-environment workflow:

```sh
.venv-kicad-ipc/bin/python hardware/kicad/modules/design/layout/align_connector_labels.py
```

Tools that use KiCad IPC require PCB Editor to be open with the API server
enabled. Mutating IPC tools make one undoable editor transaction and leave the
board unsaved for review.

## Workflow map

### 1. Design: component and text layout

Directory: `design/layout/`

| Module | Purpose |
| --- | --- |
| `center_footprint_between_edges` | Centre one footprint between the local board-edge crossings. |
| `align_connector_labels` | Match and align silkscreen labels with connector pads. |
| `arrange_repeated_footprint_groups` | Replicate a template group's layout across repeated circuits. |
| `position_mounting_holes` | Position mounting holes from board-edge offsets. |
| `center_and_distribute_footprints` | Align selected footprints and optionally distribute their spacing. |
| `center_routed_design_in_outline` | Move footprints and routed copper together into the outline centre. |
| `center_outline_around_design` | Move the outline and board-spanning zones around a fixed design. |
| `position_motherboard_interfaces` | Lay out repeated daughter-board interfaces on a motherboard. |
| `set_footprint_spacing` | Set the centre-to-centre distance between two footprints. |
| `resize_matching_board_text` | Resize free board text that exactly matches configured dimensions. |
| `update_board_text` | Resize board text or resize and position footprint references. |

### 2. Design: board geometry and routing cleanup

Directory: `design/board/`

| Module | Purpose |
| --- | --- |
| `create_board_outline_and_zones` | Replace a rectangular Edge.Cuts outline and optional copper zones. |
| `clear_routing_and_zones` | Remove tracks, vias, and copper zones from the active board. |
| `snap_zone_outlines_to_45_and_90_degrees` | Convert zone edges to 45-degree or 90-degree paths. |

### 3. Design: fabrication-aware rules

Directory: `design/rules/`

| Module | Purpose |
| --- | --- |
| `configure_jlcpcb_routing_rules` | Configure conservative JLCPCB net-class track and via sizes. |
| `validate_fiducials` | Check fiducial construction and optionally align fiducials to a grid. |
| `validate_thermal_reliefs` | Check or apply copper-zone thermal settings. |
| `validate_vias` | Check or repair via sizes and unsupported via types. |

### 4. Inspection

Directory: `inspection/`

| Module | Purpose |
| --- | --- |
| `report_board_dimensions` | Report board size plus mounting-hole and fiducial offsets. |
| `check_board_has_unsaved_changes` | Compare the live PCB document with its saved file. |
| `validate_motherboard_interface` | Check or repair daughter-board outline and connector geometry. |

### 5. Manufacturing and procurement

Directory: `manufacturing/`

| Module | Purpose |
| --- | --- |
| `check_bom_stock` | Compare a schematic BOM with the component stock workbook. |
| `generate_jlcpcb_files` | Generate Gerbers, drills, BOM, and component-placement files. |
| `create_routed_panel` | Build a routed mouse-bite panel with rails and tooling features. |
| `generate_jlcpcb_panel_files` | Generate fabrication and assembly files for a panel without a schematic. |
| `prepare_jlcpcb_panel_package` | Run panelisation and panel export as one complete workflow. |

Typical manufacturing flow:

```text
project PCB
  -> check BOM stock
  -> validate fabrication-aware rules
  -> create routed panel (when needed)
  -> generate JLCPCB upload files
```

For a single unpanelised board:

```sh
python3 -m modules.manufacturing.generate_jlcpcb_files path/to/project.kicad_pro
```

For a complete panel package:

```sh
python3 -m modules.manufacturing.prepare_jlcpcb_panel_package path/to/project -x 4 -y 3
```

### 6. System utilities

Directory: `system/`

| Module | Purpose |
| --- | --- |
| `find_open_schematic` | Print the root schematic currently open in KiCad. |
| `stop_kicad` | Stop stuck KiCad processes and remove stale IPC sockets; unsaved work can be lost. |

## Internal code and tests

`shared/` contains reusable KiCad discovery, IPC, geometry, netlist, spreadsheet,
and motherboard-interface implementation. These files are libraries, not user
commands. `tests/` mirrors the user-facing modules it verifies.

Run all module tests from the repository directory:

```sh
python3 -m unittest discover -s modules/tests
```
