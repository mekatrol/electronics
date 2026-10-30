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
from kipy.board_types import ArcTrack, Track, Via, Zone

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


def footprint_pads(footprint):
    """Return pads from either a board instance or a footprint definition."""
    definition = getattr(footprint, "definition", footprint)
    return definition.pads


def _track_endpoint_keys(track):
    """Return graph keys for the two electrically connected track ends."""
    return tuple(
        (track.net.name, track.layer, point.x, point.y)
        for point in (track.start, track.end)
    )


def connected_track_sets(tracks):
    """Partition tracks into endpoint-connected sets on the same net/layer."""
    endpoint_tracks = {}
    for index, track in enumerate(tracks):
        for key in _track_endpoint_keys(track):
            endpoint_tracks.setdefault(key, []).append(index)

    unseen = set(range(len(tracks)))
    result = []
    while unseen:
        pending = [unseen.pop()]
        indexes = []
        while pending:
            index = pending.pop()
            indexes.append(index)
            for key in _track_endpoint_keys(tracks[index]):
                for neighbour in endpoint_tracks[key]:
                    if neighbour in unseen:
                        unseen.remove(neighbour)
                        pending.append(neighbour)
        result.append([tracks[index] for index in indexes])
    return result


def connected_route_sets(tracks, vias):
    """Partition tracks and vias into electrically connected route sets."""
    endpoint_tracks = {}
    for index, track in enumerate(tracks):
        for key in _track_endpoint_keys(track):
            endpoint_tracks.setdefault(key, []).append(index)

    via_tracks = []
    track_vias = {index: [] for index in range(len(tracks))}
    for via_index, via in enumerate(vias):
        indexes = set()
        for (net_name, _layer, x, y), connected in endpoint_tracks.items():
            if net_name == via.net.name and (x, y) == (via.position.x, via.position.y):
                indexes.update(connected)
        via_tracks.append(indexes)
        for track_index in indexes:
            track_vias[track_index].append(via_index)

    unseen_tracks = set(range(len(tracks)))
    unseen_vias = set(range(len(vias)))
    result = []
    while unseen_tracks or unseen_vias:
        pending_tracks = [unseen_tracks.pop()] if unseen_tracks else []
        pending_vias = [unseen_vias.pop()] if not pending_tracks else []
        route_tracks = []
        route_vias = []
        while pending_tracks or pending_vias:
            while pending_tracks:
                index = pending_tracks.pop()
                route_tracks.append(tracks[index])
                for key in _track_endpoint_keys(tracks[index]):
                    for neighbour in endpoint_tracks[key]:
                        if neighbour in unseen_tracks:
                            unseen_tracks.remove(neighbour)
                            pending_tracks.append(neighbour)
                for neighbour in track_vias[index]:
                    if neighbour in unseen_vias:
                        unseen_vias.remove(neighbour)
                        pending_vias.append(neighbour)
            while pending_vias:
                index = pending_vias.pop()
                route_vias.append(vias[index])
                for neighbour in via_tracks[index]:
                    if neighbour in unseen_tracks:
                        unseen_tracks.remove(neighbour)
                        pending_tracks.append(neighbour)
        result.append((route_tracks, route_vias))
    return result


def track_set_pad_connections(board, track_set, footprints, vias=()):
    """Return ``(reference, pad)`` pairs touched by a track set's ends."""
    endpoints = {
        (point.x, point.y): point
        for track in track_set
        for point in (track.start, track.end)
    }
    endpoints.update(
        {(via.position.x, via.position.y): via.position for via in vias}
    )
    net_names = {track.net.name for track in track_set}
    net_names.update(via.net.name for via in vias)
    connections = []
    for reference, footprint in footprints.items():
        for pad in footprint_pads(footprint):
            if pad.net.name not in net_names:
                continue
            if any(board.hit_test(pad, point) for point in endpoints.values()):
                connections.append((reference, pad))
    return connections


def internal_track_sets(track_sets_and_connections, references):
    """Select routes joining two or more footprints, all inside one group."""
    reference_set = set(references)
    result = []
    for track_set, connections in track_sets_and_connections:
        connected_references = {reference for reference, _pad in connections}
        if len(connected_references) >= 2 and connected_references <= reference_set:
            result.append((track_set, connections))
    return result


def copy_track(track, delta_x, delta_y, net):
    """Clone a straight or arc track, preserving all properties but its UUID."""
    copied = type(track)(proto=track.proto)
    copied.proto.ClearField("id")
    copied.proto.ClearField("parent")
    copied.net = net
    copied.start = vector(track.start.x + delta_x, track.start.y + delta_y)
    copied.end = vector(track.end.x + delta_x, track.end.y + delta_y)
    if isinstance(copied, ArcTrack):
        copied.mid = vector(track.mid.x + delta_x, track.mid.y + delta_y)
    return copied


def copy_via(via, delta_x, delta_y, net):
    """Clone a via, preserving its pad stack and all other properties."""
    copied = Via(proto=via.proto)
    copied.proto.ClearField("id")
    copied.proto.ClearField("parent")
    copied.net = net
    copied.position = vector(via.position.x + delta_x, via.position.y + delta_y)
    return copied


def group_local_vias(group_box_value, footprints, references, vias):
    """Return same-net vias spatially contained by a footprint group.

    A via connected only through a copper zone has no track endpoint to place
    it in the route graph. Constraining the fallback by both group bounds and
    pad net keeps such local stitching vias associated with the nearby group
    instead of selecting every via on a board-wide net.
    """
    left, right, top, bottom = box_edges(group_box_value)
    net_names = {
        pad.net.name
        for reference in references
        for pad in footprint_pads(footprints[reference])
        if pad.net.name
    }
    return [
        via
        for via in vias
        if via.net.name in net_names
        and left <= via.position.x <= right
        and top <= via.position.y <= bottom
    ]


def group_local_via_zones(board, group_box_value, vias, zones):
    """Return localized zones that contain one of a group's selected vias."""
    group_left, group_right, group_top, group_bottom = box_edges(group_box_value)
    result = []
    for zone in zones:
        box = board.get_item_bounding_box(zone)
        if box is None:
            continue
        left, right, top, bottom = box_edges(box)
        if not (
            group_left <= left <= right <= group_right
            and group_top <= top <= bottom <= group_bottom
        ):
            continue
        if any(
            via.net.name == zone.net.name
            and left <= via.position.x <= right
            and top <= via.position.y <= bottom
            for via in vias
        ):
            result.append(zone)
    return result


def copy_zone(zone, delta_x, delta_y, net):
    """Clone and translate a localized copper zone."""
    copied = Zone(proto=zone.proto)
    copied.proto.ClearField("id")
    copied.proto.ClearField("parent")
    copied.net = net
    copied.move(vector(delta_x, delta_y))
    return copied


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

    # Use endpoint connectivity instead of whole nets so a local branch of a
    # shared net (for example GND) cannot pull unrelated board tracks into the
    # copy. Snapshot route membership before any footprints are moved.
    tracks = [
        track
        for track in board.get_tracks()
        if isinstance(track, (Track, ArcTrack))
    ]
    vias = list(board.get_vias())
    zones = list(board.get_zones())
    track_sets_and_connections = [
        (
            track_set,
            track_set_pad_connections(board, track_set, footprints, via_set),
            via_set,
        )
        for track_set, via_set in connected_route_sets(tracks, vias)
    ]
    template_track_sets = internal_track_sets(
        [
            (tracks, connections)
            for tracks, connections, _vias in track_sets_and_connections
        ],
        template,
    )
    template_track_ids = {id(tracks) for tracks, _connections in template_track_sets}
    template_reference_set = set(template)
    template_routes = [
        (
            route_tracks if id(route_tracks) in template_track_ids else [],
            connections,
            route_vias,
        )
        for route_tracks, connections, route_vias in track_sets_and_connections
        if id(route_tracks) in template_track_ids
        or (
            route_vias
            and 0 < len({reference for reference, _pad in connections})
            and {
                reference for reference, _pad in connections
            } <= template_reference_set
        )
    ]
    routed_template_via_ids = {
        id(via)
        for _route_tracks, _connections, route_vias in template_routes
        for via in route_vias
    }
    for via in group_local_vias(template_box, footprints, template, vias):
        if id(via) in routed_template_via_ids:
            continue
        matching_pads = [
            (reference, pad)
            for reference in template
            for pad in footprint_pads(footprints[reference])
            if pad.net.name == via.net.name
        ]
        template_routes.append(([], [matching_pads[0]], [via]))

    template_local_vias = group_local_vias(
        template_box, footprints, template, vias
    )
    template_zones = group_local_via_zones(
        board, template_box, template_local_vias, zones
    )

    destination_tracks = []
    destination_vias = []
    destination_zones = []
    for group in GROUPS[1:]:
        group_reference_set = set(group)
        destination_box = group_box(board, footprints, group)
        internal = internal_track_sets(
            [
                (tracks, connections)
                for tracks, connections, _vias in track_sets_and_connections
            ],
            group,
        )
        internal_track_ids = {
            id(route_tracks) for route_tracks, _connections in internal
        }
        for route_tracks, connections, route_vias in track_sets_and_connections:
            connected_references = {
                reference for reference, _pad in connections
            }
            if id(route_tracks) in internal_track_ids:
                destination_tracks.extend(route_tracks)
            if (
                route_vias
                and connected_references
                and connected_references <= group_reference_set
            ):
                destination_vias.extend(route_vias)
        destination_vias.extend(
            group_local_vias(destination_box, footprints, group, vias)
        )
        group_vias = group_local_vias(
            destination_box, footprints, group, vias
        )
        destination_zones.extend(
            group_local_via_zones(board, destination_box, group_vias, zones)
        )

    # A routed via can also satisfy the local-zone fallback. Send every board
    # item to KiCad only once when deleting the destination routes.
    destination_vias = list({id(via): via for via in destination_vias}.values())

    template_index = {reference: index for index, reference in enumerate(template)}
    route_templates = []
    for track_set, connections, route_vias in template_routes:
        source_net_name = (
            track_set[0].net.name if track_set else route_vias[0].net.name
        )
        source_pads = [
            (template_index[reference], pad.number)
            for reference, pad in connections
            if pad.net.name == source_net_name
        ]
        if not source_pads:
            raise RuntimeError(
                f"could not map routed net {source_net_name!r} to a template pad"
            )
        route_templates.append((track_set, route_vias, source_pads))

    zone_templates = []
    for zone in template_zones:
        matching_pads = [
            (template_index[reference], pad.number)
            for reference in template
            for pad in footprint_pads(footprints[reference])
            if pad.net.name == zone.net.name
        ]
        if not matching_pads:
            raise RuntimeError(
                f"could not map local zone net {zone.net.name!r} to a template pad"
            )
        zone_templates.append((zone, matching_pads[0]))

    changed = []
    created_tracks = []
    created_vias = []
    created_zones = []
    action = "Align repeated component groups"
    with editor_commit(board, action, refill_zones=True):
        board.remove_items(destination_tracks)
        board.remove_items(destination_vias)
        board.remove_items(destination_zones)
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

            for track_set, route_vias, source_pads in route_templates:
                destination_pads = []
                for item_index, pad_number in source_pads:
                    matching_pads = [
                        pad
                        for pad in footprint_pads(footprints[group[item_index]])
                        if pad.number == pad_number
                    ]
                    if len(matching_pads) != 1:
                        raise RuntimeError(
                            f"{group[item_index]} must have exactly one pad {pad_number}"
                        )
                    destination_pads.append(matching_pads[0])
                destination_net_names = {pad.net.name for pad in destination_pads}
                if len(destination_net_names) != 1:
                    raise RuntimeError(
                        f"OP{group_index + 1} corresponding pads do not share one net: "
                        f"{', '.join(sorted(destination_net_names))}"
                    )
                created_tracks.extend(
                    copy_track(track, delta_x, delta_y, destination_pads[0].net)
                    for track in track_set
                )
                created_vias.extend(
                    copy_via(via, delta_x, delta_y, destination_pads[0].net)
                    for via in route_vias
                )

            for zone, (item_index, pad_number) in zone_templates:
                matching_pads = [
                    pad
                    for pad in footprint_pads(footprints[group[item_index]])
                    if pad.number == pad_number
                ]
                if len(matching_pads) != 1:
                    raise RuntimeError(
                        f"{group[item_index]} must have exactly one pad {pad_number}"
                    )
                created_zones.append(
                    copy_zone(
                        zone,
                        delta_x,
                        delta_y,
                        matching_pads[0].net,
                    )
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

            # Keep existing OP1 routes and new destination copies aligned with
            # the footprints during the optional whole-row translation.
            for track_set, route_vias, _source_pads in route_templates:
                for track in track_set:
                    track.start = vector(track.start.x + center_delta_x, track.start.y)
                    track.end = vector(track.end.x + center_delta_x, track.end.y)
                    if isinstance(track, ArcTrack):
                        track.mid = vector(track.mid.x + center_delta_x, track.mid.y)
                    changed.append(track)
                for via in route_vias:
                    via.position = vector(
                        via.position.x + center_delta_x,
                        via.position.y,
                    )
                    changed.append(via)
            for track in created_tracks:
                track.start = vector(track.start.x + center_delta_x, track.start.y)
                track.end = vector(track.end.x + center_delta_x, track.end.y)
                if isinstance(track, ArcTrack):
                    track.mid = vector(track.mid.x + center_delta_x, track.mid.y)
            for via in created_vias:
                via.position = vector(via.position.x + center_delta_x, via.position.y)
            for zone in template_zones:
                zone.move(vector(center_delta_x, 0))
                changed.append(zone)
            for zone in created_zones:
                zone.move(vector(center_delta_x, 0))

            if DEBUG:
                print(
                    "All groups: horizontally centered on Edge.Cuts; "
                    f"moved X by {to_mm(center_delta_x):.3f} mm"
                )

        board.update_items(changed)
        board.create_items(created_tracks + created_vias + created_zones)

    print(
        f"Aligned {len(GROUPS)} groups, copied {len(created_tracks)} track(s) and "
        f"{len(created_vias)} via(s) and {len(created_zones)} local zone(s), and "
        f"replaced {len(destination_tracks)} destination track(s), "
        f"{len(destination_vias)} via(s), and {len(destination_zones)} local zone(s) "
        f"(undo: {action})."
    )


if __name__ == "__main__":
    main()
