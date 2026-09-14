#!/usr/bin/env python3
"""Create a V-scored PCB panel without modifying the source board.

The generated panel is a standalone KiCad 10 board.  Source board items are
copied into an X/Y grid, their UUIDs and nets are made unique per instance,
the individual Edge.Cuts are replaced by one panel outline, and V-score lines
are placed on User.Drawings.  Three global fiducials are added to the rails.

This intentionally supports V-scoring only: every finished PCB is the
rectangular envelope of the source Edge.Cuts.  Rounded source corners therefore
become square in the manufactured panel.  Use a routed/tab panelizer if the
exact non-rectangular outline must be retained.
"""

from __future__ import annotations

import argparse
import copy
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


Atom = str
Node = list["Atom | Node"]


class SExprError(ValueError):
    pass


TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+')


def parse_sexpr(text: str) -> Node:
    """Parse one KiCad S-expression while retaining quoted atoms."""
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
    """Serialize an S-expression in a compact, KiCad-readable layout."""
    if not node:
        return "()"
    head = str(node[0])
    if all(not isinstance(value, list) for value in node):
        return "(" + " ".join(str(value) for value in node) + ")"
    indent = "\t" * level
    child_indent = "\t" * (level + 1)
    parts = ["(" + head]
    for value in node[1:]:
        if isinstance(value, list):
            parts.append("\n" + child_indent + dump_sexpr(value, level + 1))
        else:
            if parts[-1].endswith("\n"):
                parts.append(child_indent + str(value))
            else:
                parts.append(" " + str(value))
    parts.append(")")
    return "".join(parts)


def head(node: Node) -> str:
    return str(node[0]) if node else ""


def children(node: Node, name: str) -> list[Node]:
    return [value for value in node[1:] if isinstance(value, list) and head(value) == name]


def first_child(node: Node, name: str) -> Node | None:
    found = children(node, name)
    return found[0] if found else None


def quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def translate_pair(node: Node, dx: float, dy: float) -> None:
    if len(node) >= 3:
        node[1] = number(float(str(node[1])) + dx)
        node[2] = number(float(str(node[2])) + dy)


def walk(node: Node):
    yield node
    for value in node[1:]:
        if isinstance(value, list):
            yield from walk(value)


def translate_item(item: Node, dx: float, dy: float) -> None:
    """Translate one top-level board item without moving footprint internals."""
    kind = head(item)
    if kind == "footprint":
        at = first_child(item, "at")
        if at:
            translate_pair(at, dx, dy)
        return
    coordinate_names = {
        "at", "start", "mid", "end", "center", "xy", "position",
    }
    for node in walk(item):
        if head(node) in coordinate_names:
            translate_pair(node, dx, dy)


def remove_zone_fills(item: Node) -> None:
    item[:] = [
        value for value in item
        if not (isinstance(value, list) and head(value) == "filled_polygon")
    ]
    for value in item[1:]:
        if isinstance(value, list):
            remove_zone_fills(value)


def renew_uuids(item: Node) -> None:
    replacements: dict[str, str] = {}
    for node in walk(item):
        if head(node) in {"uuid", "tstamp"} and len(node) > 1:
            old = str(node[1]).strip('"')
            replacements[old] = str(uuid.uuid4())
    for node in walk(item):
        for index, value in enumerate(node):
            if isinstance(value, str):
                bare = value.strip('"')
                if bare in replacements:
                    node[index] = quoted(replacements[bare]) if value.startswith('"') else replacements[bare]


def remap_nets(item: Node, net_map: dict[int, int], suffix: str) -> None:
    for node in walk(item):
        if head(node) == "net" and len(node) >= 2:
            raw_net = str(node[1])
            # KiCad 10's current board format identifies an item's net by name:
            #     (net "/VOUT")
            # Give each physical PCB its own name so connectivity does not span
            # otherwise isolated panel copies.
            if raw_net.startswith('"'):
                net_name = raw_net.strip('"')
                if net_name:
                    node[1] = quoted(net_name + suffix)
                continue
            # Retain compatibility with older numeric board serialization:
            #     (net 3 "/VOUT")
            try:
                old = int(raw_net)
            except ValueError:
                continue
            node[1] = str(net_map.get(old, old))
            if len(node) >= 3 and old != 0:
                node[2] = quoted(str(node[2]).strip('"') + suffix)


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


def has_non_rectangular_edges(root: Node) -> bool:
    """Return true when Edge.Cuts contains curves or diagonal line segments."""
    for item in root[1:]:
        if not isinstance(item, list) or not head(item).startswith("gr_"):
            continue
        layer = first_child(item, "layer")
        if not layer or len(layer) < 2 or str(layer[1]).strip('"') != "Edge.Cuts":
            continue
        if head(item) != "gr_line":
            return True
        start, end = first_child(item, "start"), first_child(item, "end")
        if not start or not end or (start[1] != end[1] and start[2] != end[2]):
            return True
    return False


def graphic_line(x1: float, y1: float, x2: float, y2: float, layer: str, width: float) -> Node:
    return [
        "gr_line", ["start", number(x1), number(y1)], ["end", number(x2), number(y2)],
        ["stroke", ["width", number(width)], ["type", "default"]],
        ["layer", quoted(layer)], ["uuid", quoted(str(uuid.uuid4()))],
    ]


FIDUCIAL_RELATIVE_PATH = Path("Fiducial.pretty") / "Fiducial_1mm_Mask2mm.kicad_mod"


def find_fiducial_library_file(explicit: Path | None = None) -> Path:
    """Locate KiCad's installed standard fiducial footprint."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    footprint_dir = os.environ.get("KICAD10_FOOTPRINT_DIR")
    if footprint_dir:
        candidates.append(Path(footprint_dir) / FIDUCIAL_RELATIVE_PATH)
    candidates.extend([
        Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints") / FIDUCIAL_RELATIVE_PATH,
        Path("/usr/share/kicad/footprints") / FIDUCIAL_RELATIVE_PATH,
        Path("/usr/local/share/kicad/footprints") / FIDUCIAL_RELATIVE_PATH,
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints") / FIDUCIAL_RELATIVE_PATH,
    ])
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "KiCad 10 library footprint Fiducial:Fiducial_1mm_Mask2mm was not found; "
        "pass --fiducial-footprint or set KICAD10_FOOTPRINT_DIR"
    )


def load_fiducial_template(path: Path) -> Node:
    template = parse_sexpr(path.read_text(encoding="utf-8-sig"))
    if head(template) != "footprint":
        raise SExprError(f"not a footprint file: {path}")
    return template


def fiducial(template: Node, reference: str, x: float, y: float) -> Node:
    """Instantiate the installed KiCad library footprint on the panel."""
    result = copy.deepcopy(template)
    result[1] = quoted("Fiducial:Fiducial_1mm_Mask2mm")
    # Library-only serialization metadata is not stored in an embedded board
    # footprint. KiCad assigns UUIDs to the footprint and its graphical items.
    result[:] = [
        value for value in result
        if not (isinstance(value, list) and head(value) in {"version", "generator"})
    ]
    layer_index = next(
        index for index, value in enumerate(result)
        if isinstance(value, list) and head(value) == "layer"
    )
    result.insert(layer_index + 1, ["uuid", quoted(str(uuid.uuid4()))])
    result.insert(layer_index + 2, ["at", number(x), number(y)])
    reference_property = next(
        value for value in result
        if isinstance(value, list) and head(value) == "property"
        and len(value) >= 3 and str(value[1]).strip('"') == "Reference"
    )
    reference_property[2] = quoted(reference)
    if not first_child(reference_property, "hide"):
        # Global fiducial references are manufacturing metadata, not panel
        # silkscreen. Hiding the instance field also prevents edge-clearance
        # warnings when the library's default text extends beyond a narrow rail.
        layer_position = next(
            index for index, value in enumerate(reference_property)
            if isinstance(value, list) and head(value) == "layer"
        )
        reference_property.insert(layer_position + 1, ["hide", "yes"])
    for node in walk(result):
        if node is result:
            continue
        if (head(node).startswith("fp_") or head(node) == "pad") and not first_child(node, "uuid"):
            node.append(["uuid", quoted(str(uuid.uuid4()))])
    return result


STRUCTURAL = {"version", "generator", "generator_version", "general", "paper", "layers", "setup", "embedded_fonts"}


def build_panel(
    source: Node,
    count_x: int,
    count_y: int,
    rail: float,
    gap: float = 2.0,
    fiducial_template: Node | None = None,
) -> tuple[Node, Bounds]:
    bounds = edge_bounds(source)
    if bounds.width <= 0 or bounds.height <= 0:
        raise SExprError("source Edge.Cuts has zero width or height")
    if rail < 3.0:
        raise ValueError("rail must be at least 3 mm to contain 2 mm fiducials safely")
    if gap < 0:
        raise ValueError("gap must not be negative")
    if fiducial_template is None:
        fiducial_template = load_fiducial_template(find_fiducial_library_file())

    panel_width = count_x * bounds.width + (count_x - 1) * gap + 2 * rail
    panel_height = count_y * bounds.height + (count_y - 1) * gap + 2 * rail
    result: Node = ["kicad_pcb"]
    for item in source[1:]:
        if isinstance(item, list) and head(item) in STRUCTURAL:
            result.append(copy.deepcopy(item))

    source_nets: list[tuple[int, str]] = []
    source_items: list[Node] = []
    for item in source[1:]:
        if not isinstance(item, list) or head(item) in STRUCTURAL:
            continue
        if head(item) == "net" and len(item) >= 3:
            source_nets.append((int(str(item[1])), str(item[2]).strip('"')))
        elif head(item).startswith("gr_"):
            layer = first_child(item, "layer")
            if layer and len(layer) >= 2 and str(layer[1]).strip('"') == "Edge.Cuts":
                continue
            source_items.append(item)
        else:
            source_items.append(item)

    if source_nets:
        result.append(["net", "0", quoted("")])
    next_net = 1
    for row in range(count_y):
        for column in range(count_x):
            suffix = f"@X{column + 1}Y{row + 1}"
            net_map = {0: 0}
            for old_id, old_name in source_nets:
                if old_id == 0:
                    continue
                net_map[old_id] = next_net
                result.append(["net", str(next_net), quoted(old_name + suffix)])
                next_net += 1
            dx = rail + column * (bounds.width + gap) - bounds.left
            dy = rail + row * (bounds.height + gap) - bounds.top
            for original in source_items:
                item = copy.deepcopy(original)
                renew_uuids(item)
                remap_nets(item, net_map, suffix)
                translate_item(item, dx, dy)
                remove_zone_fills(item)
                result.append(item)

    # One continuous routed panel outline. Internal score locations live on
    # User.Drawings because Edge.Cuts would incorrectly make them routed slots.
    result.extend([
        graphic_line(0, 0, panel_width, 0, "Edge.Cuts", 0.1),
        graphic_line(panel_width, 0, panel_width, panel_height, "Edge.Cuts", 0.1),
        graphic_line(panel_width, panel_height, 0, panel_height, "Edge.Cuts", 0.1),
        graphic_line(0, panel_height, 0, 0, "Edge.Cuts", 0.1),
    ])
    # Score both sides of every circuit row/column. With a nonzero gap, the
    # intervening strip becomes removable scrap and keeps edge copper (such as
    # the sample board's castellations) from touching the next PCB.
    vertical_scores = {
        rail + column * (bounds.width + gap) + side * bounds.width
        for column in range(count_x) for side in (0, 1)
    }
    horizontal_scores = {
        rail + row * (bounds.height + gap) + side * bounds.height
        for row in range(count_y) for side in (0, 1)
    }
    for x in sorted(vertical_scores):
        result.append(graphic_line(x, 0, x, panel_height, "Dwgs.User", 0.15))
    for y in sorted(horizontal_scores):
        result.append(graphic_line(0, y, panel_width, y, "Dwgs.User", 0.15))

    inset = rail / 2
    result.extend([
        fiducial(fiducial_template, "PFID1", inset, inset),
        fiducial(fiducial_template, "PFID2", panel_width - inset, inset),
        fiducial(fiducial_template, "PFID3", inset, panel_height - inset),
    ])
    result.append(["embedded_fonts", "no"])
    return result, Bounds(0, 0, panel_width, panel_height)


def find_kicad_cli(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    found = shutil.which("kicad-cli")
    if found:
        return found
    windows = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
    return str(windows) if windows.exists() else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="source .kicad_pcb (read-only)")
    parser.add_argument("-x", "--count-x", type=int, required=True, help="PCB columns")
    parser.add_argument("-y", "--count-y", type=int, required=True, help="PCB rows")
    parser.add_argument("-o", "--output", type=Path, help="output .kicad_pcb")
    parser.add_argument("--rail", type=float, default=5.0, help="rail width in mm (default: 5)")
    parser.add_argument("--gap", type=float, default=2.0, help="scrap gap between PCBs in mm (default: 2)")
    parser.add_argument("--kicad-cli", help="path to KiCad 10 kicad-cli")
    parser.add_argument(
        "--fiducial-footprint", type=Path,
        help="installed Fiducial_1mm_Mask2mm.kicad_mod (normally auto-detected)",
    )
    parser.add_argument("--no-kicad-check", action="store_true", help="skip KiCad parse/resave check")
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.count_x < 1 or args.count_y < 1:
        raise SystemExit("count-x and count-y must both be positive")
    source_path = args.input.resolve()
    output_path = (args.output or source_path.with_name(
        f"{source_path.stem}_panel_{args.count_x}x{args.count_y}.kicad_pcb"
    )).resolve()
    if source_path == output_path:
        raise SystemExit("output must differ from input; the source PCB is never modified")
    if output_path.exists() and not args.force:
        raise SystemExit(f"output already exists: {output_path} (use --force to replace it)")

    source_bytes = source_path.read_bytes()
    source = parse_sexpr(source_bytes.decode("utf-8-sig"))
    non_rectangular = has_non_rectangular_edges(source)
    fiducial_path = find_fiducial_library_file(args.fiducial_footprint)
    fiducial_template = load_fiducial_template(fiducial_path)
    panel, bounds = build_panel(
        source, args.count_x, args.count_y, args.rail, args.gap, fiducial_template
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_sexpr(panel) + "\n", encoding="utf-8", newline="\n")

    cli = find_kicad_cli(args.kicad_cli)
    if not args.no_kicad_check:
        if not cli:
            output_path.unlink(missing_ok=True)
            raise SystemExit("KiCad 10 kicad-cli not found; pass --kicad-cli or --no-kicad-check")
        drc_report = output_path.with_name(f".{output_path.stem}.panelize-drc.json")
        completed = subprocess.run([
            cli, "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--output", str(drc_report), str(output_path),
        ], text=True)
        drc_report.unlink(missing_ok=True)
        if completed.returncode:
            output_path.unlink(missing_ok=True)
            raise SystemExit(f"KiCad rejected the generated panel (exit {completed.returncode})")

    if source_path.read_bytes() != source_bytes:
        raise RuntimeError("source PCB changed unexpectedly")
    print(f"Created {args.count_x} x {args.count_y} panel: {output_path}")
    print(f"Fiducial library source: {fiducial_path}")
    print(
        f"Panel size: {bounds.width:.3f} x {bounds.height:.3f} mm; "
        f"rail: {args.rail:.3f} mm; gap: {args.gap:.3f} mm"
    )
    if non_rectangular:
        print("WARNING: source outline is non-rectangular; V-scoring produces its rectangular envelope.")
    print("V-score centre lines are on User.Drawings; confirm them with the fabricator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
