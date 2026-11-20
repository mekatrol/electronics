# Module inventory

The user-facing module catalogue is organised by workflow under `modules/`.
The executable index remains the authoritative web-application allow-list.

## Approved and indexed

| Module | Classification | Index state |
| --- | --- | --- |
| `inspection/report_board_dimensions.py` | Read-only IPC report | Enabled |
| `manufacturing/check_bom_stock.py` | Read-only procurement report | Enabled |
| `manufacturing/generate_jlcpcb_files.py` | Fabrication/assembly file generator | Enabled |
| `manufacturing/create_routed_panel.py` | Routed panel generator | Enabled |
| `manufacturing/prepare_jlcpcb_panel_package.py` | Complete panel manufacturing workflow | Enabled |
| `design/layout/center_footprint_between_edges.py` | Undoable layout editor | Enabled |
| `design/layout/position_mounting_holes.py` | Undoable layout editor | Enabled |
| `design/layout/center_and_distribute_footprints.py` | Undoable layout editor | Enabled |
| `design/layout/center_routed_design_in_outline.py` | Undoable whole-design editor | Enabled |
| `design/layout/center_outline_around_design.py` | Undoable outline editor | Enabled |
| `design/layout/set_footprint_spacing.py` | Undoable layout editor | Enabled |
| `system/stop_kicad.py` | External process control | Disabled |

## Reviewed but not indexed

The remaining scripts are intentionally outside the browser allow-list:

- `design/layout/align_connector_labels.py`,
  `design/layout/update_board_text.py`,
  `design/layout/resize_matching_board_text.py`, and
  `design/board/snap_zone_outlines_to_45_and_90_degrees.py` use configurable matching
  or geometry heuristics and need stable previews before browser execution.
- `design/layout/arrange_repeated_footprint_groups.py` uses a project-specific
  group map and reconstructs routed tracks and vias.
- `design/rules/validate_fiducials.py` and
  `inspection/validate_motherboard_interface.py` combine checking with optional
  repair and therefore cannot have one fixed browser risk classification.
- `design/rules/configure_jlcpcb_routing_rules.py` persists project settings.
- `design/board/create_board_outline_and_zones.py` and
  `design/board/clear_routing_and_zones.py` replace broad classes of geometry.
- `design/rules/validate_thermal_reliefs.py` and
  `design/rules/validate_vias.py` combine optional mutation with DRC execution.

`system/find_open_schematic.py` and
`inspection/check_board_has_unsaved_changes.py` are internal read-only helpers.
`manufacturing/generate_jlcpcb_panel_files.py` is an internal stage of the
complete manufacturing workflow.

## Libraries and tests

Everything in `shared/` is reusable implementation code and never an entry
point. Everything in `tests/` is test code. Neither directory may appear in the
executable index.
