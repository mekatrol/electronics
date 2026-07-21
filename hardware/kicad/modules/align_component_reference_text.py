# Run with:
# exec(open("/home/dad/repos/electronics/hardware/kicad/modules/align_component_reference_text.py").read())

import math

import pcbnew


# ============================================================
# User settings
# ============================================================
# References in this list retain their special/manual positions. Add or remove
# entries as required; matching is exact and case-sensitive.
IGNORE_REFERENCES = []

# Visible edge-to-edge gap between the component courtyard and reference text.
REFERENCE_OFFSET_MM = 0.1

# Minimum gap between a moved reference and every other component courtyard
# on the same side of the PCB. If the intended position would violate this,
# the collision is reported and that reference is left unchanged.
OTHER_COURTYARD_CLEARANCE_MM = 0.1

# A reference exactly at the courtyard centre has no existing side to retain.
# Choose which side should be used in that uncommon case.
CENTRED_REFERENCE_SIDE = "top"  # "left", "right", "top", or "bottom"

# KiCad console edits do not always mark the PCB editor document as modified.
# Saving explicitly ensures the changed reference positions reach the PCB file.
SAVE_BOARD_AFTER_ALIGNMENT = True

DEBUG = True


# ============================================================
# Geometry helpers
# ============================================================
def mm_to_iu(value_mm):
    """Convert millimetres to KiCad internal units."""
    return pcbnew.FromMM(value_mm)


def iu_to_mm(value_iu):
    """Convert KiCad internal units to millimetres."""
    return pcbnew.ToMM(value_iu)


def bbox_centre(bbox):
    """Return the centre of a KiCad bounding box."""
    return pcbnew.VECTOR2I(
        bbox.GetX() + bbox.GetWidth() // 2,
        bbox.GetY() + bbox.GetHeight() // 2,
    )


def text_angle_degrees(reference_text):
    """Read a reference angle in degrees across KiCad API versions."""
    angle = reference_text.GetTextAngle()

    if hasattr(angle, "AsDegrees"):
        return angle.AsDegrees()

    return float(angle) / 10.0


def nominal_text_half_extents(reference_text):
    """
    Return nominal board-axis half extents without KiCad's selection margin.

    GetBoundingBox() includes a sizeable font/interline selection margin. The
    unrotated text-box width supplies the string length, while GetTextSize().y
    supplies the configured character height. Projecting those dimensions by
    the existing angle supports both horizontal and vertical references.
    """
    try:
        local_width = reference_text.GetTextBox().GetWidth()
        local_height = reference_text.GetTextSize().y
        angle_radians = math.radians(text_angle_degrees(reference_text))
        cosine = abs(math.cos(angle_radians))
        sine = abs(math.sin(angle_radians))
        half_width = (cosine * local_width + sine * local_height) / 2.0
        half_height = (sine * local_width + cosine * local_height) / 2.0
        return int(round(half_width)), int(round(half_height))
    except Exception:
        # Compatibility fallback for a KiCad build without GetTextBox().
        bbox = reference_text.GetBoundingBox()
        return bbox.GetWidth() // 2, bbox.GetHeight() // 2


def rendered_text_bounds(reference_text):
    """Return the bounds of the actual rendered strokes, without font margins."""
    shape = None

    # KiCad SWIG signatures vary by release, so try the supported forms in
    # order. GetEffectiveShape() includes the configured stroke thickness.
    try:
        shape = reference_text.GetEffectiveShape()
    except Exception:
        try:
            shape = reference_text.GetEffectiveShape(reference_text.GetLayer())
        except Exception:
            try:
                shape = reference_text.GetEffectiveTextShape()
            except Exception:
                shape = None

    if shape is not None:
        try:
            bbox = shape.BBox()
            return (
                bbox.GetLeft(),
                bbox.GetRight(),
                bbox.GetTop(),
                bbox.GetBottom(),
            )
        except Exception:
            pass

    # Compatibility fallback uses nominal dimensions centred on KiCad's text
    # box. It is less optically exact but avoids the inflated selection margin.
    centre = bbox_centre(reference_text.GetBoundingBox())
    half_width, half_height = nominal_text_half_extents(reference_text)
    return (
        centre.x - half_width,
        centre.x + half_width,
        centre.y - half_height,
        centre.y + half_height,
    )


def bounds_centre(bounds):
    left, right, top, bottom = bounds
    return pcbnew.VECTOR2I((left + right) // 2, (top + bottom) // 2)


def courtyard_bbox(footprint):
    """Return the footprint courtyard bounding box on its placed board side."""
    courtyard_layer = pcbnew.B_CrtYd if footprint.IsFlipped() else pcbnew.F_CrtYd

    # Rebuild the cache in case the footprint was edited in this session.
    if hasattr(footprint, "BuildCourtyardCaches"):
        footprint.BuildCourtyardCaches()

    courtyard = footprint.GetCourtyard(courtyard_layer)
    bbox = courtyard.BBox()

    if bbox.GetWidth() <= 0 or bbox.GetHeight() <= 0:
        raise RuntimeError("footprint has no valid courtyard")

    return bbox


def validate_settings():
    valid_sides = {"left", "right", "top", "bottom"}

    if CENTRED_REFERENCE_SIDE not in valid_sides:
        raise RuntimeError(
            "CENTRED_REFERENCE_SIDE must be left, right, top, or bottom"
        )

    if REFERENCE_OFFSET_MM < 0 or OTHER_COURTYARD_CLEARANCE_MM < 0:
        raise RuntimeError("offset and clearance values cannot be negative")


def current_reference_side(reference_text, courtyard):
    """
    Determine which courtyard side the reference currently occupies.

    Displacement is normalised by courtyard width and height. This avoids a
    wide rectangular footprint incorrectly favouring its long axis merely
    because the coordinate difference is numerically larger.
    """
    text_centre = bounds_centre(rendered_text_bounds(reference_text))
    courtyard_centre = bbox_centre(courtyard)
    delta_x = text_centre.x - courtyard_centre.x
    delta_y = text_centre.y - courtyard_centre.y

    if delta_x == 0 and delta_y == 0:
        return CENTRED_REFERENCE_SIDE

    half_width = max(courtyard.GetWidth() / 2.0, 1.0)
    half_height = max(courtyard.GetHeight() / 2.0, 1.0)
    normalised_x = delta_x / half_width
    normalised_y = delta_y / half_height

    if abs(normalised_x) > abs(normalised_y):
        return "left" if delta_x < 0 else "right"

    return "top" if delta_y < 0 else "bottom"


def target_reference_centre(reference_text, courtyard, side):
    """Return the aligned, courtyard-relative target centre for a side."""
    courtyard_centre = bbox_centre(courtyard)
    visible_gap = mm_to_iu(REFERENCE_OFFSET_MM)
    left, right, top, bottom = rendered_text_bounds(reference_text)
    half_width = (right - left) // 2
    half_height = (bottom - top) // 2

    if side in ("left", "right"):
        # The reference is centred vertically. Its rendered board-axis width
        # determines the visible edge-to-edge gap from the courtyard.
        boundary_offset = visible_gap + half_width
        target_y = courtyard_centre.y

        if side == "left":
            target_x = courtyard.GetLeft() - boundary_offset
        else:
            target_x = courtyard.GetRight() + boundary_offset
    else:
        # The reference is centred horizontally. Its rendered board-axis
        # height determines the visible gap from the courtyard boundary.
        boundary_offset = visible_gap + half_height
        target_x = courtyard_centre.x

        if side == "top":
            target_y = courtyard.GetTop() - boundary_offset
        else:
            target_y = courtyard.GetBottom() + boundary_offset

    return pcbnew.VECTOR2I(target_x, target_y)


def moved_text_bounds(reference_text, target_centre):
    """Return rendered board-axis bounds the text would have at a target centre."""
    left, right, top, bottom = rendered_text_bounds(reference_text)
    current_centre = bounds_centre((left, right, top, bottom))
    delta_x = target_centre.x - current_centre.x
    delta_y = target_centre.y - current_centre.y

    return (
        left + delta_x,
        right + delta_x,
        top + delta_y,
        bottom + delta_y,
    )


def bounds_intersect_courtyard(bounds, courtyard, clearance):
    """Check a proposed text rectangle against an expanded courtyard."""
    left, right, top, bottom = bounds

    return not (
        right <= courtyard.GetLeft() - clearance
        or left >= courtyard.GetRight() + clearance
        or bottom <= courtyard.GetTop() - clearance
        or top >= courtyard.GetBottom() + clearance
    )


def colliding_references(reference_text, target_centre, other_courtyards):
    """Return component references whose courtyards collide with the text."""
    bounds = moved_text_bounds(reference_text, target_centre)
    clearance = mm_to_iu(OTHER_COURTYARD_CLEARANCE_MM)
    collisions = []

    for other_reference, other_courtyard in other_courtyards:
        if bounds_intersect_courtyard(bounds, other_courtyard, clearance):
            collisions.append(other_reference)

    return collisions


def checked_placement(
    reference_text,
    courtyard,
    preferred_side,
    other_courtyards,
):
    """Return the preferred placement, or fail without selecting another side."""
    target_centre = target_reference_centre(
        reference_text,
        courtyard,
        preferred_side,
    )
    collisions = colliding_references(
        reference_text,
        target_centre,
        other_courtyards,
    )

    if collisions:
        raise RuntimeError(
            f"intended {preferred_side} position collides with "
            + ", ".join(sorted(collisions))
        )

    return target_centre


def move_text_centre(reference_text, target_centre):
    """
    Move a reference using its visible centre while preserving its angle.

    Moving by the bounding-box delta also works for non-centred justification.
    SetTextAngle() is intentionally not called, so orientation is unchanged.
    """
    old_position = reference_text.GetPosition()
    old_centre = bounds_centre(rendered_text_bounds(reference_text))
    delta_x = target_centre.x - old_centre.x
    delta_y = target_centre.y - old_centre.y
    reference_text.SetPosition(
        pcbnew.VECTOR2I(old_position.x + delta_x, old_position.y + delta_y)
    )


# ============================================================
# Main operation
# ============================================================
def align_reference_labels(board):
    """Align all visible component references except ignored references."""
    validate_settings()
    ignored = set(IGNORE_REFERENCES)
    moved_count = 0
    ignored_count = 0
    hidden_count = 0
    error_count = 0
    footprint_records = []

    # Collect every valid courtyard before moving anything. Ignored and hidden
    # references still contribute obstacles for other reference labels.
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()

        try:
            footprint_records.append(
                (
                    footprint,
                    reference,
                    courtyard_bbox(footprint),
                    footprint.IsFlipped(),
                )
            )
        except Exception as error:
            error_count += 1
            print(f"Warning: {reference}: {error}; skipping it.")

    for footprint, reference, courtyard, is_flipped in footprint_records:

        if reference in ignored:
            ignored_count += 1
            continue

        reference_text = footprint.Reference()

        # Hidden fabrication references do not need a visible board position.
        if hasattr(reference_text, "IsVisible") and not reference_text.IsVisible():
            hidden_count += 1
            continue

        try:
            preferred_side = current_reference_side(reference_text, courtyard)
            other_courtyards = [
                (other_reference, other_courtyard)
                for other_footprint, other_reference, other_courtyard, other_flipped
                in footprint_records
                if other_footprint is not footprint and other_flipped == is_flipped
            ]
            target_centre = checked_placement(
                reference_text,
                courtyard,
                preferred_side,
                other_courtyards,
            )
            move_text_centre(reference_text, target_centre)
            moved_count += 1

            if DEBUG:
                print(
                    f"{reference}: {preferred_side}, centre "
                    f"({iu_to_mm(target_centre.x):.3f}, "
                    f"{iu_to_mm(target_centre.y):.3f}) mm, visible gap "
                    f"{REFERENCE_OFFSET_MM:.3f} mm"
                )
        except Exception as error:
            error_count += 1
            print(f"Warning: {reference}: {error}; skipping it.")

    if DEBUG:
        print()
        print(f"Ignored references: {ignored_count}")
        print(f"Hidden references: {hidden_count}")
        print(f"Skipped with errors: {error_count}")

    return moved_count


board = pcbnew.GetBoard()

if board is None:
    print("Error: no board is currently open.")
else:
    try:
        moved_count = align_reference_labels(board)

        if moved_count > 0 and SAVE_BOARD_AFTER_ALIGNMENT:
            board_filename = board.GetFileName()

            if not board_filename:
                raise RuntimeError("the current board has no filename")

            pcbnew.SaveBoard(board_filename, board)
            print(f'Saved aligned references to "{board_filename}".')

        pcbnew.Refresh()
        print(f"Aligned {moved_count} component reference label(s).")
    except Exception as error:
        print(f"Error: {error}")
