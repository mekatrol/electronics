"""Create a routed mouse-bite panel while preserving the source PCB outline.

Run from the repository root with::

    python3 hardware/kicad/modules/panelize_routed_pcb.py hardware/mek-sub-triac/mek-sub-triac.kicad_pcb -x 2 -y 2 --force
    python3 hardware/kicad/modules/panelize_routed_pcb.py --help


Each source Edge.Cuts outline is copied. Straight sections at the middle of
each top and bottom edge are opened for breakaway tabs and 0.6 mm NPTH
mouse-bite holes. The source PCB is read only.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import ctypes.util
import json
import math
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from kicad_discovery import find_fiducial_library_file, find_kicad_cli

# ---------------------------------------------------------------------------
# User-adjustable panel geometry and JLCPCB limits (all dimensions in mm)
# ---------------------------------------------------------------------------
# Review these sources before changing the values: fabrication capabilities
# can change after this script is updated.
#
# Mouse-bite guide (hole count/diameter/spacing, tab placement, panel gap):
# https://jlcpcb.com/blog/mouse-bite-panelization-guide
#
# PCB capabilities (routing gap, tooling rails, fiducials and tooling holes):
# https://jlcpcb.com/capabilities/Capab
#
# The command-line options use the DEFAULT_* values. MIN_*/MAX_* values are
# validation limits, not alternative defaults.

# Routed clearance between adjacent PCB envelopes. JLCPCB describes 1.6 or
# 2.0 mm as typical and 1.2 mm as the absolute minimum. This script keeps the
# more conservative 2.0 mm minimum/default to accommodate normal routing.
DEFAULT_GAP_MM = 2.0
MIN_GAP_MM = 2.0

# Process rail around all four panel sides. JLCPCB lists 3 mm as a fabrication
# minimum, but specifies 5 mm when the panel carries SMT tooling features.
# This script always adds those features, so it enforces 5 mm.
DEFAULT_RAIL_MM = 5.0
MIN_RAIL_MM = 5.0

# Width of each solid breakaway bridge before drilling the mouse bites.
# JLCPCB specifies 5 mm minimum for a breakaway tab containing mouse bites.
DEFAULT_TAB_WIDTH_MM = 5.0
MIN_TAB_WIDTH_MM = 5.0

# NPTH mouse-bite drill diameter. JLCPCB permits 0.5-0.8 mm and recommends
# 0.6 mm. Five holes at the defaults below occupy a 4.6 mm overall span.
DEFAULT_MOUSE_BITE_DIAMETER_MM = 0.6
MIN_MOUSE_BITE_DIAMETER_MM = 0.5
MAX_MOUSE_BITE_DIAMETER_MM = 0.8

# Material left edge-to-edge between adjacent mouse-bite holes. JLCPCB's
# dedicated guide requires at least 0.3 mm and recommends 0.35-0.4 mm. The
# 0.4 mm default plus 0.6 mm drills produces a 1.0 mm centre pitch.
DEFAULT_MOUSE_BITE_CLEARANCE_MM = 0.4
MIN_MOUSE_BITE_CLEARANCE_MM = 0.3
MAX_MOUSE_BITE_CLEARANCE_MM = 0.4

# Move the drill centre slightly out of the finished PCB and into its tab. This
# preserves a pronounced breakaway scallop while avoiding marginal hole-to-pad
# clearance failures on densely populated board edges.
MOUSE_BITE_OUTWARD_OFFSET_MM = 0.05

# Global SMT fiducials use the installed KiCad 1 mm copper / 2 mm mask
# footprint. JLCPCB specifies their centres 3.85 mm from the panel edge.
FIDUCIAL_EDGE_OFFSET_MM = 3.85
# Horizontal clearance between each fiducial and the adjacent PCB area. This
# is a conservative layout choice, not a published JLCPCB minimum.
FIDUCIAL_HORIZONTAL_CLEARANCE_MM = 5.0

# JLCPCB SMT panel tooling holes are 2 mm NPTH. A 2.5 mm centre inset leaves
# 1.5 mm of laminate between each hole edge and its two adjacent panel edges.
TOOLING_HOLE_DIAMETER_MM = 2.0
TOOLING_HOLE_EDGE_OFFSET_MM = 2.5

# KiCad drawing width for routed Edge.Cuts. JLCPCB follows the line centre and
# recommends 0.15 mm for board outlines, slots, cutouts and milling geometry:
# https://jlcpcb.com/help/article/instructions-for-ordering
EDGE_CUT_WIDTH_MM = 0.15

Atom = str
Node = list["Atom | Node"]


class SExprError(ValueError):
    pass


TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+')


def parse_sexpr(text: str) -> Node:
    root: Node = []
    stack: list[Node] = [root]
    for token in TOKEN_RE.findall(text):
        if token == "(":
            child: Node = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) == 1:
                raise SExprError("unexpected closing parenthesis")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise SExprError("unterminated S-expression")
    if len(root) != 1 or not isinstance(root[0], list):
        raise SExprError("expected exactly one root expression")
    return root[0]


def dump_sexpr(node: Node, level: int = 0) -> str:
    if not node:
        return "()"
    head_value = str(node[0])
    if all(not isinstance(value, list) for value in node):
        return "(" + " ".join(str(value) for value in node) + ")"
    child_indent = "\t" * (level + 1)
    parts = ["(" + head_value]
    for value in node[1:]:
        if isinstance(value, list):
            parts.append("\n" + child_indent + dump_sexpr(value, level + 1))
        elif parts[-1].endswith("\n"):
            parts.append(child_indent + str(value))
        else:
            parts.append(" " + str(value))
    parts.append(")")
    return "".join(parts)


def head(node: Node) -> str:
    return str(node[0]) if node else ""


def first_child(node: Node, name: str) -> Node | None:
    for value in node[1:]:
        if isinstance(value, list) and head(value) == name:
            return value
    return None


def quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def walk(node: Node):
    yield node
    for value in node[1:]:
        if isinstance(value, list):
            yield from walk(value)


def translate_pair(node: Node, dx: float, dy: float) -> None:
    if len(node) >= 3:
        node[1] = number(float(str(node[1])) + dx)
        node[2] = number(float(str(node[2])) + dy)


def translate_item(item: Node, dx: float, dy: float) -> None:
    if head(item) == "footprint":
        at = first_child(item, "at")
        if at:
            translate_pair(at, dx, dy)
        return
    for node in walk(item):
        if head(node) in {"at", "start", "mid", "end", "center", "xy", "position"}:
            translate_pair(node, dx, dy)


def remove_zone_fills(item: Node) -> None:
    item[:] = [
        value
        for value in item
        if not (isinstance(value, list) and head(value) == "filled_polygon")
    ]
    for value in item[1:]:
        if isinstance(value, list):
            remove_zone_fills(value)


def renew_uuids(item: Node) -> None:
    replacements: dict[str, str] = {}
    for node in walk(item):
        if head(node) in {"uuid", "tstamp"} and len(node) > 1:
            replacements[str(node[1]).strip('"')] = str(uuid.uuid4())
    for node in walk(item):
        for index, value in enumerate(node):
            if isinstance(value, str) and value.strip('"') in replacements:
                replacement = replacements[value.strip('"')]
                node[index] = (
                    quoted(replacement) if value.startswith('"') else replacement
                )


def remap_nets(item: Node, suffix: str) -> None:
    for node in walk(item):
        if head(node) != "net" or len(node) < 2:
            continue
        raw_net = str(node[1])
        if raw_net.startswith('"'):
            net_name = raw_net.strip('"')
            if net_name:
                node[1] = quoted(net_name + suffix)
        elif len(node) >= 3 and raw_net != "0":
            node[2] = quoted(str(node[2]).strip('"') + suffix)


def make_reference_unique(item: Node, suffix: str) -> None:
    """Append a panel-position suffix to a footprint's reference."""
    if head(item) != "footprint":
        return
    for value in item[1:]:
        if (
            isinstance(value, list)
            and head(value) == "property"
            and len(value) >= 3
            and str(value[1]).strip('"') == "Reference"
        ):
            value[2] = quoted(str(value[2]).strip('"') + suffix)


@dataclass(frozen=True)
class Bounds:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top


def tab_edge_orientation(bounds: Bounds, tab_width: float) -> str:
    """Choose edges long enough to contain a centred breakaway tab."""
    if bounds.width >= tab_width:
        return "horizontal"
    if bounds.height >= tab_width:
        return "vertical"
    raise ValueError(
        f"{tab_width:g} mm tabs do not fit the source PCB's "
        f"{bounds.width:g} x {bounds.height:g} mm Edge.Cuts envelope"
    )


def edge_bounds(root: Node) -> Bounds:
    points: list[tuple[float, float]] = []
    for item in root[1:]:
        if not isinstance(item, list) or not head(item).startswith("gr_"):
            continue
        layer = first_child(item, "layer")
        if not layer or len(layer) < 2 or str(layer[1]).strip('"') != "Edge.Cuts":
            continue
        for node in walk(item):
            if head(node) in {"start", "mid", "end", "center", "xy"} and len(node) >= 3:
                points.append((float(str(node[1])), float(str(node[2]))))
    if not points:
        raise SExprError("source board has no Edge.Cuts geometry")
    xs, ys = zip(*points)
    return Bounds(min(xs), min(ys), max(xs), max(ys))


def _point(node: Node) -> tuple[float, float]:
    return float(str(node[1])), float(str(node[2]))


def _required_point(item: Node, name: str) -> tuple[float, float]:
    node = first_child(item, name)
    if node is None or len(node) < 3:
        raise SExprError(f"{head(item)} is missing a valid {name} point")
    return _point(node)


def _arc_points(
    item: Node, maximum_step_degrees: float = 5.0
) -> list[tuple[float, float]]:
    """Approximate one KiCad start/mid/end arc without changing its endpoints."""
    start = _required_point(item, "start")
    middle = _required_point(item, "mid")
    end = _required_point(item, "end")
    x1, y1 = start
    x2, y2 = middle
    x3, y3 = end
    determinant = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(determinant) < 1e-12:
        raise ValueError("Edge.Cuts contains a degenerate arc")
    ux = (
        (x1 * x1 + y1 * y1) * (y2 - y3)
        + (x2 * x2 + y2 * y2) * (y3 - y1)
        + (x3 * x3 + y3 * y3) * (y1 - y2)
    ) / determinant
    uy = (
        (x1 * x1 + y1 * y1) * (x3 - x2)
        + (x2 * x2 + y2 * y2) * (x1 - x3)
        + (x3 * x3 + y3 * y3) * (x2 - x1)
    ) / determinant
    angles = [math.atan2(y - uy, x - ux) for x, y in (start, middle, end)]

    def ccw_distance(first: float, second: float) -> float:
        return (second - first) % (2 * math.pi)

    ccw_sweep = ccw_distance(angles[0], angles[2])
    if ccw_distance(angles[0], angles[1]) <= ccw_sweep + 1e-12:
        sweep = ccw_sweep
    else:
        sweep = ccw_sweep - 2 * math.pi
    segments = max(2, math.ceil(abs(math.degrees(sweep)) / maximum_step_degrees))
    radius = math.hypot(x1 - ux, y1 - uy)
    points = [
        (
            ux + radius * math.cos(angles[0] + sweep * index / segments),
            uy + radius * math.sin(angles[0] + sweep * index / segments),
        )
        for index in range(segments + 1)
    ]
    points[0], points[-1] = start, end
    return points


def edge_contour_points(root: Node) -> list[tuple[float, float]]:
    """Return the single source Edge.Cuts contour as an ordered polygon."""
    pieces: list[list[tuple[float, float]]] = []
    for item in root[1:]:
        if not isinstance(item, list) or not is_edge_item(item):
            continue
        if head(item) == "gr_line":
            pieces.append(
                [_required_point(item, "start"), _required_point(item, "end")]
            )
        elif head(item) == "gr_arc":
            pieces.append(_arc_points(item))
        else:
            raise ValueError(f"unsupported source Edge.Cuts item: {head(item)}")
    if not pieces:
        raise ValueError("source board has no Edge.Cuts contour")
    contour = pieces.pop(0)
    tolerance = 1e-5
    while pieces:
        endpoint = contour[-1]
        for index, piece in enumerate(pieces):
            if math.dist(endpoint, piece[0]) <= tolerance:
                contour.extend(piece[1:])
                pieces.pop(index)
                break
            if math.dist(endpoint, piece[-1]) <= tolerance:
                contour.extend(reversed(piece[:-1]))
                pieces.pop(index)
                break
        else:
            raise ValueError("source Edge.Cuts is not one connected contour")
    if math.dist(contour[0], contour[-1]) > tolerance:
        raise ValueError("source Edge.Cuts contour is open")
    return contour[:-1]


def _wkt_polygon(points: list[tuple[float, float]]) -> str:
    closed = points + [points[0]]
    return "POLYGON((" + ",".join(f"{x:.9f} {y:.9f}" for x, y in closed) + "))"


def _rectangle(
    left: float, top: float, right: float, bottom: float
) -> list[tuple[float, float]]:
    return [(left, top), (right, top), (right, bottom), (left, bottom)]


def union_polygon_rings(
    polygons: list[list[tuple[float, float]]],
) -> list[list[tuple[float, float]]]:
    """Union polygons with the system GEOS library and return all boundary rings."""
    library_name = ctypes.util.find_library("geos_c")
    if not library_name:
        raise RuntimeError("libgeos_c is required to construct closed routed cutouts")
    geos = ctypes.CDLL(library_name)
    pointer = ctypes.c_void_p
    geos.GEOS_init_r.restype = pointer
    context = geos.GEOS_init_r()
    if not context:
        raise RuntimeError("could not initialize GEOS")
    signatures = {
        "GEOSWKTReader_create_r": ([pointer], pointer),
        "GEOSWKTReader_read_r": ([pointer, pointer, ctypes.c_char_p], pointer),
        "GEOSUnaryUnion_r": ([pointer, pointer], pointer),
        "GEOSGetGeometryN_r": ([pointer, pointer, ctypes.c_int], pointer),
        "GEOSGetExteriorRing_r": ([pointer, pointer], pointer),
        "GEOSGetInteriorRingN_r": ([pointer, pointer, ctypes.c_int], pointer),
        "GEOSGeom_getCoordSeq_r": ([pointer, pointer], pointer),
    }
    for name, (argument_types, result_type) in signatures.items():
        function = getattr(geos, name)
        function.argtypes = argument_types
        function.restype = result_type
    geos.GEOSGeomTypeId_r.argtypes = [pointer, pointer]
    geos.GEOSGeomTypeId_r.restype = ctypes.c_int
    geos.GEOSGetNumGeometries_r.argtypes = [pointer, pointer]
    geos.GEOSGetNumGeometries_r.restype = ctypes.c_int
    geos.GEOSGetNumInteriorRings_r.argtypes = [pointer, pointer]
    geos.GEOSGetNumInteriorRings_r.restype = ctypes.c_int
    geos.GEOSCoordSeq_getSize_r.argtypes = [
        pointer,
        pointer,
        ctypes.POINTER(ctypes.c_uint),
    ]
    geos.GEOSCoordSeq_getX_r.argtypes = [
        pointer,
        pointer,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_double),
    ]
    geos.GEOSCoordSeq_getY_r.argtypes = [
        pointer,
        pointer,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_double),
    ]
    geos.GEOSGeom_destroy_r.argtypes = [pointer, pointer]
    geos.GEOSWKTReader_destroy_r.argtypes = [pointer, pointer]
    geos.GEOS_finish_r.argtypes = [pointer]
    reader = geos.GEOSWKTReader_create_r(context)
    collection_wkt = (
        "GEOMETRYCOLLECTION(" + ",".join(_wkt_polygon(p) for p in polygons) + ")"
    )
    collection = geos.GEOSWKTReader_read_r(context, reader, collection_wkt.encode())
    merged = geos.GEOSUnaryUnion_r(context, collection)
    if not merged:
        raise RuntimeError("GEOS could not union the panel substrate geometry")

    def coordinates(ring: int) -> list[tuple[float, float]]:
        sequence = geos.GEOSGeom_getCoordSeq_r(context, ring)
        size = ctypes.c_uint()
        geos.GEOSCoordSeq_getSize_r(context, sequence, ctypes.byref(size))
        result: list[tuple[float, float]] = []
        for index in range(size.value - 1):
            x, y = ctypes.c_double(), ctypes.c_double()
            geos.GEOSCoordSeq_getX_r(context, sequence, index, ctypes.byref(x))
            geos.GEOSCoordSeq_getY_r(context, sequence, index, ctypes.byref(y))
            result.append((x.value, y.value))
        return result

    rings: list[list[tuple[float, float]]] = []
    geometries = (
        [merged]
        if geos.GEOSGeomTypeId_r(context, merged) == 3
        else [
            geos.GEOSGetGeometryN_r(context, merged, index)
            for index in range(geos.GEOSGetNumGeometries_r(context, merged))
        ]
    )
    for geometry in geometries:
        rings.append(coordinates(geos.GEOSGetExteriorRing_r(context, geometry)))
        for index in range(geos.GEOSGetNumInteriorRings_r(context, geometry)):
            rings.append(
                coordinates(geos.GEOSGetInteriorRingN_r(context, geometry, index))
            )
    geos.GEOSGeom_destroy_r(context, merged)
    geos.GEOSGeom_destroy_r(context, collection)
    geos.GEOSWKTReader_destroy_r(context, reader)
    geos.GEOS_finish_r(context)
    return rings


def graphic_polygon(points: list[tuple[float, float]]) -> Node:
    return [
        "gr_poly",
        ["pts", *[["xy", number(x), number(y)] for x, y in points]],
        ["stroke", ["width", number(EDGE_CUT_WIDTH_MM)], ["type", "solid"]],
        ["fill", "none"],
        ["layer", quoted("Edge.Cuts")],
        ["uuid", quoted(str(uuid.uuid4()))],
    ]


def graphic_line(
    x1: float, y1: float, x2: float, y2: float, layer: str, width: float
) -> Node:
    return [
        "gr_line",
        ["start", number(x1), number(y1)],
        ["end", number(x2), number(y2)],
        ["stroke", ["width", number(width)], ["type", "default"]],
        ["layer", quoted(layer)],
        ["uuid", quoted(str(uuid.uuid4()))],
    ]


def load_fiducial_template(path: Path) -> Node:
    template = parse_sexpr(path.read_text(encoding="utf-8-sig"))
    if head(template) != "footprint":
        raise SExprError(f"not a footprint file: {path}")
    return template


def fiducial(template: Node, reference: str, x: float, y: float) -> Node:
    result = copy.deepcopy(template)
    result[1] = quoted("Fiducial:Fiducial_1mm_Mask2mm")
    result[:] = [
        value
        for value in result
        if not (isinstance(value, list) and head(value) in {"version", "generator"})
    ]
    layer_index = next(
        index
        for index, value in enumerate(result)
        if isinstance(value, list) and head(value) == "layer"
    )
    result.insert(layer_index + 1, ["uuid", quoted(str(uuid.uuid4()))])
    result.insert(layer_index + 2, ["at", number(x), number(y)])
    reference_property = next(
        value
        for value in result
        if isinstance(value, list)
        and head(value) == "property"
        and len(value) >= 3
        and str(value[1]).strip('"') == "Reference"
    )
    reference_property[2] = quoted(reference)
    if not first_child(reference_property, "hide"):
        layer_position = next(
            index
            for index, value in enumerate(reference_property)
            if isinstance(value, list) and head(value) == "layer"
        )
        reference_property.insert(layer_position + 1, ["hide", "yes"])
    for node in walk(result):
        if (
            node is not result
            and (head(node).startswith("fp_") or head(node) == "pad")
            and not first_child(node, "uuid")
        ):
            node.append(["uuid", quoted(str(uuid.uuid4()))])
    return result


STRUCTURAL = {
    "version",
    "generator",
    "generator_version",
    "general",
    "paper",
    "layers",
    "setup",
    "embedded_fonts",
}

PAPER_SIZES_MM = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
    "A5": (210.0, 148.0),
    "Letter": (279.4, 215.9),
    "Legal": (355.6, 215.9),
    "Ledger": (431.8, 279.4),
}


def page_dimensions(root: Node) -> tuple[float, float] | None:
    """Return the KiCad drawing-sheet dimensions in landscape coordinates."""
    paper = first_child(root, "paper")
    if not paper or len(paper) < 2:
        return None
    size = PAPER_SIZES_MM.get(str(paper[1]).strip('"'))
    if not size:
        return None
    if any(str(value).strip('"').lower() == "portrait" for value in paper[2:]):
        return size[1], size[0]
    return size


def is_edge_item(item: list) -> bool:
    layer = first_child(item, "layer")
    return bool(layer and len(layer) >= 2 and str(layer[1]).strip('"') == "Edge.Cuts")


def npth_hole(reference: str, value: str, x: float, y: float, diameter: float) -> list:
    """Create a board-only NPTH drill with no library association."""
    import uuid

    return [
        "footprint",
        quoted(""),
        ["layer", quoted("F.Cu")],
        ["uuid", quoted(str(uuid.uuid4()))],
        ["at", number(x), number(y)],
        [
            "property",
            quoted("Reference"),
            quoted(reference),
            ["at", "0", "0", "0"],
            ["layer", quoted("F.Fab")],
            ["hide", "yes"],
            ["effects", ["font", ["size", "0.5", "0.5"], ["thickness", "0.08"]]],
        ],
        [
            "property",
            quoted("Value"),
            quoted(value),
            ["at", "0", "0", "0"],
            ["layer", quoted("F.Fab")],
            ["hide", "yes"],
            ["effects", ["font", ["size", "0.5", "0.5"], ["thickness", "0.08"]]],
        ],
        ["attr", "board_only", "exclude_from_pos_files", "exclude_from_bom"],
        [
            "pad",
            quoted(""),
            "np_thru_hole",
            "circle",
            ["at", "0", "0"],
            ["size", number(diameter), number(diameter)],
            ["drill", number(diameter)],
            ["layers", quoted("*.Cu"), quoted("*.Mask")],
            ["uuid", quoted(str(uuid.uuid4()))],
        ],
        ["embedded_fonts", "no"],
    ]


def mouse_bite(reference: str, x: float, y: float, diameter: float) -> list:
    return npth_hole(reference, "MouseBite", x, y, diameter)


def bite_positions(
    centre: float, tab_width: float, diameter: float, clearance: float
) -> list[float]:
    pitch = diameter + clearance
    count = max(2, math.floor((tab_width + clearance) / pitch))
    span = (count - 1) * pitch
    return [centre - span / 2 + index * pitch for index in range(count)]


def build_routed_panel(
    source: list,
    count_x: int,
    count_y: int,
    gap: float,
    rail: float,
    tab_width: float,
    bite_diameter: float,
    bite_clearance: float,
    fiducial_template: list,
    center_on_page: bool = True,
) -> tuple[list, Bounds]:
    if gap < MIN_GAP_MM:
        raise ValueError(f"gap must be at least {MIN_GAP_MM:.1f} mm for JLCPCB routing")
    if rail < MIN_RAIL_MM:
        raise ValueError(
            f"rail must be at least {MIN_RAIL_MM:g} mm for JLCPCB SMT assembly"
        )
    if tab_width < MIN_TAB_WIDTH_MM:
        raise ValueError("mouse-bite tab width must be at least 5 mm")
    if not MIN_MOUSE_BITE_DIAMETER_MM <= bite_diameter <= MAX_MOUSE_BITE_DIAMETER_MM:
        raise ValueError(
            f"mouse-bite diameter must be {MIN_MOUSE_BITE_DIAMETER_MM:g} to "
            f"{MAX_MOUSE_BITE_DIAMETER_MM:g} mm"
        )
    if not MIN_MOUSE_BITE_CLEARANCE_MM <= bite_clearance <= MAX_MOUSE_BITE_CLEARANCE_MM:
        raise ValueError(
            f"mouse-bite edge clearance must be {MIN_MOUSE_BITE_CLEARANCE_MM:g} "
            f"to {MAX_MOUSE_BITE_CLEARANCE_MM:g} mm; JLCPCB recommends "
            "0.35 to 0.4 mm"
        )
    bounds = edge_bounds(source)
    tab_orientation = tab_edge_orientation(bounds, tab_width)
    width = count_x * bounds.width + (count_x - 1) * gap + 2 * (rail + gap)
    height = count_y * bounds.height + (count_y - 1) * gap + 2 * (rail + gap)
    page = page_dimensions(source) if center_on_page else None
    origin_x = (page[0] - width) / 2 if page else 0.0
    origin_y = (page[1] - height) / 2 if page else 0.0
    result: Node = ["kicad_pcb"]
    result.extend(
        copy.deepcopy(item)
        for item in source[1:]
        if isinstance(item, list) and head(item) in STRUCTURAL
    )
    source_items = [
        item
        for item in source[1:]
        if isinstance(item, list)
        and head(item) not in STRUCTURAL
        and not is_edge_item(item)
    ]
    source_contour = edge_contour_points(source)
    solid_polygons = [
        _rectangle(origin_x, origin_y, origin_x + width, origin_y + rail),
        _rectangle(
            origin_x, origin_y + height - rail, origin_x + width, origin_y + height
        ),
        _rectangle(origin_x, origin_y, origin_x + rail, origin_y + height),
        _rectangle(
            origin_x + width - rail, origin_y, origin_x + width, origin_y + height
        ),
    ]
    bite_number = 1
    for row in range(count_y):
        for column in range(count_x):
            suffix = f"@X{column + 1}Y{row + 1}"
            dx = origin_x + rail + gap + column * (bounds.width + gap) - bounds.left
            dy = origin_y + rail + gap + row * (bounds.height + gap) - bounds.top
            for original in source_items:
                item = copy.deepcopy(original)
                renew_uuids(item)
                remap_nets(item, suffix)
                make_reference_unique(item, f"_X{column + 1}Y{row + 1}")
                translate_item(item, dx, dy)
                remove_zone_fills(item)
                result.append(item)
            x0, x1 = (
                origin_x + rail + gap + column * (bounds.width + gap),
                origin_x + rail + gap + column * (bounds.width + gap) + bounds.width,
            )
            y0, y1 = (
                origin_y + rail + gap + row * (bounds.height + gap),
                origin_y + rail + gap + row * (bounds.height + gap) + bounds.height,
            )
            solid_polygons.append([(x + dx, y + dy) for x, y in source_contour])
            if tab_orientation == "horizontal":
                tab_left = (x0 + x1 - tab_width) / 2
                tab_right = tab_left + tab_width
                solid_polygons.extend(
                    [
                        _rectangle(tab_left, y0 - gap, tab_right, y0),
                        _rectangle(tab_left, y1, tab_right, y1 + gap),
                    ]
                )
                bite_coordinates = (
                    (
                        x,
                        y - MOUSE_BITE_OUTWARD_OFFSET_MM
                        if y == y0
                        else y + MOUSE_BITE_OUTWARD_OFFSET_MM,
                    )
                    for x in bite_positions(
                        (x0 + x1) / 2,
                        tab_width,
                        bite_diameter,
                        bite_clearance,
                    )
                    for y in (y0, y1)
                )
            else:
                tab_top = (y0 + y1 - tab_width) / 2
                tab_bottom = tab_top + tab_width
                solid_polygons.extend(
                    [
                        _rectangle(x0 - gap, tab_top, x0, tab_bottom),
                        _rectangle(x1, tab_top, x1 + gap, tab_bottom),
                    ]
                )
                bite_coordinates = (
                    (
                        x - MOUSE_BITE_OUTWARD_OFFSET_MM
                        if x == x0
                        else x + MOUSE_BITE_OUTWARD_OFFSET_MM,
                        y,
                    )
                    for y in bite_positions(
                        (y0 + y1) / 2,
                        tab_width,
                        bite_diameter,
                        bite_clearance,
                    )
                    for x in (x0, x1)
                )
            for x, y in bite_coordinates:
                result.append(mouse_bite(f"MB{bite_number}", x, y, bite_diameter))
                bite_number += 1
    result.extend(graphic_polygon(ring) for ring in union_polygon_rings(solid_polygons))
    fiducial_x_left = origin_x + rail + FIDUCIAL_HORIZONTAL_CLEARANCE_MM
    fiducial_x_right = origin_x + width - rail - FIDUCIAL_HORIZONTAL_CLEARANCE_MM
    tooling_inset = TOOLING_HOLE_EDGE_OFFSET_MM
    result.extend(
        [
            # Four global fiducials sit in the horizontal process rails. Their Y
            # centres satisfy JLCPCB's 3.85 mm edge offset, while moving them away
            # from the corners leaves clearance for the four tooling holes.
            fiducial(
                fiducial_template,
                "PFID1",
                fiducial_x_left,
                origin_y + FIDUCIAL_EDGE_OFFSET_MM,
            ),
            fiducial(
                fiducial_template,
                "PFID2",
                fiducial_x_right,
                origin_y + FIDUCIAL_EDGE_OFFSET_MM,
            ),
            fiducial(
                fiducial_template,
                "PFID3",
                fiducial_x_left,
                origin_y + height - FIDUCIAL_EDGE_OFFSET_MM,
            ),
            fiducial(
                fiducial_template,
                "PFID4",
                fiducial_x_right,
                origin_y + height - FIDUCIAL_EDGE_OFFSET_MM,
            ),
            # JLCPCB panel tooling holes: four 2 mm NPTH holes in the process-rail
            # corners, 2.5 mm from each panel edge and clear of the fiducials.
            npth_hole(
                "TH1",
                "PanelToolingHole_2mm",
                origin_x + tooling_inset,
                origin_y + tooling_inset,
                TOOLING_HOLE_DIAMETER_MM,
            ),
            npth_hole(
                "TH2",
                "PanelToolingHole_2mm",
                origin_x + width - tooling_inset,
                origin_y + tooling_inset,
                TOOLING_HOLE_DIAMETER_MM,
            ),
            npth_hole(
                "TH3",
                "PanelToolingHole_2mm",
                origin_x + tooling_inset,
                origin_y + height - tooling_inset,
                TOOLING_HOLE_DIAMETER_MM,
            ),
            npth_hole(
                "TH4",
                "PanelToolingHole_2mm",
                origin_x + width - tooling_inset,
                origin_y + height - tooling_inset,
                TOOLING_HOLE_DIAMETER_MM,
            ),
            ["embedded_fonts", "no"],
        ]
    )
    return result, Bounds(origin_x, origin_y, origin_x + width, origin_y + height)


def validation_summary(
    *,
    source_path: Path,
    output_path: Path,
    source_bounds: Bounds,
    panel_bounds: Bounds,
    count_x: int,
    count_y: int,
    gap: float,
    rail: float,
    tab_width: float,
    bite_diameter: float,
    bite_clearance: float,
    fiducial_path: Path,
    drc_checked: bool,
) -> str:
    """Return a self-contained report suitable for independent review."""
    boards = count_x * count_y
    tabs = boards * 2
    tab_orientation = tab_edge_orientation(source_bounds, tab_width)
    tab_edges = (
        "top and bottom" if tab_orientation == "horizontal" else "left and right"
    )
    holes_per_tab = len(bite_positions(0.0, tab_width, bite_diameter, bite_clearance))
    drc_result = (
        "PASS: 0 violations; 0 unconnected items; all routing cutouts closed"
        if drc_checked
        else "NOT RUN (--no-kicad-check was used)"
    )
    return "\n".join(
        [
            "=== ROUTED PCB PANEL VALIDATION SUMMARY ===",
            f"Source PCB: {source_path}",
            f"Generated panel: {output_path}",
            "Panelization method: CNC-routed gaps with NPTH mouse-bite breakaway tabs",
            f"Array: {count_x} columns x {count_y} rows = {boards} identical PCBs",
            f"Source Edge.Cuts envelope: {source_bounds.width:.3f} x {source_bounds.height:.3f} mm",
            f"Finished panel Edge.Cuts: {panel_bounds.width:.3f} x {panel_bounds.height:.3f} mm",
            f"Drawing-sheet placement: centred; Edge.Cuts top-left at ({panel_bounds.left:.3f}, {panel_bounds.top:.3f}) mm",
            f"Routing gap between PCB envelopes: {gap:.3f} mm",
            f"Routing gap between PCB array and process rails: {gap:.3f} mm",
            f"Perimeter process rail: {rail:.3f} mm on all four sides",
            "Source outline handling: copied for every PCB; non-rectangular geometry is preserved",
            f"Breakaway placement: one centred tab on each PCB {tab_edges} edge",
            f"Breakaway tabs: {tabs} total; {tab_width:.3f} mm nominal width",
            f"Mouse bites: {holes_per_tab} holes/tab, {tabs * holes_per_tab} holes total; {bite_diameter:.3f} mm NPTH diameter; {bite_clearance:.3f} mm edge-to-edge spacing",
            "Global fiducials: 4; 1 mm copper / 2 mm mask; centres 3.850 mm from top/bottom panel edges",
            f"Fiducial footprint source: {fiducial_path}",
            "Panel tooling holes: 4; 2.000 mm NPTH; centres 2.500 mm from adjacent panel edges",
            "Edge.Cuts topology: one closed rectangular exterior plus closed internal routing cutouts",
            f"KiCad panel DRC: {drc_result}",
            "Source-file integrity: PASS (source bytes unchanged)",
            "Ordering intent: customer-supplied routed mouse-bite panel",
            "Castellated Holes option: NPTH mouse bites do not require it; select it only when the finished source PCB has plated half-holes on an edge.",
            "Review limits: verify copper-to-route clearances, tab locations, component overhang, fabrication limits, and Gerber/drill output before ordering.",
            "=== END VALIDATION SUMMARY ===",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-x", "--count-x", type=int, required=True)
    parser.add_argument("-y", "--count-y", type=int, required=True)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--gap",
        type=float,
        default=DEFAULT_GAP_MM,
        help=(
            f"routed space between PCBs (default: {DEFAULT_GAP_MM:g} mm; "
            f"script minimum: {MIN_GAP_MM:g} mm)"
        ),
    )
    parser.add_argument(
        "--rail",
        type=float,
        default=DEFAULT_RAIL_MM,
        help=f"perimeter process rail (default/minimum: {DEFAULT_RAIL_MM:g} mm)",
    )
    parser.add_argument(
        "--tab-width",
        type=float,
        default=DEFAULT_TAB_WIDTH_MM,
        help=(
            f"solid breakaway-tab width (default/minimum: {DEFAULT_TAB_WIDTH_MM:g} mm)"
        ),
    )
    parser.add_argument(
        "--mouse-bite-diameter",
        type=float,
        default=DEFAULT_MOUSE_BITE_DIAMETER_MM,
        help=(
            f"NPTH drill diameter (default: {DEFAULT_MOUSE_BITE_DIAMETER_MM:g} mm; "
            f"allowed: {MIN_MOUSE_BITE_DIAMETER_MM:g}-"
            f"{MAX_MOUSE_BITE_DIAMETER_MM:g} mm)"
        ),
    )
    parser.add_argument(
        "--mouse-bite-clearance",
        type=float,
        default=DEFAULT_MOUSE_BITE_CLEARANCE_MM,
        help=(
            f"hole edge-to-edge spacing (default: "
            f"{DEFAULT_MOUSE_BITE_CLEARANCE_MM:g} mm; allowed: "
            f"{MIN_MOUSE_BITE_CLEARANCE_MM:g}-"
            f"{MAX_MOUSE_BITE_CLEARANCE_MM:g} mm)"
        ),
    )
    parser.add_argument("--fiducial-footprint", type=Path)
    parser.add_argument("--kicad-cli")
    parser.add_argument("--no-kicad-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.count_x < 1 or args.count_y < 1:
        raise SystemExit("count-x and count-y must be positive")
    source_path = args.input.resolve()
    output_path = (
        args.output
        or source_path.parent / "manufacture" /
        (
            f"{source_path.stem}_routed_panel_{args.count_x}x{args.count_y}.kicad_pcb"
        )
    ).resolve()
    if source_path == output_path:
        raise SystemExit("output must differ from input")
    if output_path.exists() and not args.force:
        raise SystemExit(f"output already exists: {output_path} (use --force)")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = source_path.read_bytes()
    source = parse_sexpr(source_bytes.decode("utf-8-sig"))
    source_bounds = edge_bounds(source)
    fid_path = find_fiducial_library_file(args.fiducial_footprint)
    panel, panel_bounds = build_routed_panel(
        source,
        args.count_x,
        args.count_y,
        args.gap,
        args.rail,
        args.tab_width,
        args.mouse_bite_diameter,
        args.mouse_bite_clearance,
        load_fiducial_template(fid_path),
    )
    output_path.write_text(dump_sexpr(panel) + "\n", encoding="utf-8", newline="\n")
    if not args.no_kicad_check:
        cli = find_kicad_cli(args.kicad_cli)
        if not cli:
            output_path.unlink(missing_ok=True)
            raise SystemExit("KiCad 10 kicad-cli not found")
        report = output_path.with_name(f".{output_path.stem}.panelize-drc.json")
        completed = subprocess.run(
            cli
            + [
                "pcb",
                "drc",
                "--refill-zones",
                "--save-board",
                "--format",
                "json",
                "--output",
                str(report),
                str(output_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        drc = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
        report.unlink(missing_ok=True)
        if completed.returncode:
            print(completed.stdout, end="")
            print(completed.stderr, end="")
            output_path.unlink(missing_ok=True)
            raise SystemExit("KiCad rejected the routed panel")
        unexpected = drc.get("violations", [])
        unconnected = drc.get("unconnected_items", [])
        if unexpected or unconnected:
            print(completed.stdout, end="")
            print(completed.stderr, end="")
            output_path.unlink(missing_ok=True)
            raise SystemExit(
                "routed panel failed DRC: "
                f"{len(unexpected)} non-tab violation(s), "
                f"{len(unconnected)} unconnected item(s)"
            )
    if source_path.read_bytes() != source_bytes:
        raise RuntimeError("source PCB changed unexpectedly")
    print(
        validation_summary(
            source_path=source_path,
            output_path=output_path,
            source_bounds=source_bounds,
            panel_bounds=panel_bounds,
            count_x=args.count_x,
            count_y=args.count_y,
            gap=args.gap,
            rail=args.rail,
            tab_width=args.tab_width,
            bite_diameter=args.mouse_bite_diameter,
            bite_clearance=args.mouse_bite_clearance,
            fiducial_path=fid_path,
            drc_checked=not args.no_kicad_check,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
