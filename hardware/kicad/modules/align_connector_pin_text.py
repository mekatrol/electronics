#!/usr/bin/env python3
"""Align connector pin labels through KiCad's supported IPC API.

Run with ``.venv-kicad-ipc/bin/python hardware/kicad/modules/align_connector_pin_text.py``.
The moved labels are one PCB Editor undo/redo transaction.
"""

from kipy.board_types import BoardText
from kipy.proto.common.types.enums_pb2 import KiCadObjectType

from kicad_ipc import (
    board_edge_bounds, box_center, box_edges, connect_board, courtyard_box,
    distance, editor_commit, footprints_by_reference, from_mm, move_text_center,
    text_box, to_mm, vector,
)


CONNECTOR_REFERENCES = ["J1", "J2", "J3", "J4", "J5", "J6"]
LABEL_OFFSET_MM = 1.5
COURTYARD_CLEARANCE_MM = 0.2
LABEL_PROXIMITY_MM = 10.0
INLINE_TOLERANCE_MM = 1.0
ANGLE_TOLERANCE_DEGREES = 10.0
PIN_ROW_TOLERANCE_MM = 0.1
DEBUG = True


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


def pad_connected(board, pad):
    """Ask KiCad whether a pad has connected track, arc, or via copper."""
    types = [
        KiCadObjectType.KOT_PCB_TRACE,
        KiCadObjectType.KOT_PCB_ARC,
        KiCadObjectType.KOT_PCB_VIA,
    ]
    return bool(board.get_connected_items(pad, types=types))


def candidate(text, pad, row_orientation, direction, courtyard, client):
    """Return positional match metrics, or ``None`` when a label is unsuitable."""
    center = box_center(text_box(client, text))
    c_left, c_right, c_top, c_bottom = box_edges(courtyard)
    proximity = from_mm(LABEL_PROXIMITY_MM)
    inline_limit = from_mm(INLINE_TOLERANCE_MM)
    expected_angle = 90.0 if row_orientation == "vertical" else 0.0
    if parallel_angle_error(text.attributes.angle, expected_angle) > ANGLE_TOLERANCE_DEGREES:
        return None
    if row_orientation == "vertical":
        outward = c_left - center.x if direction < 0 else center.x - c_right
        inline = abs(center.y - pad.position.y)
    else:
        outward = c_top - center.y if direction < 0 else center.y - c_bottom
        inline = abs(center.x - pad.position.x)
    if not 0 <= outward <= proximity or inline > inline_limit:
        return None
    return inline, distance(center, pad.position)


def target_center(client, text, pad, row_orientation, direction, courtyard):
    """Place label centre beyond the courtyard with sufficient rendered clearance."""
    bounds = text_box(client, text)
    left, right, top, bottom = box_edges(courtyard)
    t_left, t_right, t_top, t_bottom = box_edges(bounds)
    offset = from_mm(LABEL_OFFSET_MM)
    clearance = from_mm(COURTYARD_CLEARANCE_MM)
    if row_orientation == "vertical":
        half = (t_right - t_left) // 2
        normal = max(offset, half + clearance)
        return vector((left - normal if direction < 0 else right + normal), pad.position.y)
    half = (t_bottom - t_top) // 2
    normal = max(offset, half + clearance)
    return vector(pad.position.x, (top - normal if direction < 0 else bottom + normal))


def main():
    """Match and move connector labels in one undoable transaction."""
    client, board = connect_board()
    footprints = footprints_by_reference(board)
    available = [text for text in board.get_text() if isinstance(text, BoardText)]
    edges = board_edge_bounds(board)
    changed = []

    with editor_commit(board, "Align connector pin labels"):
        for reference in CONNECTOR_REFERENCES:
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
            for pad in (pad for pad in pads if pad_connected(board, pad)):
                matches = [
                    (candidate(text, pad, row, direction, courtyard, client), text)
                    for text in available
                ]
                matches = [(metric, text) for metric, text in matches if metric is not None]
                if not matches:
                    continue
                _metric, text = min(matches, key=lambda item: item[0])
                destination = target_center(client, text, pad, row, direction, courtyard)
                move_text_center(client, text, destination)
                changed.append(text)
                available.remove(text)
                if DEBUG:
                    print(
                        f'{reference} pad {pad.number} -> "{text.value}" at '
                        f"({to_mm(destination.x):.3f}, "
                        f"{to_mm(destination.y):.3f}) mm"
                    )
        board.update_items(changed)

    print(f"Aligned {len(changed)} connector label(s) (undo: Align connector pin labels).")


if __name__ == "__main__":
    main()
