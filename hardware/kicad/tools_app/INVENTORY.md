# Module inventory

This inventory records the Phase 1 review of every non-legacy Python file in
`modules/`. The executable index remains the authoritative allow-list: a file
being runnable does not make it web-accessible.

## Approved and indexed

| Module | Classification | Index state |
| --- | --- | --- |
| `report_board_dimensions.py` | User-facing, read-only IPC report | Enabled |
| `check_bom_stock.py` | User-facing, read-only report | Enabled |
| `generate_jlcpcb.py` | User-facing file generator | Enabled |
| `panelize_routed_pcb.py` | User-facing file generator | Enabled |
| `manufacture_jlcpcb.py` | User-facing file generator | Enabled |
| `align_component_edge_center.py` | User-facing, undoable IPC board editor | Enabled |
| `align_holes.py` | User-facing, undoable IPC board editor | Enabled |
| `center_and_distribute_items.py` | User-facing, undoable IPC board editor | Enabled |
| `center_components_inside_edge.py` | User-facing, undoable IPC board editor | Enabled |
| `center_edge_around_components.py` | User-facing, undoable IPC board editor | Enabled |
| `space_components.py` | User-facing, undoable IPC board editor | Enabled |
| `kill_kicad.py` | User-facing system control | Disabled |

## Reviewed but not approved

These scripts remain outside the allow-list after Phase 4 review:

- `align_connector_pin_text.py`, `component_reference_text.py`,
  `resize_matching_text.py`, and `zone_outline_perp.py` depend on broad
  heuristic matching. They need dry-run previews and stable selection reports
  before browser execution is safe.
- `align_groups.py` reconstructs routed tracks and vias from a project-specific
  group map. It needs a portable group schema and artifact-level integration
  tests before approval.
- `check_fiducials.py` and `check_motherboard_interface.py` mix analysis with
  optional repair. They need separate read-only and mutating actions so the
  displayed risk accurately describes the selected operation.
- `configure_jlcpcb_netclasses.py` changes project configuration outside the
  board-edit transaction model and needs explicit file persistence and backup
  semantics.
- `pcb_edge.py` replaces Edge.Cuts and can replace zones; `remove_items.py`
  deletes broad item classes. Both need a preview of exact deletion targets.
- `thermal_reliefs.py` and `vias.py` combine board mutation with optional
  external DRC execution. They need separate mutation and validation actions.

This list is intentionally resolved rather than a queue of implicitly approved
candidates. A future catalogue phase must address the stated safety prerequisite
before moving any item into the executable index.

`find_open_schematic.py` and `check_kicad_unsaved.py` are internal read-only
subprocess helpers. `generate_jlcpcb_panel.py` is an internal stage of the
approved manufacturing workflow. They are deliberately not separate web
actions.

## Support libraries and tests

`kicad_discovery.py`, `kicad_ipc.py`, `kicad_netlist_reader.py`,
`kicad_utils.py`, and `xlsx_reader.py` are shared libraries and are never
entry points. Files named `test_*.py` are tests. Everything under
`modules/legacy/` is legacy code. None may appear in the module index.
