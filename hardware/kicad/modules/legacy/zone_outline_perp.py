"""Replace diagonal zone-outline edges with perpendicular segments.

Execution:
    Open a board in KiCad's PCB Editor, set ``ZONE_NAME`` and the corner
    preference below, then run this file from the scripting console with::

        import runpy; _result = runpy.run_path("/home/dad/repos/electronics/hardware/kicad/modules/legacy/zone_outline_perp.py")

The first outer contour is rebuilt and zone cutouts are not preserved. Review
the result in the editor and save the board manually.
"""

import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pcbnew_helpers import (  # noqa: E402
    get_current_board,
    is_horizontal,
    is_vertical,
    iu_to_mm as mm,
    same_point,
    vector as vec,
)


# ============================================================
# User settings
# ============================================================
ZONE_NAME = ""          # exact zone name to match
PREFER_HORIZONTAL_FIRST = True  # for diagonal replacement: horizontal then vertical
DEBUG = True


# ============================================================
# Helpers
# ============================================================
def is_axis_aligned(a, b):
    """Return whether an outline edge is horizontal or vertical."""
    return is_horizontal(a, b) or is_vertical(a, b)


def compress_duplicate_points(points):
    if not points:
        return []

    out = [vec(points[0].x, points[0].y)]

    for p in points[1:]:
        if not same_point(out[-1], p):
            out.append(vec(p.x, p.y))

    # Drop explicit closing point if present
    if len(out) > 1 and same_point(out[0], out[-1]):
        out.pop()

    return out


def merge_collinear_edges(points):
    """
    Merge consecutive collinear edges in a closed polygon.
    Input/output: list of unique polygon vertices, with no repeated closing point.
    """
    pts = compress_duplicate_points(points)

    if len(pts) < 3:
        return pts[:]

    changed = True

    while changed and len(pts) >= 3:
        changed = False
        new_pts = []
        n = len(pts)

        for i in range(n):
            prev = pts[(i - 1) % n]
            cur = pts[i]
            nxt = pts[(i + 1) % n]

            prev_cur_h = is_horizontal(prev, cur)
            prev_cur_v = is_vertical(prev, cur)
            cur_nxt_h = is_horizontal(cur, nxt)
            cur_nxt_v = is_vertical(cur, nxt)

            # Merge if the current point sits between two collinear axis-aligned edges
            if (prev_cur_h and cur_nxt_h) or (prev_cur_v and cur_nxt_v):
                changed = True
                continue

            new_pts.append(vec(cur.x, cur.y))

        pts = compress_duplicate_points(new_pts)

    return pts


def orthogonalize_edges(points, prefer_horizontal_first=True):
    """
    Walk edges of a closed polygon. Any diagonal edge is replaced with two
    orthogonal edges by inserting one corner point.
    """
    pts = compress_duplicate_points(points)

    if len(pts) < 3:
        raise RuntimeError("Polygon has fewer than 3 unique points")

    out = []
    n = len(pts)

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]

        if not out:
            out.append(vec(a.x, a.y))

        if is_axis_aligned(a, b):
            if not same_point(out[-1], b):
                out.append(vec(b.x, b.y))
            continue

        # Replace diagonal edge with an L-shape
        if prefer_horizontal_first:
            mid = vec(b.x, a.y)
        else:
            mid = vec(a.x, b.y)

        if not same_point(out[-1], mid):
            out.append(mid)

        if not same_point(out[-1], b):
            out.append(vec(b.x, b.y))

    out = compress_duplicate_points(out)
    out = merge_collinear_edges(out)
    out = compress_duplicate_points(out)

    if len(out) < 3:
        raise RuntimeError("Orthogonalization collapsed polygon too far")

    return out


def has_only_90_degree_corners(points):
    """
    True if every edge is horizontal or vertical.
    For an orthogonal polygon, that means all corners are 90 or 270 degrees.
    """
    pts = compress_duplicate_points(points)
    n = len(pts)

    if n < 3:
        return False

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        if not is_axis_aligned(a, b):
            return False

    return True


def get_matching_zones(board, zone_name):
    matches = []

    for zone in board.Zones():
        try:
            if zone.GetZoneName() == zone_name or zone_name == '':
                matches.append(zone)
        except Exception:
            pass

    return matches


def extract_outer_outline_points(zone):
    """
    Reads only the first outer outline.
    This script does not preserve holes/cutouts.
    """
    poly = zone.Outline()
    outline_count = poly.OutlineCount()

    if outline_count < 1:
        raise RuntimeError("Zone has no outlines")

    chain = poly.Outline(0)
    count = chain.PointCount()

    if count < 3:
        raise RuntimeError("Zone outline has too few points")

    pts = []

    for i in range(count):
        p = chain.CPoint(i)
        pts.append(vec(p.x, p.y))

    return compress_duplicate_points(pts)


def rebuild_zone_outline(zone, points):
    """
    Rebuilds a single outer contour.
    """
    zone.RemoveAllContours()

    for p in points:
        ok = zone.AppendCorner(vec(p.x, p.y), -1, False)
        if not ok:
            raise RuntimeError(f"Failed to append point ({p.x}, {p.y})")


def dump_points(label, points):
    print(label)
    for i, p in enumerate(points):
        print(f"  {i:02d}: ({mm(p.x):.3f}, {mm(p.y):.3f}) mm")


# ============================================================
# Main
# ============================================================
board = get_current_board()
if board is None:
    raise RuntimeError("No board is open")

zones = get_matching_zones(board, ZONE_NAME)

if not zones:
    raise RuntimeError(f'No zones found with zone name "{ZONE_NAME}"')

changed_count = 0

for index, zone in enumerate(zones, start=1):
    old_points = extract_outer_outline_points(zone)
    merged_points = merge_collinear_edges(old_points)
    new_points = orthogonalize_edges(
        merged_points,
        prefer_horizontal_first=PREFER_HORIZONTAL_FIRST
    )

    if DEBUG:
        print(f'Zone {index}: "{ZONE_NAME}"')
        dump_points("  Original points:", old_points)
        dump_points("  After collinear merge:", merged_points)
        dump_points("  Final orthogonal points:", new_points)
        print(f"  Orthogonal result: {has_only_90_degree_corners(new_points)}")

    rebuild_zone_outline(zone, new_points)
    changed_count += 1

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

pcbnew.Refresh()

print(f'Updated {changed_count} zone(s) named "{ZONE_NAME}"')
