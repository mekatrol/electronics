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
| `kill_kicad.py` | User-facing system control | Disabled |

## Runnable candidates not yet approved

The following scripts edit the open PCB through KiCad IPC, but their options
are module-level constants. They remain excluded until they expose a validated
CLI or configuration object: `align_component_edge_center.py`,
`align_connector_pin_text.py`, `align_groups.py`, `align_holes.py`,
`center_and_distribute_items.py`, `center_components_inside_edge.py`,
`center_edge_around_components.py`, `check_fiducials.py`,
`check_motherboard_interface.py`, `component_reference_text.py`,
`configure_jlcpcb_netclasses.py`, `pcb_edge.py`, `remove_items.py`,
`resize_matching_text.py`, `space_components.py`, `thermal_reliefs.py`,
`vias.py`, and `zone_outline_perp.py`.

`find_open_schematic.py` and `check_kicad_unsaved.py` are internal read-only
subprocess helpers. `generate_jlcpcb_panel.py` is an internal stage of the
approved manufacturing workflow. They are deliberately not separate web
actions.

## Support libraries and tests

`kicad_discovery.py`, `kicad_ipc.py`, `kicad_netlist_reader.py`,
`kicad_utils.py`, and `xlsx_reader.py` are shared libraries and are never
entry points. Files named `test_*.py` are tests. Everything under
`modules/legacy/` is legacy code. None may appear in the module index.
