"""Shared KiCad PCB Editor API and geometry helpers.

This module contains small, board-independent operations used by the PCB Editor
console scripts in this directory. It deliberately does not contain project
settings or perform edits when imported: callers remain responsible for
choosing footprints, changing the board, refreshing the canvas, and saving.

The console scripts are normally launched with ``runpy.run_path``. Each script
adds its own directory to ``sys.path`` before importing this module because
KiCad's embedded Python console does not automatically add the executed file's
directory when a file is evaluated indirectly.
"""

import math

import pcbnew


def mm_to_iu(value_mm):
    """Convert a millimetre measurement to KiCad internal units.

    Board coordinates and dimensions exposed by ``pcbnew`` are integer internal
    units rather than floating-point millimetres. Going through KiCad's own
    conversion function avoids embedding a scale factor that could differ
    between old and new API versions.
    """
    return pcbnew.FromMM(value_mm)


def iu_to_mm(value_iu):
    """Convert a KiCad internal-unit measurement to millimetres.

    This is primarily useful at display boundaries. Geometry should stay in
    integer internal units until a value is printed so calculations do not
    accumulate floating-point rounding errors.
    """
    return pcbnew.ToMM(value_iu)


def vector(x, y):
    """Create an integer ``VECTOR2I`` from two coordinate-like values.

    KiCad geometry setters require integer vectors. Explicit conversion makes
    this helper safe for calculations that temporarily produce floats while
    retaining KiCad's normal truncation behaviour.
    """
    return pcbnew.VECTOR2I(int(x), int(y))


def point_from_mm(x_mm, y_mm):
    """Create a KiCad point from X and Y coordinates expressed in millimetres.

    This combines unit conversion and vector construction for scripts that
    define board geometry using human-readable millimetre settings.
    """
    return vector(mm_to_iu(x_mm), mm_to_iu(y_mm))


def same_point(first, second):
    """Return whether two KiCad points have identical integer coordinates.

    Equality on SWIG proxy objects has varied between KiCad releases, so
    comparing X and Y explicitly is more portable than relying on ``==``.
    """
    return first.x == second.x and first.y == second.y


def is_horizontal(first, second):
    """Return whether a segment between two points has no Y-axis change."""
    return first.y == second.y


def is_vertical(first, second):
    """Return whether a segment between two points has no X-axis change."""
    return first.x == second.x


def distance(first, second):
    """Return the Euclidean distance between two KiCad points in internal units.

    The result is a float because diagonal distances are generally irrational;
    callers can compare it directly with an internal-unit tolerance.
    """
    return math.hypot(first.x - second.x, first.y - second.y)


def bounding_box_center(bbox):
    """Return the integer centre of a KiCad bounding box.

    The centre is calculated from the box origin and dimensions instead of
    calling ``GetCenter()``, which is absent or inconsistently wrapped in some
    KiCad Python API versions. Floor division keeps the result on KiCad's
    integer coordinate grid when a box has an odd width or height.
    """
    return vector(
        bbox.GetX() + bbox.GetWidth() // 2,
        bbox.GetY() + bbox.GetHeight() // 2,
    )


def text_angle_degrees(text_item):
    """Read a PCB text angle as degrees across KiCad API versions.

    Current KiCad versions return an angle object with ``AsDegrees()``. Older
    SWIG bindings returned an integer measured in tenths of a degree. Testing
    for the modern method first supports both representations without using a
    version-number check.
    """
    angle = text_item.GetTextAngle()
    if hasattr(angle, "AsDegrees"):
        return angle.AsDegrees()
    return float(angle) / 10.0


def is_board_text(item, required_methods=()):
    """Return whether a drawing item behaves like free-standing PCB text.

    SWIG proxy class identities have changed between KiCad releases. Duck
    typing against the operations used by the scripts is therefore more robust
    than ``isinstance``. Callers provide the methods needed for their operation
    because a read/move script and a resize script use different portions of
    the API. ``GetText`` is always required.
    """
    return all(
        hasattr(item, method_name)
        for method_name in ("GetText", *required_methods)
    )


def board_edge_bounds(board):
    """Return left, right, top, and bottom Edge.Cuts bounds in internal units.

    KiCad's screen-style coordinate system increases X to the right and Y
    downwards, so ``top`` is the smaller Y coordinate. The returned bounds come
    directly from ``GetBoardEdgesBoundingBox`` and include half the visible
    Edge.Cuts stroke on every side. Callers needing fabrication-centreline
    dimensions should compensate for that line width explicitly.
    """
    bbox = board.GetBoardEdgesBoundingBox()
    return bbox.GetLeft(), bbox.GetRight(), bbox.GetTop(), bbox.GetBottom()


def get_current_board():
    """Return the board open in PCB Editor, including a KiCad 10 workaround.

    Most KiCad builds return a normal ``BOARD`` proxy from ``GetBoard()``. Some
    KiCad 10 SWIG builds instead expose the underlying ``SwigPyObject``. In that
    case this function attaches the pointer to a non-owning Python ``BOARD``
    wrapper. The wrapper must not own the object because PCB Editor controls its
    lifetime; taking ownership could free the live board when Python collects
    the temporary proxy.
    """
    current_board = pcbnew.GetBoard()

    if current_board is None or hasattr(current_board, "GetDrawings"):
        return current_board
    if type(current_board).__name__ != "SwigPyObject":
        return current_board

    wrapped_board = pcbnew.BOARD.__new__(pcbnew.BOARD)
    wrapped_board.this = current_board
    try:
        wrapped_board.this.own(False)
    except AttributeError:
        # Older SWIG pointer wrappers are already non-owning and do not expose
        # the ownership mutator.
        pass
    return wrapped_board
