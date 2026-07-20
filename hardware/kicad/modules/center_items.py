import pcbnew

REFS = ["J1", "J2"]
HORIZONTAL_TOLERANCE_MM = 0.01
DEBUG = True

def mm_to_iu(mm):
    return pcbnew.FromMM(mm)

def iu_to_mm(iu):
    return pcbnew.ToMM(iu)

def is_horizontal_edge(shape, tol_iu):
    try:
        if shape.GetLayer() != pcbnew.Edge_Cuts:
            return False
    except Exception:
        return False

    try:
        if shape.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            return False
    except Exception:
        pass

    try:
        a = shape.GetStart()
        b = shape.GetEnd()
    except Exception:
        return False

    return abs(a.y - b.y) <= tol_iu

def find_board_vertical_center(board, tol_iu):
    ys = []

    for item in board.GetDrawings():
        if is_horizontal_edge(item, tol_iu):
            a = item.GetStart()
            b = item.GetEnd()
            ys.append((a.y + b.y) // 2)

    if len(ys) < 2:
        raise RuntimeError("Need at least two horizontal Edge.Cuts segments")

    ys.sort()
    bottom_y = ys[0]
    top_y = ys[-1]
    return (bottom_y + top_y) // 2, bottom_y, top_y

def get_footprint_by_ref(board, ref):
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise RuntimeError(f"Footprint {ref} not found")
    return fp

board = pcbnew.GetBoard()
tol_iu = mm_to_iu(HORIZONTAL_TOLERANCE_MM)

target_center_y, bottom_y, top_y = find_board_vertical_center(board, tol_iu)

for ref in REFS:
    fp = get_footprint_by_ref(board, ref)

    old_anchor = fp.GetPosition()
    bbox = fp.GetBoundingBox()

    bbox_center_y = bbox.GetY() + bbox.GetHeight() // 2
    delta_y = target_center_y - bbox_center_y

    new_anchor = pcbnew.VECTOR2I(old_anchor.x, old_anchor.y + delta_y)
    fp.SetPosition(new_anchor)

    if DEBUG:
        print(f"{ref}")
        print(f"  anchor old Y   : {iu_to_mm(old_anchor.y):.3f} mm")
        print(f"  bbox center old: {iu_to_mm(bbox_center_y):.3f} mm")
        print(f"  target center Y: {iu_to_mm(target_center_y):.3f} mm")
        print(f"  move delta Y   : {iu_to_mm(delta_y):.3f} mm")
        print(f"  anchor new Y   : {iu_to_mm(new_anchor.y):.3f} mm")

pcbnew.Refresh()

if DEBUG:
    print(f"Bottom edge Y: {iu_to_mm(bottom_y):.3f} mm")
    print(f"Top edge Y:    {iu_to_mm(top_y):.3f} mm")
    print(f"Board center Y:{iu_to_mm(target_center_y):.3f} mm")

