"""Shared mechanical dimensions for the motherboard/daughter-board interface.

This module deliberately contains geometry only.  Footprint references belong
to an individual schematic and are therefore declared by the script operating
on that board.  Keeping the dimensions here prevents the daughter-board
checker and motherboard layout script from quietly acquiring different copies
of the interface specification.

All values are millimetres measured to the Edge.Cuts centreline.  The daughter
board's origin is its finished top-left corner; X increases right and Y
increases down, matching KiCad's board coordinate system.
"""

# Finished daughter-board envelope.  Motherboard slots use this same width as
# their pitch, producing a contiguous row with no gap between board outlines.
DAUGHTER_BOARD_WIDTH_MM = 25.0
DAUGHTER_BOARD_HEIGHT_MM = 42.0
DAUGHTER_BOARD_CORNER_RADIUS_MM = 1.0
EDGE_CUTS_LINE_WIDTH_MM = 0.10

# Connector datums are the centre of the pin nearest the daughter board's
# top-left corner.  The connector itself is horizontally centred: the
# asymmetric X value is the first-pin location of a four-pin, 2.54 mm row.
PRIMARY_CONNECTOR_LEFT_MM = 8.69
PRIMARY_CONNECTOR_TOP_MM = 3.15
OPTIONAL_CONNECTOR_LEFT_MM = 9.96
OPTIONAL_CONNECTOR_TOP_MM = 36.0

# Mounting-hole datums are their drill centres.  Both holes share a Y datum and
# are symmetric about the daughter board's horizontal centreline.
LEFT_HOLE_LEFT_MM = 3.0
RIGHT_HOLE_LEFT_MM = 22.0
MOUNTING_HOLE_TOP_MM = 38.15

# IPC dimensions are integral nanometres.  This permits harmless serializer
# rounding while still detecting a one-micron change to the interface.
INTERFACE_TOLERANCE_MM = 0.001
