import math
import os

import pcbnew


# =========================
# User constants
# =========================
BOARD_WIDTH_MM = 50.0
BOARD_HEIGHT_MM = 70.0

ORIGIN_X_MM = 120.0
ORIGIN_Y_MM = 50.0

# Set to 0.0 for square corners.
CORNER_RADIUS_MM = 3.0

EDGE_LINE_WIDTH_MM = 0.10

DELETE_EXISTING_EDGE_CUTS = True
PLUGIN_NAME = "Create Rectangular Edge Cuts"


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def pt(x_mm: float, y_mm: float):
    return pcbnew.VECTOR2I(mm(x_mm), mm(y_mm))


def add_edge_segment(board, start, end, line_width):
    segment = pcbnew.PCB_SHAPE(board)
    segment.SetLayer(pcbnew.Edge_Cuts)
    segment.SetShape(pcbnew.SHAPE_T_SEGMENT)
    segment.SetStart(start)
    segment.SetEnd(end)
    segment.SetWidth(line_width)
    board.Add(segment)


def add_edge_arc(board, start, mid, end, line_width):
    arc = pcbnew.PCB_SHAPE(board)
    arc.SetLayer(pcbnew.Edge_Cuts)
    arc.SetShape(pcbnew.SHAPE_T_ARC)

    # KiCad defines the arc using three points lying on the arc.
    arc.SetArcGeometry(start, mid, end)

    arc.SetWidth(line_width)
    board.Add(arc)


def remove_existing_edge_cuts(board):
    items_to_remove = []

    for item in board.GetDrawings():
        try:
            if item.GetLayer() == pcbnew.Edge_Cuts:
                items_to_remove.append(item)
        except Exception:
            pass

    for item in items_to_remove:
        board.Remove(item)


def validate_dimensions(width, height, radius):
    if width <= 0:
        raise ValueError("BOARD_WIDTH_MM must be greater than zero.")

    if height <= 0:
        raise ValueError("BOARD_HEIGHT_MM must be greater than zero.")

    if radius < 0:
        raise ValueError("CORNER_RADIUS_MM cannot be negative.")

    maximum_radius = min(width, height) / 2.0

    if radius > maximum_radius:
        raise ValueError(
            f"CORNER_RADIUS_MM is too large. "
            f"The maximum radius for a {width} mm × {height} mm board "
            f"is {maximum_radius} mm."
        )


def create_square_rectangle(
    board,
    x0,
    y0,
    x1,
    y1,
    line_width,
):
    top_left = pt(x0, y0)
    top_right = pt(x1, y0)
    bottom_right = pt(x1, y1)
    bottom_left = pt(x0, y1)

    add_edge_segment(board, top_left, top_right, line_width)
    add_edge_segment(board, top_right, bottom_right, line_width)
    add_edge_segment(board, bottom_right, bottom_left, line_width)
    add_edge_segment(board, bottom_left, top_left, line_width)


def create_rounded_rectangle(
    board,
    x0,
    y0,
    x1,
    y1,
    radius,
    line_width,
):
    # Offset from an arc centre to its 45-degree midpoint.
    diagonal = radius / math.sqrt(2.0)

    # Straight portions
    top_start = pt(x0 + radius, y0)
    top_end = pt(x1 - radius, y0)

    right_start = pt(x1, y0 + radius)
    right_end = pt(x1, y1 - radius)

    bottom_start = pt(x1 - radius, y1)
    bottom_end = pt(x0 + radius, y1)

    left_start = pt(x0, y1 - radius)
    left_end = pt(x0, y0 + radius)

    add_edge_segment(board, top_start, top_end, line_width)
    add_edge_segment(board, right_start, right_end, line_width)
    add_edge_segment(board, bottom_start, bottom_end, line_width)
    add_edge_segment(board, left_start, left_end, line_width)

    # Top-right corner
    add_edge_arc(
        board,
        start=top_end,
        mid=pt(
            x1 - radius + diagonal,
            y0 + radius - diagonal,
        ),
        end=right_start,
        line_width=line_width,
    )

    # Bottom-right corner
    add_edge_arc(
        board,
        start=right_end,
        mid=pt(
            x1 - radius + diagonal,
            y1 - radius + diagonal,
        ),
        end=bottom_start,
        line_width=line_width,
    )

    # Bottom-left corner
    add_edge_arc(
        board,
        start=bottom_end,
        mid=pt(
            x0 + radius - diagonal,
            y1 - radius + diagonal,
        ),
        end=left_start,
        line_width=line_width,
    )

    # Top-left corner
    add_edge_arc(
        board,
        start=left_end,
        mid=pt(
            x0 + radius - diagonal,
            y0 + radius - diagonal,
        ),
        end=top_start,
        line_width=line_width,
    )


class CreateRectangularEdgeCutsPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = PLUGIN_NAME
        self.category = "Board Outline"
        self.description = (
            "Create a rectangular Edge.Cuts outline with configurable corner radius"
        )
        self.show_toolbar_button = False

        icon_path = os.path.join(
            os.path.dirname(__file__),
            "create_rect_edge_cuts.png",
        )

        if os.path.exists(icon_path):
            self.icon_file_name = icon_path

    def Run(self):
        board = pcbnew.GetBoard()

        if board is None:
            raise RuntimeError("No board is open.")

        validate_dimensions(
            BOARD_WIDTH_MM,
            BOARD_HEIGHT_MM,
            CORNER_RADIUS_MM,
        )

        if DELETE_EXISTING_EDGE_CUTS:
            remove_existing_edge_cuts(board)

        x0 = ORIGIN_X_MM
        y0 = ORIGIN_Y_MM
        x1 = x0 + BOARD_WIDTH_MM
        y1 = y0 + BOARD_HEIGHT_MM

        line_width = mm(EDGE_LINE_WIDTH_MM)

        if CORNER_RADIUS_MM == 0:
            create_square_rectangle(
                board,
                x0,
                y0,
                x1,
                y1,
                line_width,
            )
        else:
            create_rounded_rectangle(
                board,
                x0,
                y0,
                x1,
                y1,
                CORNER_RADIUS_MM,
                line_width,
            )

        pcbnew.Refresh()


CreateRectangularEdgeCutsPlugin().register()
