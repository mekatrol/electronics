#!/usr/bin/env python3
"""Arrange repeated footprint groups from one reference layout using IPC.

Run from the repository root with::

    .venv-kicad-ipc/bin/python hardware/kicad/modules/align_groups.py

The first group is the layout template. Every other group is rebuilt from that
template, including its component-label positions, then placed to its right in
one top-aligned row. An optional final step centres the complete row, including
the template group, within the board. All moves and rotations are one entry in
PCB Editor's Undo/Redo history.
"""

from kicad_ipc import (
    board_edge_bounds,
    box_edges,
    connect_board,
    editor_commit,
    footprints_by_reference,
    from_mm,
    merge_boxes,
    to_mm,
    vector,
)

# Each tuple has the same logical component order. For example, item zero is
# the input resistor in every channel, item one is the indicator LED, and so
# on. Keeping this mapping explicit is intentional: reference numbers alone do
# not describe a circuit's role, and guessing from numeric offsets could
# silently move the wrong footprint after a future schematic re-annotation.
#
# GROUPS[0] (OP1) is the master layout. Its footprint positions and rotations
# are read from the open board when the script starts; no coordinates need to
# be copied into this file when the preferred OP1 arrangement changes.
GROUPS = [
    ("R9", "D5", "R13", "U7", "R17", "R18", "Q1", "R25", "C20", "D9"),
    ("R10", "D6", "R14", "U8", "R19", "R20", "Q2", "R26", "C21", "D10"),
    ("R11", "D7", "R15", "U9", "R21", "R22", "Q3", "R27", "C22", "D11"),
    ("R12", "D8", "R16", "U10", "R23", "R24", "Q4", "R28", "C23", "D12"),
    ("R29", "D13", "R33", "U11", "R37", "R38", "Q5", "R45", "C24", "D17"),
    ("R30", "D14", "R34", "U12", "R39", "R40", "Q6", "R46", "C25", "D18"),
    ("R31", "D15", "R35", "U13", "R41", "R42", "Q7", "R47", "C26", "D19"),
    ("R32", "D16", "R36", "U14", "R43", "R44", "Q8", "R48", "C27", "D20"),
]

# Empty space between the physical bounding boxes of adjacent groups. The
# template group's width, rather than a manually entered pitch, is used so a
# later OP1 layout change cannot make neighbouring groups overlap unnoticed.
GROUP_SPACING_MM = 2.54

# After building the top-aligned row, move the entire set as one object until
# its physical centre matches the horizontal centre of Edge.Cuts. This final
# translation includes OP1: moving every group by exactly the same amount keeps
# all copied component and label relationships intact. Disable this when OP1's
# existing X position must remain the absolute anchor for the finished row.
CENTER_GROUPS_HORIZONTALLY = True
DEBUG = True


def group_box(board, footprints, references):
    """Return the combined physical bounding box of a footprint group.

    Reference and value text are excluded because manually moved text should
    not change the component pitch. Pads, fabrication graphics, courtyard
    graphics, and the footprint bodies remain part of KiCad's footprint box,
    so the resulting spacing is based on the actual component geometry.
    """
    boxes = []
    for reference in references:
        box = board.get_item_bounding_box(footprints[reference], include_text=False)
        if box is None:
            raise RuntimeError(f"KiCad returned no bounding box for {reference}")
        boxes.append(box)
    return merge_boxes(boxes)


def label_layout(footprint):
    """Snapshot the positions and angles of a footprint's component labels.

    KiCad stores the Reference and Value fields as text owned by the footprint,
    but each field has its own independently editable board position. Moving a
    footprint carries its existing fields along; it does not automatically use
    another footprint's field offsets. Capturing both standard fields here lets
    the destination keep its own reference/value strings while adopting OP1's
    deliberate label placement.
    """
    return tuple(
        (
            vector(field.text.position.x, field.text.position.y),
            field.text.attributes.angle,
        )
        for field in (footprint.reference_field, footprint.value_field)
    )


def apply_label_layout(footprint, layout, delta_x, delta_y):
    """Place Reference and Value fields like OP1, translated to this group.

    Reassigning the edited text wrapper to its field follows kipy's supported
    mutation pattern and ensures the updated nested protobuf is included when
    the containing footprint is sent back to PCB Editor.
    """
    fields = (footprint.reference_field, footprint.value_field)
    for field, (source_position, source_angle) in zip(fields, layout):
        text = field.text
        text.position = vector(
            source_position.x + delta_x,
            source_position.y + delta_y,
        )
        text.attributes.angle = source_angle
        field.text = text


def main():
    """Copy OP1's layout into OP2--OP8 and publish one undoable change."""
    if len(GROUPS) < 2:
        raise ValueError("GROUPS must contain a template and at least one copy")

    component_count = len(GROUPS[0])
    if component_count == 0:
        raise ValueError("the template group must contain at least one footprint")
    if any(len(group) != component_count for group in GROUPS):
        raise ValueError("every group must have the same number of footprints")

    # Duplicate references would make one footprint receive two contradictory
    # target positions. Reject that configuration before opening a commit so a
    # typo cannot leave the editor with a partially staged arrangement.
    references = [reference for group in GROUPS for reference in group]
    duplicates = sorted(
        reference for reference in set(references) if references.count(reference) > 1
    )
    if duplicates:
        raise ValueError(f"duplicate group footprint(s): {', '.join(duplicates)}")

    _client, board = connect_board()
    footprints = footprints_by_reference(board)
    missing = [reference for reference in references if reference not in footprints]
    if missing:
        raise RuntimeError(f"missing group footprint(s): {', '.join(missing)}")

    template = GROUPS[0]
    template_box = group_box(board, footprints, template)
    left, right, top, _bottom = box_edges(template_box)
    pitch = right - left + from_mm(GROUP_SPACING_MM)

    # Snapshot positions and orientations before editing anything. This makes
    # OP1 immutable while it acts as the source and prevents a destination
    # update from becoming the source for a later group in the transaction.
    template_positions = [
        vector(footprints[reference].position.x, footprints[reference].position.y)
        for reference in template
    ]
    template_orientations = [
        footprints[reference].orientation for reference in template
    ]
    template_labels = [
        label_layout(footprints[reference]) for reference in template
    ]

    changed = []
    action = "Align repeated component groups"
    with editor_commit(board, action):
        for group_index, group in enumerate(GROUPS[1:], start=1):
            # Moving every member by the same whole-group offset preserves all
            # of OP1's relative X/Y distances. KiCad's Y axis increases down
            # the screen; an unchanged Y coordinate therefore also aligns the
            # copied group to OP1's top edge.
            delta_x = group_index * pitch
            delta_y = 0
            if DEBUG:
                print(
                    f"OP{group_index + 1}: template offset "
                    f"({to_mm(delta_x):.3f}, {to_mm(delta_y):.3f}) mm; "
                    f"top = {to_mm(top):.3f} mm"
                )

            for item_index, reference in enumerate(group):
                footprint = footprints[reference]
                old = vector(footprint.position.x, footprint.position.y)

                # Apply rotation before translation. The kipy rotation setter
                # rotates pads and footprint graphics around the footprint's
                # current anchor; assigning the final position afterwards then
                # translates that complete geometry as one coherent object.
                footprint.orientation = template_orientations[item_index]
                source = template_positions[item_index]
                footprint.position = vector(source.x + delta_x, source.y + delta_y)

                # Positioning a footprint only translates that footprint's old
                # labels. Override those inherited offsets with OP1's Reference
                # and Value field positions so silkscreen labels repeat with
                # the same layout as the component bodies.
                apply_label_layout(
                    footprint,
                    template_labels[item_index],
                    delta_x,
                    delta_y,
                )
                changed.append(footprint)

                if DEBUG:
                    target = footprint.position
                    print(
                        f"  {reference}: "
                        f"({to_mm(old.x):.3f}, {to_mm(old.y):.3f}) -> "
                        f"({to_mm(target.x):.3f}, {to_mm(target.y):.3f}) mm; "
                        f"rotation {footprint.orientation.degrees:.1f} degrees"
                    )

        if CENTER_GROUPS_HORIZONTALLY:
            # All groups have the same physical geometry as OP1 after their
            # rotations are copied. Their complete row therefore begins at
            # OP1's left edge and ends one template width after the final group
            # origin. Calculate the row centre from those known final bounds;
            # this avoids depending on whether KiCad exposes staged commit
            # geometry through a fresh bounding-box request.
            row_left = left
            row_right = right + (len(GROUPS) - 1) * pitch
            board_left, board_right, _board_top, _board_bottom = (
                board_edge_bounds(board)
            )
            row_center_x = (row_left + row_right) // 2
            board_center_x = (board_left + board_right) // 2
            center_delta_x = board_center_x - row_center_x

            # Destination footprints are already in ``changed``. Add only OP1
            # here so every modified wrapper is sent to KiCad exactly once when
            # the transaction is published.
            for reference in template:
                changed.append(footprints[reference])
            for group in GROUPS:
                for reference in group:
                    footprint = footprints[reference]
                    footprint.position = vector(
                        footprint.position.x + center_delta_x,
                        footprint.position.y,
                    )

            if DEBUG:
                print(
                    "All groups: horizontally centered on Edge.Cuts; "
                    f"moved X by {to_mm(center_delta_x):.3f} mm"
                )

        board.update_items(changed)

    print(
        f"Aligned {len(GROUPS)} groups and {len(changed)} copied footprint(s) "
        f"(undo: {action})."
    )


if __name__ == "__main__":
    main()
