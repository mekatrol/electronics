"""Align free-standing connector pin labels with their connected pads.

Execution:
    Open a board in KiCad's PCB Editor, adjust the settings below, then run
    this file from the PCB Editor scripting console with::

        import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/align_connector_pin_text.py")

Review the result in the editor and save the board manually.
"""

import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pcbnew_helpers import (  # noqa: E402
    bounding_box_center as bbox_centre,
    distance,
    get_current_board,
    is_board_text,
    iu_to_mm,
    mm_to_iu,
    text_angle_degrees,
)


# ============================================================
# User settings
# ============================================================
# Connector references to process. Add or remove references as required.
CONNECTOR_REFERENCES = ["J1", "J2", "J3", "J4", "J5", "J6"]

# Desired distance between the connector courtyard boundary and label centre.
# The pin centre is used only to align the label along the connector row. If
# this offset is too small for the complete label to clear the courtyard, the
# courtyard clearance setting below takes precedence.
LABEL_OFFSET_MM = 1
COURTYARD_CLEARANCE_MM = 0.2

# A label must be no farther than this distance beyond the outward courtyard
# boundary before it can be matched. Measuring from the courtyard makes repeat
# runs independent of connector body size.
LABEL_PROXIMITY_MM = 10.0

# Maximum initial error along the pin row. For a vertical connector this is
# the Y error; for a horizontal connector it is the X error.
INLINE_TOLERANCE_MM = 1.0

# Label baselines are expected to be parallel to the connector's pin row.
# Angles differing by 180 degrees are treated as equivalent.
ANGLE_TOLERANCE_DEGREES = 10.0

# A nominally one-dimensional row may have this much variation across its
# short axis. Larger variation means the connector is skipped as ambiguous.
PIN_ROW_TOLERANCE_MM = 0.1

DEBUG = True


# ============================================================
# Connector-specific geometry helpers
# ============================================================
def parallel_angle_error(first_degrees, second_degrees):
    """Return the smallest angle between two unoriented baselines (0..90)."""
    difference = abs(first_degrees - second_degrees) % 180.0
    return min(difference, 180.0 - difference)


# ============================================================
# Board item helpers
# ============================================================
def get_board_text_items(board):
    """Return visible, free-standing text items from the board drawings."""
    text_items = []

    for item in board.GetDrawings():
        if not is_board_text(item, ("GetTextAngle", "SetPosition")):
            continue

        if hasattr(item, "IsVisible") and not item.IsVisible():
            continue

        text_items.append(item)

    return text_items


def pad_has_track(board, pad):
    """
    Return True when a routed track or via touches the pad.

    Pins without tracks are deliberately excluded before label matching. This
    prevents a missing label from causing the next pin's label to be stolen.
    """
    for track in board.GetTracks():
        try:
            if pad.HitTest(track.GetStart()) or pad.HitTest(track.GetEnd()):
                return True
        except Exception:
            # Ignore board items which do not expose track-style endpoints.
            pass

    return False


def pad_is_connected(board, pad):
    """
    Return True unless the pad is explicitly unconnected.

    A track endpoint is direct evidence of a routed connection. Pads connected
    only by a copper zone, such as GND pads, have no touching track, so their
    net name must also be checked. KiCad gives deliberately unconnected pads
    names beginning with "unconnected-(".
    """
    if pad_has_track(board, pad):
        return True

    try:
        net_code = pad.GetNetCode()
        net_name = pad.GetNetname()
    except Exception:
        try:
            net = pad.GetNet()
            net_code = net.GetNetCode()
            net_name = net.GetNetname()
        except Exception:
            return False

    if net_code <= 0 or not net_name:
        return False

    return not net_name.lower().startswith("unconnected-(")


def connector_orientation(pads):
    """Return 'vertical' or 'horizontal' for a one-dimensional pad row."""
    positions = [pad.GetPosition() for pad in pads]
    x_span = max(position.x for position in positions) - min(
        position.x for position in positions
    )
    y_span = max(position.y for position in positions) - min(
        position.y for position in positions
    )
    tolerance = mm_to_iu(PIN_ROW_TOLERANCE_MM)

    if x_span <= tolerance and y_span > tolerance:
        return "vertical"

    if y_span <= tolerance and x_span > tolerance:
        return "horizontal"

    # A single-pad connector has no row direction and a two-dimensional pad
    # arrangement does not satisfy this script's assumptions.
    raise RuntimeError(
        "pads do not form a one-dimensional row "
        f"(X span {iu_to_mm(x_span):.3f} mm, "
        f"Y span {iu_to_mm(y_span):.3f} mm)"
    )


def board_edges(board):
    bbox = board.GetBoardEdgesBoundingBox()

    if bbox.GetWidth() <= 0 or bbox.GetHeight() <= 0:
        raise RuntimeError("the board needs a valid Edge.Cuts outline")

    return bbox.GetLeft(), bbox.GetRight(), bbox.GetTop(), bbox.GetBottom()


def outward_direction(pads, orientation, edges):
    """Choose the side of the connector nearest the corresponding board edge."""
    left_x, right_x, top_y, bottom_y = edges
    positions = [pad.GetPosition() for pad in pads]
    centre = pcbnew.VECTOR2I(
        sum(position.x for position in positions) // len(positions),
        sum(position.y for position in positions) // len(positions),
    )

    if orientation == "vertical":
        if centre.x - left_x <= right_x - centre.x:
            return -1
        return 1

    if centre.y - top_y <= bottom_y - centre.y:
        return -1
    return 1


def courtyard_bbox(footprint):
    """Return the footprint courtyard bounding box on its placed side."""
    courtyard_layer = pcbnew.B_CrtYd if footprint.IsFlipped() else pcbnew.F_CrtYd

    # Courtyard polygons are cached by KiCad. Building the cache here also
    # handles footprints that have just been edited in the current session.
    if hasattr(footprint, "BuildCourtyardCaches"):
        footprint.BuildCourtyardCaches()

    courtyard = footprint.GetCourtyard(courtyard_layer)
    bbox = courtyard.BBox()

    if bbox.GetWidth() <= 0 or bbox.GetHeight() <= 0:
        raise RuntimeError("connector has no valid courtyard")

    return bbox


def candidate_matches_pin(text, pad, orientation, direction, courtyard):
    """Check proximity, inline error, angle, and outward side for one pairing."""
    text_centre = bbox_centre(text.GetBoundingBox())
    pad_centre = pad.GetPosition()
    proximity = mm_to_iu(LABEL_PROXIMITY_MM)
    inline_tolerance = mm_to_iu(INLINE_TOLERANCE_MM)

    if orientation == "vertical":
        inline_error = abs(text_centre.y - pad_centre.y)
        outward_offset = direction * (text_centre.x - pad_centre.x)
        courtyard_edge = (
            courtyard.GetLeft() if direction < 0 else courtyard.GetRight()
        )
        boundary_distance = direction * (text_centre.x - courtyard_edge)
        expected_angle = 90.0
    else:
        inline_error = abs(text_centre.x - pad_centre.x)
        outward_offset = direction * (text_centre.y - pad_centre.y)
        courtyard_edge = (
            courtyard.GetTop() if direction < 0 else courtyard.GetBottom()
        )
        boundary_distance = direction * (text_centre.y - courtyard_edge)
        expected_angle = 0.0

    if (
        inline_error > inline_tolerance
        or outward_offset <= 0
        or boundary_distance > proximity
    ):
        return False

    angle_error = parallel_angle_error(
        text_angle_degrees(text),
        expected_angle,
    )
    return angle_error <= ANGLE_TOLERANCE_DEGREES


def match_labels(pads, text_items, orientation, direction, courtyard):
    """
    Greedily make unique pad/label pairs, starting with the best match.

    Only connected pads are supplied by the caller. Sorting all possible pairs
    by inline error first prevents a nearby label for another pin being selected.
    """
    candidates = []

    for pad in pads:
        pad_centre = pad.GetPosition()

        for text in text_items:
            if not candidate_matches_pin(
                text,
                pad,
                orientation,
                direction,
                courtyard,
            ):
                continue

            text_centre = bbox_centre(text.GetBoundingBox())

            if orientation == "vertical":
                inline_error = abs(text_centre.y - pad_centre.y)
            else:
                inline_error = abs(text_centre.x - pad_centre.x)

            candidates.append(
                (inline_error, distance(text_centre, pad_centre), pad, text)
            )

    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
    matched_pad_ids = set()
    matched_text_ids = set()
    matches = []

    for _inline_error, _distance, pad, text in candidates:
        pad_id = id(pad)
        text_id = id(text)

        if pad_id in matched_pad_ids or text_id in matched_text_ids:
            continue

        matched_pad_ids.add(pad_id)
        matched_text_ids.add(text_id)
        matches.append((pad, text))

    return matches


def target_text_centre(pad, text, orientation, direction, courtyard):
    """Align to the pin and offset the label centre from the courtyard edge."""
    pad_centre = pad.GetPosition()
    text_bbox = text.GetBoundingBox()
    offset = mm_to_iu(LABEL_OFFSET_MM)
    clearance = mm_to_iu(COURTYARD_CLEARANCE_MM)

    if orientation == "vertical":
        # The label is vertical, so its board-axis X extent controls clearance
        # from the left or right courtyard edge. GetBoundingBox() is already
        # rotated into board coordinates; using height here would incorrectly
        # make longer strings such as "GND" sit farther away than "D".
        outward_half_extent = text_bbox.GetWidth() // 2
        boundary_offset = max(offset, clearance + outward_half_extent)
        target_y = pad_centre.y

        if direction < 0:
            target_x = courtyard.GetLeft() - boundary_offset
        else:
            target_x = courtyard.GetRight() + boundary_offset

        return pcbnew.VECTOR2I(target_x, target_y)

    # The label is horizontal, so its board-axis Y extent controls clearance
    # from the top or bottom courtyard edge.
    outward_half_extent = text_bbox.GetHeight() // 2
    boundary_offset = max(offset, clearance + outward_half_extent)
    target_x = pad_centre.x

    if direction < 0:
        target_y = courtyard.GetTop() - boundary_offset
    else:
        target_y = courtyard.GetBottom() + boundary_offset

    return pcbnew.VECTOR2I(target_x, target_y)


def move_text_centre(text, target_centre):
    """Move text by its bounding-box centre, independent of text justification."""
    old_position = text.GetPosition()
    old_centre = bbox_centre(text.GetBoundingBox())
    delta_x = target_centre.x - old_centre.x
    delta_y = target_centre.y - old_centre.y
    text.SetPosition(
        pcbnew.VECTOR2I(old_position.x + delta_x, old_position.y + delta_y)
    )


def pad_number(pad):
    if hasattr(pad, "GetNumber"):
        return pad.GetNumber()
    return pad.GetPadName()


# ============================================================
# Main operation
# ============================================================
def align_connector_labels(board):
    edges = board_edges(board)
    available_text = get_board_text_items(board)
    total_moved = 0

    for reference in CONNECTOR_REFERENCES:
        footprint = board.FindFootprintByReference(reference)

        if footprint is None:
            print(f"Warning: connector {reference} was not found; skipping it.")
            continue

        pads = list(footprint.Pads())

        try:
            orientation = connector_orientation(pads)
            direction = outward_direction(pads, orientation, edges)
            courtyard = courtyard_bbox(footprint)
        except Exception as error:
            print(f"Warning: connector {reference}: {error}; skipping it.")
            continue

        connected_pads = [pad for pad in pads if pad_is_connected(board, pad)]
        matches = match_labels(
            connected_pads,
            available_text,
            orientation,
            direction,
            courtyard,
        )

        if DEBUG:
            side = (
                "left" if orientation == "vertical" and direction < 0 else
                "right" if orientation == "vertical" else
                "top" if direction < 0 else
                "bottom"
            )
            print()
            print(f"{reference}: {orientation} pin row, labels toward {side}")
            print(f"  connected pads: {len(connected_pads)} of {len(pads)}")
            print(f"  labels found: {len(matches)}")

        for pad, text in matches:
            target_centre = target_text_centre(
                pad,
                text,
                orientation,
                direction,
                courtyard,
            )
            move_text_centre(text, target_centre)
            available_text.remove(text)
            total_moved += 1

            if DEBUG:
                if orientation == "vertical":
                    courtyard_edge = (
                        courtyard.GetLeft()
                        if direction < 0
                        else courtyard.GetRight()
                    )
                    actual_offset = abs(target_centre.x - courtyard_edge)
                else:
                    courtyard_edge = (
                        courtyard.GetTop()
                        if direction < 0
                        else courtyard.GetBottom()
                    )
                    actual_offset = abs(target_centre.y - courtyard_edge)

                clearance_limited = actual_offset > mm_to_iu(LABEL_OFFSET_MM)
                limit_note = (
                    " (minimum-clearance limited)" if clearance_limited else ""
                )
                print(
                    f'  pad {pad_number(pad)} -> "{text.GetText()}" at '
                    f"({iu_to_mm(target_centre.x):.3f}, "
                    f"{iu_to_mm(target_centre.y):.3f}) mm; courtyard offset "
                    f"{iu_to_mm(actual_offset):.3f} mm{limit_note}"
                )

    return total_moved


board = get_current_board()

if board is None:
    print("Error: no board is currently open.")
else:
    try:
        moved_count = align_connector_labels(board)
        pcbnew.Refresh()
        print()
        print(f"Aligned {moved_count} connector pin label(s).")
    except Exception as error:
        print(f"Error: {error}")
