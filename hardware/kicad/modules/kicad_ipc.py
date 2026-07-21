"""Shared helpers for KiCad's supported ``kipy`` IPC API.

All dimensions in the IPC protocol are integer nanometres.  Mutating scripts
must use :func:`editor_commit`: it groups their updates into one named PCB
Editor transaction, making the entire script operation available through the
normal Undo and Redo commands.  Dropping a failed transaction prevents partial
changes from remaining in the editor.
"""

from contextlib import contextmanager
import math
from pathlib import Path
import re

from kipy import KiCad
from kipy.geometry import Box2, Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer
from kipy.util import from_mm, to_mm


def connect_board():
    """Connect to the running PCB Editor and return its client and open board.

    KiCad 10 must have Preferences > Plugins > API server enabled.  The
    official client automatically detects both native and Flatpak socket paths.
    We intentionally do not call ``check_version`` because the latest released
    binding targets KiCad 10.0.1 and rejects compatible newer 10.0.x patches.
    """
    client = KiCad(timeout_ms=5000)
    client.ping()
    return client, client.get_board()


def board_document_path(document):
    """Return the absolute file path represented by an IPC PCB document."""
    board_path = Path(document.board_filename)
    if board_path.is_absolute():
        return board_path.resolve()
    return (Path(document.project.path) / board_path).resolve()


def _normalized_board_tokens(contents):
    """Tokenize PCB content while ignoring IPC serializer-only differences."""
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', contents)
    ignored_expressions = {
        "filled_polygon",
        "generator",
        "generator_version",
        "version",
    }
    normalized = []
    index = 0
    while index < len(tokens):
        if (
            tokens[index] == "("
            and index + 1 < len(tokens)
            and tokens[index + 1] in ignored_expressions
        ):
            depth = 0
            while index < len(tokens):
                if tokens[index] == "(":
                    depth += 1
                elif tokens[index] == ")":
                    depth -= 1
                index += 1
                if depth == 0:
                    break
            continue
        normalized.append(tokens[index])
        index += 1
    return normalized


def board_has_unsaved_changes(board, saved_path=None):
    """Return whether an open board differs meaningfully from its saved file.

    KiCad's ``get_as_string`` output uses different whitespace and adds
    serializer metadata to embedded footprints, even immediately after Save.
    It can also omit cached zone-fill polygons written by ``kicad-cli``.
    Comparing normalized S-expression tokens avoids those false positives
    while retaining changes to editable board content and zone outlines.
    """
    path = (
        Path(saved_path).resolve()
        if saved_path is not None
        else board_document_path(board.document)
    )
    live_tokens = _normalized_board_tokens(board.get_as_string())
    saved_tokens = _normalized_board_tokens(path.read_text(encoding="utf-8"))
    return live_tokens != saved_tokens


@contextmanager
def editor_commit(board, message, refill_zones=False):
    """Wrap board changes in one atomic PCB Editor undo/redo transaction.

    Callers modify retrieved item wrappers and send them with
    ``board.update_items`` (or create/remove calls) inside this context.  A
    successful exit pushes a single named entry to the editor history.  Any
    exception raised while staging changes drops the transaction before
    re-raising it.

    Set ``refill_zones`` when the staged edits affect zone outlines, board
    edges, pads, tracks, or other copper connectivity. KiCad does not expose
    staged items to the zone filler, so the blocking all-zone refill must run
    after ``push_commit`` publishes them. Centralizing that ordering here keeps
    every mutating script consistent with PCB Editor's B / Fill All Zones
    operation.
    """
    commit = board.begin_commit()
    try:
        yield
    except Exception:
        board.drop_commit(commit)
        raise
    else:
        board.push_commit(commit, message)
        if refill_zones:
            refill_all_zones(board)


def refill_all_zones(board):
    """Block until KiCad rebuilds every zone against the live board state.

    An empty zone list in KiCad's IPC ``RefillZones`` request means all zones;
    ``kipy`` exposes that operation as ``Board.refill_zones``. Blocking avoids
    returning control while the editor is still busy and ensures its copper
    fills and connectivity/ratsnest display have been recalculated before the
    script reports success.

    This function must be called only after any related editor commit has been
    pushed. Items inside an open commit are staged and invisible to the filler.
    Prefer ``editor_commit(..., refill_zones=True)`` over calling it directly.
    """
    board.refill_zones(block=True)


def vector(x, y):
    """Create an IPC point/vector from integer nanometre coordinates."""
    return Vector2.from_xy(int(x), int(y))


def point_from_mm(x_mm, y_mm):
    """Create an IPC point from human-readable millimetre coordinates."""
    return Vector2.from_xy_mm(x_mm, y_mm)


def distance(first, second):
    """Return Euclidean point distance in nanometres."""
    return math.hypot(first.x - second.x, first.y - second.y)


def same_point(first, second):
    """Return whether two IPC points have identical coordinates."""
    return first.x == second.x and first.y == second.y


def is_horizontal(first, second):
    """Return whether a segment has no Y-axis change."""
    return first.y == second.y


def is_vertical(first, second):
    """Return whether a segment has no X-axis change."""
    return first.x == second.x


def box_edges(box):
    """Return left, right, top and bottom coordinates for an IPC ``Box2``.

    KiCad uses screen-style coordinates: X increases rightwards and Y
    downwards, so the top edge has the smaller Y value.  IPC may represent a
    rotated or reversed shape with a negative box width or height.  Sorting
    each endpoint pair guarantees geometric left/right/top/bottom ordering
    regardless of the sign of ``box.size``.
    """
    first_x = box.pos.x
    second_x = box.pos.x + box.size.x
    first_y = box.pos.y
    second_y = box.pos.y + box.size.y
    return (
        min(first_x, second_x),
        max(first_x, second_x),
        min(first_y, second_y),
        max(first_y, second_y),
    )


def box_center(box):
    """Return the integer centre point of an IPC bounding box."""
    left, right, top, bottom = box_edges(box)
    return vector((left + right) // 2, (top + bottom) // 2)


def merge_boxes(boxes):
    """Return the smallest box containing every non-empty input box."""
    boxes = list(boxes)
    if not boxes:
        raise RuntimeError("no geometry was available for a bounding box")
    left = min(box_edges(box)[0] for box in boxes)
    right = max(box_edges(box)[1] for box in boxes)
    top = min(box_edges(box)[2] for box in boxes)
    bottom = max(box_edges(box)[3] for box in boxes)
    return Box2.from_xywh(left, top, right - left, bottom - top)


def board_edge_bounds(board):
    """Return the bounds of all board graphics on the Edge.Cuts layer."""
    boxes = [
        shape.bounding_box()
        for shape in board.get_shapes()
        if shape.layer == BoardLayer.BL_Edge_Cuts
    ]
    return box_edges(merge_boxes(boxes))


def footprint_reference(footprint):
    """Return the displayed reference string of an IPC footprint instance."""
    return footprint.reference_field.text.value


def footprints_by_reference(board):
    """Index all board footprints by their reference designator."""
    return {footprint_reference(fp): fp for fp in board.get_footprints()}


def courtyard_box(footprint):
    """Return the merged courtyard graphics box for a footprint instance.

    Footprint child geometry received through IPC already uses absolute board
    coordinates.  Front footprints use F.CrtYd and back footprints B.CrtYd.
    """
    layer = (
        BoardLayer.BL_B_CrtYd
        if footprint.layer == BoardLayer.BL_B_Cu
        else BoardLayer.BL_F_CrtYd
    )
    return merge_boxes(
        shape.bounding_box()
        for shape in footprint.definition.shapes
        if shape.layer == layer
    )


def text_box(client, text):
    """Ask KiCad for the rendered bounding box of a board-text object."""
    return client.get_text_extents(text.as_text())


def move_text_center(client, text, target_center):
    """Move text so its rendered box centre reaches ``target_center``."""
    current_center = box_center(text_box(client, text))
    text.position = text.position + (target_center - current_center)


__all__ = [
    "BoardLayer", "board_document_path", "board_edge_bounds",
    "board_has_unsaved_changes", "box_center", "box_edges", "connect_board",
    "courtyard_box", "distance", "editor_commit", "footprint_reference",
    "footprints_by_reference", "from_mm", "is_horizontal", "is_vertical",
    "merge_boxes", "move_text_center", "point_from_mm", "refill_all_zones",
    "same_point", "text_box", "to_mm", "vector",
]
