#!/usr/bin/env python3
"""Align connector pin labels through KiCad's supported IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/align_connector_pin_text.py``.
The moved labels are one PCB Editor undo/redo transaction.
"""

from kipy.board_types import BoardText
from kipy.proto.common.types.enums_pb2 import KiCadObjectType

from kicad_ipc import (
    BoardLayer, board_edge_bounds, box_center, box_edges, connect_board,
    courtyard_box, distance, editor_commit, footprints_by_reference, from_mm,
    move_text_center, text_box, to_mm, vector,
)


CONNECTOR_REFERENCES = ["J1", "J2", "J3", "J4", "J5", "J6", "J7"]
FRONT_LABEL_OFFSET_MM = 1.5
FRONT_COURTYARD_CLEARANCE_MM = 0.1
FRONT_LABEL_PROXIMITY_MM = 10.0
FRONT_INLINE_TOLERANCE_MM = 1.0
BACK_LABEL_OFFSET_MM = 1.0
BACK_PIN_CLEARANCE_MM = 2.5
BACK_LABEL_PROXIMITY_MM = 10.0
BACK_INLINE_TOLERANCE_MM = 1.0
ANGLE_TOLERANCE_DEGREES = 10.0
PIN_ROW_TOLERANCE_MM = 0.1
SILKSCREEN_LAYERS = {BoardLayer.BL_F_SilkS, BoardLayer.BL_B_SilkS}


def layer_name(layer):
    """Return a concise display name for a supported silkscreen layer."""
    return "F.SilkS" if layer == BoardLayer.BL_F_SilkS else "B.SilkS"


def parallel_angle_error(first, second):
    """Return the difference between two unoriented text baselines."""
    difference = abs(first - second) % 180.0
    return min(difference, 180.0 - difference)


def orientation(pads):
    """Classify a one-dimensional pad row as horizontal or vertical."""
    if not pads:
        raise RuntimeError("connector has no pads")
    x_span = max(p.position.x for p in pads) - min(p.position.x for p in pads)
    y_span = max(p.position.y for p in pads) - min(p.position.y for p in pads)
    tolerance = from_mm(PIN_ROW_TOLERANCE_MM)
    if x_span <= tolerance < y_span:
        return "vertical"
    if y_span <= tolerance < x_span:
        return "horizontal"
    raise RuntimeError(f"ambiguous pad row ({to_mm(x_span):.3f} x {to_mm(y_span):.3f} mm)")


def outward_direction(pads, row_orientation, edges):
    """Return -1 for left/top or +1 for right/bottom, whichever is nearer."""
    left, right, top, bottom = edges
    x = sum(p.position.x for p in pads) // len(pads)
    y = sum(p.position.y for p in pads) // len(pads)
    if row_orientation == "vertical":
        return -1 if x - left <= right - x else 1
    return -1 if y - top <= bottom - y else 1


def copper_types():
    """Return copper object types which make a connector net in use."""
    return [
        KiCadObjectType.KOT_PCB_TRACE,
        KiCadObjectType.KOT_PCB_ARC,
        KiCadObjectType.KOT_PCB_VIA,
        KiCadObjectType.KOT_PCB_ZONE,
    ]


def routed_net_names(board):
    """Return net names represented by routed copper or a copper zone."""
    return {
        item.net.name
        for item in board.get_items(types=copper_types())
        if getattr(item, "net", None) is not None and item.net.name
    }


def pad_connected(board, pad, routed_nets):
    """Return whether a pad is directly connected or belongs to a routed net."""
    return bool(board.get_connected_items(pad, types=copper_types())) or (
        pad.net.name in routed_nets
    )


def assess_candidate(text, pad, row_orientation, direction, courtyard, client):
    """Return a positional match metric and an explanation of the outcome."""
    center = box_center(text_box(client, text))
    c_left, c_right, c_top, c_bottom = box_edges(courtyard)
    back = text.layer == BoardLayer.BL_B_SilkS
    proximity_mm = BACK_LABEL_PROXIMITY_MM if back else FRONT_LABEL_PROXIMITY_MM
    inline_tolerance_mm = (
        BACK_INLINE_TOLERANCE_MM if back else FRONT_INLINE_TOLERANCE_MM
    )
    proximity = from_mm(proximity_mm)
    inline_limit = from_mm(inline_tolerance_mm)
    if row_orientation == "vertical":
        if back:
            outward = (
                pad.position.x - center.x
                if direction < 0
                else center.x - pad.position.x
            )
        else:
            outward = c_left - center.x if direction < 0 else center.x - c_right
        inline = abs(center.y - pad.position.y)
    else:
        if back:
            outward = (
                pad.position.y - center.y
                if direction < 0
                else center.y - pad.position.y
            )
        else:
            outward = c_top - center.y if direction < 0 else center.y - c_bottom
        inline = abs(center.x - pad.position.x)
    if outward < 0 and not text.attributes.mirrored:
        return None, "overlaps or is inside the connector courtyard"
    if outward < -proximity:
        reference = "pin" if back else "courtyard"
        return None, (
            f"mirrored text is too far inside the {reference} "
            f"({to_mm(-outward):.3f} mm; limit {proximity_mm:.3f} mm)"
        )
    if outward > proximity:
        reference = "pin" if back else "courtyard"
        return None, (
            f"too far outside the {reference} ({to_mm(outward):.3f} mm; "
            f"limit {proximity_mm:.3f} mm)"
        )
    if inline > inline_limit:
        return None, (
            f"not in line with the pad ({to_mm(inline):.3f} mm; "
            f"limit {inline_tolerance_mm:.3f} mm)"
        )
    # Pin labels may be written either horizontally or vertically. Angles 180
    # degrees apart describe the same unoriented baseline.
    angle_error = min(
        parallel_angle_error(text.attributes.angle, 0.0),
        parallel_angle_error(text.attributes.angle, 90.0),
    )
    if angle_error > ANGLE_TOLERANCE_DEGREES:
        return None, (
            f"diagonal angle ({text.attributes.angle:.1f} degrees; expected "
            f"a horizontal or vertical baseline +/- {ANGLE_TOLERANCE_DEGREES:.1f})"
        )
    return (inline, distance(center, pad.position)), "eligible"


def target_center(client, text, pad, row_orientation, direction, courtyard):
    """Return a front courtyard-based or back pin-based label centre."""
    bounds = text_box(client, text)
    left, right, top, bottom = box_edges(courtyard)
    t_left, t_right, t_top, t_bottom = box_edges(bounds)
    back = text.layer == BoardLayer.BL_B_SilkS
    offset = from_mm(BACK_LABEL_OFFSET_MM if back else FRONT_LABEL_OFFSET_MM)
    clearance = from_mm(
        BACK_PIN_CLEARANCE_MM if back else FRONT_COURTYARD_CLEARANCE_MM
    )
    if row_orientation == "vertical":
        half = (t_right - t_left) // 2
        normal = max(offset, half + clearance)
        if back:
            x = pad.position.x + direction * normal
        else:
            x = left - normal if direction < 0 else right + normal
        return vector(x, pad.position.y)
    half = (t_bottom - t_top) // 2
    normal = max(offset, half + clearance)
    if back:
        y = pad.position.y + direction * normal
    else:
        y = top - normal if direction < 0 else bottom + normal
    return vector(pad.position.x, y)


def main():
    """Match and move connector labels in one undoable transaction."""
    client, board = connect_board()
    footprints = footprints_by_reference(board)
    available = [
        text
        for text in board.get_text()
        if isinstance(text, BoardText) and text.layer in SILKSCREEN_LAYERS
    ]
    routed_nets = routed_net_names(board)
    edges = board_edge_bounds(board)
    changed = []

    with editor_commit(board, "Align connector pin labels"):
        for reference in CONNECTOR_REFERENCES:
            print(f"\n{reference}:")
            footprint = footprints.get(reference)
            if footprint is None:
                print(f"Warning: connector {reference} not found; skipped")
                continue
            pads = list(footprint.definition.pads)
            try:
                row = orientation(pads)
                direction = outward_direction(pads, row, edges)
                courtyard = courtyard_box(footprint)
            except RuntimeError as error:
                print(f"Warning: {reference}: {error}; skipped")
                continue
            for pad in pads:
                if not pad_connected(board, pad, routed_nets):
                    print(f"  pad {pad.number}: skipped (no connected copper or zone)")
                    continue
                assessments = [
                    (
                        *assess_candidate(
                            text, pad, row, direction, courtyard, client
                        ),
                        text,
                    )
                    for text in available
                ]
                matches_by_layer = {}
                for metric, _reason, text in assessments:
                    if metric is not None:
                        matches_by_layer.setdefault(text.layer, []).append(
                            (metric, text)
                        )
                if not matches_by_layer:
                    print(f"  pad {pad.number}: no suitable text")
                    for _metric, reason, text in assessments:
                        print(
                            f'    [{layer_name(text.layer)}] "{text.value}": '
                            f"skipped ({reason})"
                        )
                    continue
                selected = {}
                for layer, matches in matches_by_layer.items():
                    _metric, text = min(matches, key=lambda item: item[0])
                    selected[layer] = text
                    destination = target_center(
                        client, text, pad, row, direction, courtyard
                    )
                    move_text_center(client, text, destination)
                    changed.append(text)
                    available.remove(text)
                    print(
                        f'  pad {pad.number} [{layer_name(layer)}]: aligned '
                        f'"{text.value}" to ({to_mm(destination.x):.3f}, '
                        f"{to_mm(destination.y):.3f}) mm"
                    )
                for metric, reason, assessed_text in assessments:
                    if selected.get(assessed_text.layer) is assessed_text:
                        continue
                    if metric is not None:
                        chosen = selected[assessed_text.layer]
                        reason = f"eligible, but {chosen.value!r} was the closer match"
                    print(
                        f'    [{layer_name(assessed_text.layer)}] '
                        f'"{assessed_text.value}": skipped ({reason})'
                    )
        board.update_items(changed)

    print(f"Aligned {len(changed)} connector label(s) (undo: Align connector pin labels).")


if __name__ == "__main__":
    main()
