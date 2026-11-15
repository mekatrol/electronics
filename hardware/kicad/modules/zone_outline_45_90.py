"""Snap zone-outline edges to 45-degree or axis-aligned paths via KiCad IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/zone_outline_45_90.py

Each run is one PCB Editor undo/redo transaction.  The first outer contour is
rebuilt and existing zone holes/cutouts are deliberately not preserved.
"""

import math

from kicad_ipc import (
    connect_board,
    editor_commit,
    from_mm,
    same_point,
    to_mm,
    vector,
)
from kipy.geometry import ArcStartMidEnd, PolygonWithHoles, PolyLine, PolyLineNode
from kipy.proto.board.board_types_pb2 import ZoneType

# Every keep-out/rule-area zone is updated, regardless of its name or layers.
# Copper zones are selected by electrical net rather than their optional zone
# display name. Every zone on every layer assigned to one of these nets is
# updated. Keep this list narrow because sending unrelated copper zones through
# KiCad IPC can rewrite metadata such as net assignments. Leave empty to update
# keep-outs only.
COPPER_NET_NAMES = ["VIN"]
# Edges in this inclusive range are kept as diagonal paths, but made exactly
# 45 degrees. Shallower and steeper edges are replaced by perpendicular paths.
MIN_DIAGONAL_ANGLE_DEGREES = 25.0
MAX_DIAGONAL_ANGLE_DEGREES = 65.0
# Applied after the existing 45/90-degree adjustment. A value less than or
# equal to zero preserves the current square-corner behaviour exactly.
CORNER_RADIUS_MM = 0.5
IGNORE_CORNER_RADIUS = False
DEBUG = True


def zone_kind(zone):
    """Return a human-readable zone kind for diagnostics."""
    return "keep-out" if zone.type == ZoneType.ZT_RULE_AREA else "copper zone"


def zone_net_name(zone):
    """Return a zone's net name, or an empty string when it has no net."""
    net = zone.net
    return net.name if net is not None else ""


def compress(points):
    """Remove adjacent duplicates and a repeated closing vertex."""
    result = []
    for point in points:
        if not result or not same_point(result[-1], point):
            result.append(vector(point.x, point.y))
    if len(result) > 1 and same_point(result[0], result[-1]):
        result.pop()
    return result


def line_intersection(first_start, first_end, second_start, second_end):
    """Return the intersection of two infinite lines in IPC coordinates."""
    first_x = first_end.x - first_start.x
    first_y = first_end.y - first_start.y
    second_x = second_end.x - second_start.x
    second_y = second_end.y - second_start.y
    denominator = first_x * second_y - first_y * second_x
    if denominator == 0:
        raise RuntimeError(
            "cannot remove a rounded corner whose neighbouring segments are parallel"
        )
    offset_x = second_start.x - first_start.x
    offset_y = second_start.y - first_start.y
    distance = (offset_x * second_y - offset_y * second_x) / denominator
    return vector(
        round(first_start.x + distance * first_x),
        round(first_start.y + distance * first_y),
    )


def same_node_geometry(first, second):
    """Return whether two IPC polygon nodes contain identical geometry."""
    if first.has_point and second.has_point:
        return same_point(first.point, second.point)
    if first.has_arc and second.has_arc:
        return all(
            same_point(first_point, second_point)
            for first_point, second_point in (
                (first.arc.start, second.arc.start),
                (first.arc.mid, second.arc.mid),
                (first.arc.end, second.arc.end),
            )
        )
    return False


def unique_nodes(nodes):
    """Remove adjacent duplicate nodes returned by affected KiCad IPC builds."""
    result = []
    for node in nodes:
        if not result or not same_node_geometry(result[-1], node):
            result.append(node)
    if len(result) > 1 and same_node_geometry(result[0], result[-1]):
        result.pop()
    return result


def sharp_points_from_nodes(nodes):
    """Replace arc nodes with intersections of their neighbouring segments.

    A rounded polygon stores an arc's tangent start/end points, while KiCad
    implicitly connects adjacent nodes with straight segments. Extending the
    straight segment before an arc and the one after it recovers the sharp
    corner that existed before the radius was applied. Point nodes pass through
    unchanged, so an unrounded outline follows precisely the previous path.
    """
    nodes = unique_nodes(nodes)
    if not nodes:
        return []
    starts = [node.point if node.has_point else node.arc.start for node in nodes]
    ends = [node.point if node.has_point else node.arc.end for node in nodes]
    points = []
    for index, node in enumerate(nodes):
        if node.has_point:
            points.append(node.point)
            continue
        if not node.has_arc:
            raise RuntimeError("zone outline contains an unsupported empty node")
        points.append(
            line_intersection(
                ends[index - 1],
                node.arc.start,
                node.arc.end,
                starts[(index + 1) % len(nodes)],
            )
        )
    return compress(points)


def angle_from_horizontal(first, second):
    """Return an edge's unsigned angle from horizontal in the 0..90 range."""
    delta_x = abs(second.x - first.x)
    delta_y = abs(second.y - first.y)
    return math.degrees(math.atan2(delta_y, delta_x))


def snapped_direction(first, second):
    """Classify an existing edge without creating or removing any segments.

    The returned value is ``horizontal``, ``vertical``, ``diagonal_up`` (equal
    X/Y changes), or ``diagonal_down`` (equal and opposite X/Y changes).
    """
    angle = angle_from_horizontal(first, second)
    if angle < MIN_DIAGONAL_ANGLE_DEGREES:
        return "horizontal"
    if angle > MAX_DIAGONAL_ANGLE_DEGREES:
        return "vertical"
    same_sign = (second.x - first.x) * (second.y - first.y) >= 0
    return "diagonal_up" if same_sign else "diagonal_down"


def project_edge(first, second, direction):
    """Move both endpoints minimally toward one requested edge direction.

    Moving each endpoint by half the error preserves the edge midpoint. Repeated
    projection around the closed outline lets every shared corner settle at a
    position satisfying both of its neighbouring edges.
    """
    if direction == "horizontal":
        error = second[1] - first[1]
        first[1] += error / 2
        second[1] -= error / 2
    elif direction == "vertical":
        error = second[0] - first[0]
        first[0] += error / 2
        second[0] -= error / 2
    else:
        slope = 1 if direction == "diagonal_up" else -1
        error = (second[1] - first[1]) - slope * (second[0] - first[0])
        first[0] -= slope * error / 4
        first[1] += error / 4
        second[0] += slope * error / 4
        second[1] -= error / 4
    return abs(error)


def snap_outline(points):
    """Snap a closed outline by moving corners, never by adding segments.

    Each original edge is classified once from its original angle. Iterative
    orthogonal projection then finds nearby corner positions that satisfy all
    edge directions together, including the closing edge of the polygon. The
    input and output always contain exactly the same number of vertices.
    """
    points = compress(points)
    if len(points) < 3:
        raise RuntimeError("zone outline has fewer than three unique vertices")

    directions = [
        snapped_direction(point, points[(index + 1) % len(points)])
        for index, point in enumerate(points)
    ]
    adjusted = [[float(point.x), float(point.y)] for point in points]

    # Alternating projections converge quickly for these linear constraints.
    # The generous limit protects unusual outlines without affecting normal ones.
    for _iteration in range(10_000):
        largest_error = 0.0
        for index, direction in enumerate(directions):
            error = project_edge(
                adjusted[index], adjusted[(index + 1) % len(adjusted)], direction
            )
            largest_error = max(largest_error, error)
        if largest_error < 0.1:  # one tenth of an IPC nanometre
            break
    else:
        raise RuntimeError("outline corner adjustment did not converge")

    output = [vector(round(x), round(y)) for x, y in adjusted]
    if any(
        same_point(point, output[(index + 1) % len(output)])
        for index, point in enumerate(output)
    ):
        raise RuntimeError("corner adjustment collapsed an outline segment")
    return output


def remove_collinear_points(points):
    """Remove redundant vertices that split one continuous straight edge."""
    result = list(points)
    changed = True
    while changed and len(result) > 3:
        changed = False
        simplified = []
        for index, point in enumerate(result):
            previous = result[index - 1]
            following = result[(index + 1) % len(result)]
            incoming_x = point.x - previous.x
            incoming_y = point.y - previous.y
            outgoing_x = following.x - point.x
            outgoing_y = following.y - point.y
            cross = incoming_x * outgoing_y - incoming_y * outgoing_x
            dot = incoming_x * outgoing_x + incoming_y * outgoing_y
            if cross == 0 and dot > 0:
                changed = True
                continue
            simplified.append(point)
        result = simplified
    return result


def rounded_corners(points, radius):
    """Return tangent start/mid/end points for a fillet at each true corner.

    The radius is never silently reduced. If neighbouring fillets would
    overlap, the update is rejected so every generated arc has the requested
    radius.
    """
    corners = []
    tangent_distances = []
    for index, corner in enumerate(points):
        previous = points[index - 1]
        following = points[(index + 1) % len(points)]
        previous_length = math.hypot(previous.x - corner.x, previous.y - corner.y)
        following_length = math.hypot(following.x - corner.x, following.y - corner.y)
        if previous_length == 0 or following_length == 0:
            raise RuntimeError("cannot round a collapsed outline segment")

        toward_previous = (
            (previous.x - corner.x) / previous_length,
            (previous.y - corner.y) / previous_length,
        )
        toward_following = (
            (following.x - corner.x) / following_length,
            (following.y - corner.y) / following_length,
        )
        dot = max(
            -1.0,
            min(
                1.0,
                toward_previous[0] * toward_following[0]
                + toward_previous[1] * toward_following[1],
            ),
        )
        angle = math.acos(dot)
        if math.isclose(angle, math.pi, abs_tol=1e-12):
            corners.append(None)
            tangent_distances.append(0.0)
            continue
        if math.isclose(angle, 0.0, abs_tol=1e-12):
            raise RuntimeError("cannot round a 180-degree reversal in the outline")

        half_angle = angle / 2.0
        tangent_distance = radius / math.tan(half_angle)
        bisector_x = toward_previous[0] + toward_following[0]
        bisector_y = toward_previous[1] + toward_following[1]
        bisector_length = math.hypot(bisector_x, bisector_y)
        bisector_x /= bisector_length
        bisector_y /= bisector_length
        centre_distance = radius / math.sin(half_angle)
        centre_x = corner.x + bisector_x * centre_distance
        centre_y = corner.y + bisector_y * centre_distance

        start = vector(
            round(corner.x + toward_previous[0] * tangent_distance),
            round(corner.y + toward_previous[1] * tangent_distance),
        )
        end = vector(
            round(corner.x + toward_following[0] * tangent_distance),
            round(corner.y + toward_following[1] * tangent_distance),
        )
        middle = vector(
            round(centre_x - bisector_x * radius),
            round(centre_y - bisector_y * radius),
        )
        corners.append((start, middle, end))
        tangent_distances.append(tangent_distance)

    for index, first in enumerate(points):
        second = points[(index + 1) % len(points)]
        length = math.hypot(second.x - first.x, second.y - first.y)
        occupied = (
            tangent_distances[index] + tangent_distances[(index + 1) % len(points)]
        )
        if occupied >= length:
            raise RuntimeError(
                f"corner radius {to_mm(round(radius)):.3f} mm is too large for "
                f"outline edge {index + 1} ({to_mm(round(length)):.3f} mm)"
            )
    return corners


def polygon_from_points(points, corner_radius=0):
    """Build the closed IPC polygon, optionally filleting every true corner."""
    line = PolyLine()
    if corner_radius <= 0 or IGNORE_CORNER_RADIUS:
        for point in points:
            line.append(PolyLineNode.from_point(point))
    else:
        for point, rounded in zip(points, rounded_corners(points, corner_radius)):
            if rounded is None:
                line.append(PolyLineNode.from_point(point))
                continue
            start, middle, end = rounded
            arc = ArcStartMidEnd()
            arc.start = start
            arc.mid = middle
            arc.end = end
            node = PolyLineNode()
            node.arc = arc
            line.append(node)
    line.closed = True
    polygon = PolygonWithHoles()
    polygon.outline = line
    return polygon


def main():
    """Update all keep-outs and copper zones on configured nets."""
    corner_radius = from_mm(CORNER_RADIUS_MM)
    _client, board = connect_board()
    board_zones = board.get_zones()
    keep_outs = [zone for zone in board_zones if zone.type == ZoneType.ZT_RULE_AREA]
    copper_zones = [
        zone
        for zone in board_zones
        if zone.type == ZoneType.ZT_COPPER and zone_net_name(zone) in COPPER_NET_NAMES
    ]
    zones = keep_outs + copper_zones
    if not zones:
        raise RuntimeError(
            "no keep-out zones or copper zones on configured COPPER_NET_NAMES found"
        )

    with editor_commit(
        board,
        "Snap zone outlines to 45/90 degrees",
        refill_zones=True,
    ):
        for index, zone in enumerate(zones, start=1):
            nodes = zone.outline.outline.nodes
            original = sharp_points_from_nodes(nodes)
            snapped = snap_outline(original)
            final = remove_collinear_points(snapped)
            if len(final) < 3:
                raise RuntimeError(
                    f"{zone_kind(zone)} {index} would have fewer than three vertices"
                )
            zone.outline = polygon_from_points(final, corner_radius)
            if DEBUG:
                print(
                    f'{zone_kind(zone).title()} {index} "{zone.name}": '
                    f"{len(original)} -> {len(final)} vertices, "
                    f"corner radius {max(CORNER_RADIUS_MM, 0):.3f} mm"
                )
                for point in final:
                    print(f"  ({to_mm(point.x):.3f}, {to_mm(point.y):.3f}) mm")
        board.update_items(zones)

    print(
        f"Updated {len(keep_outs)} keep-out zone(s) and "
        f"{len(copper_zones)} copper zone(s) "
        "(undo: Snap zone outlines to 45/90 degrees)."
    )


if __name__ == "__main__":
    main()
