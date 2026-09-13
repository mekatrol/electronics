"""Shared filesystem and KiCad geometry helpers."""

import math
import os

from kipy.board_types import (
    BoardArc, BoardBezier, BoardCircle, BoardPolygon, BoardRectangle,
    BoardSegment,
)

from kicad_ipc import vector


def open_file_write(path, mode):
    """Open ``path`` for writing, creating parent directories as needed."""
    dir_path = os.path.dirname(path)

    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    return open(path, mode)


def distribution_offsets(items):
    """Return equal edge-to-edge spacing offsets for axis-sorted items."""
    ordered = sorted(items, key=lambda item: (item[1] + item[2], item[0]))
    first_end = ordered[0][2]
    last_start = ordered[-1][1]
    inner_width = sum(end - start for _name, start, end in ordered[1:-1])
    gap = (last_start - first_end - inner_width) / (len(ordered) - 1)
    offsets = {ordered[0][0]: 0, ordered[-1][0]: 0}
    next_start = first_end + gap
    for name, start, end in ordered[1:-1]:
        offsets[name] = round(next_start - start)
        next_start += end - start + gap
    return offsets


def centering_delta(moving_center, target_center):
    """Return the integer translation placing one centre on another."""
    return vector(
        target_center.x - moving_center.x,
        target_center.y - moving_center.y,
    )


def _arc_points(arc, maximum_step_degrees=5.0):
    center = arc.center()
    if center is None:
        return [arc.start, arc.end]
    start = math.atan2(arc.start.y - center.y, arc.start.x - center.x)
    middle = math.atan2(arc.mid.y - center.y, arc.mid.x - center.x)
    end = math.atan2(arc.end.y - center.y, arc.end.x - center.x)
    tau = 2 * math.pi
    ccw_sweep = (end - start) % tau
    sweep = ccw_sweep if (middle - start) % tau <= ccw_sweep else ccw_sweep - tau
    steps = max(1, math.ceil(abs(math.degrees(sweep)) / maximum_step_degrees))
    radius = arc.radius()
    points = [
        vector(
            center.x + radius * math.cos(start + sweep * index / steps),
            center.y + radius * math.sin(start + sweep * index / steps),
        )
        for index in range(steps + 1)
    ]
    points[0], points[-1] = arc.start, arc.end
    return points


def _polyline_points(polyline):
    points = []
    for node in polyline:
        node_points = [node.point] if node.has_point else _arc_points(node.arc)
        if points and points[-1] == node_points[0]:
            points.extend(node_points[1:])
        else:
            points.extend(node_points)
    if points and points[-1] != points[0]:
        points.append(points[0])
    return points


def _edge_pieces(edge_items):
    pieces = []
    for item in edge_items:
        if isinstance(item, BoardSegment):
            pieces.append([item.start, item.end])
        elif isinstance(item, BoardArc):
            pieces.append(_arc_points(item))
        elif isinstance(item, BoardRectangle):
            left = min(item.top_left.x, item.bottom_right.x)
            right = max(item.top_left.x, item.bottom_right.x)
            top = min(item.top_left.y, item.bottom_right.y)
            bottom = max(item.top_left.y, item.bottom_right.y)
            pieces.append([
                vector(left, top), vector(right, top), vector(right, bottom),
                vector(left, bottom), vector(left, top),
            ])
        elif isinstance(item, BoardCircle):
            radius = math.hypot(
                item.radius_point.x - item.center.x,
                item.radius_point.y - item.center.y,
            )
            circle = [
                vector(
                    item.center.x + radius * math.cos(2 * math.pi * i / 72),
                    item.center.y + radius * math.sin(2 * math.pi * i / 72),
                )
                for i in range(73)
            ]
            circle[-1] = circle[0]
            pieces.append(circle)
        elif isinstance(item, BoardPolygon):
            for polygon in item.polygons:
                pieces.append(_polyline_points(polygon.outline))
                pieces.extend(_polyline_points(hole) for hole in polygon.holes)
        elif isinstance(item, BoardBezier):
            points = []
            for index in range(41):
                t = index / 40
                u = 1 - t
                points.append(vector(
                    u**3 * item.start.x + 3*u*u*t * item.control1.x
                    + 3*u*t*t * item.control2.x + t**3 * item.end.x,
                    u**3 * item.start.y + 3*u*u*t * item.control1.y
                    + 3*u*t*t * item.control2.y + t**3 * item.end.y,
                ))
            points[0], points[-1] = item.start, item.end
            pieces.append(points)
        else:
            raise RuntimeError(f"unsupported Edge.Cuts item {type(item).__name__}")
    return [piece for piece in pieces if piece]


def edge_contours(edge_items):
    """Join arbitrary Edge.Cuts primitives into closed ordered contours."""
    pieces = _edge_pieces(edge_items)
    contours = []
    while pieces:
        contour = pieces.pop(0)
        while contour[-1] != contour[0]:
            endpoint = contour[-1]
            match = next((
                (index, reverse)
                for index, piece in enumerate(pieces)
                for reverse in (False, True)
                if (piece[-1] if reverse else piece[0]) == endpoint
            ), None)
            if match is None:
                raise RuntimeError("Edge.Cuts contains an open contour")
            index, reverse = match
            piece = pieces.pop(index)
            if reverse:
                piece.reverse()
            contour.extend(piece[1:])
        contours.append(contour)
    return contours


def _area_centroid(points):
    twice_area = weighted_x = weighted_y = 0
    for first, second in zip(points, points[1:]):
        cross = first.x * second.y - second.x * first.y
        twice_area += cross
        weighted_x += (first.x + second.x) * cross
        weighted_y += (first.y + second.y) * cross
    if twice_area == 0:
        raise RuntimeError("Edge.Cuts contour has zero area")
    return abs(twice_area), weighted_x / (3 * twice_area), weighted_y / (3 * twice_area)


def edge_cuts_centroid(edge_items):
    """Return the area centroid of a complex Edge.Cuts polygon.

    The largest contour is treated as the outer boundary. Additional closed
    contours are treated as cut-outs regardless of their drawing direction.
    """
    contours = edge_contours(edge_items)
    if not contours:
        raise RuntimeError("board has no Edge.Cuts contour")
    parts = sorted((_area_centroid(points) for points in contours), reverse=True)
    outer_area, outer_x, outer_y = parts[0]
    total_area = outer_area - sum(area for area, _x, _y in parts[1:])
    if total_area <= 0:
        raise RuntimeError("Edge.Cuts cut-outs consume the outer contour")
    x = (outer_area * outer_x - sum(a*x for a, x, _y in parts[1:])) / total_area
    y = (outer_area * outer_y - sum(a*y for a, _x, y in parts[1:])) / total_area
    return vector(x, y)
