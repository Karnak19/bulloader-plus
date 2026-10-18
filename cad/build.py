"""Build every part and export it as STL and STEP into out/.

Add a part: write a function returning a build123d shape, then add it to PARTS.
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Cone,
    Cylinder,
    Face,
    Location,
    Part,
    Plane,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    SlotOverall,
    Sketch,
    Text,
    Vector,
    Wire,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
    loft,
)

import params as p

OUT_DIR = Path(__file__).parent / "out"


def test_ring() -> Part:
    """Plain ring that should slide onto the inner barrel. M0 smoke test."""
    inner_d = p.BARREL_OD + p.FIT_TOLERANCE
    outer_d = inner_d + 2 * max(p.RING_WALL, p.MIN_WALL)
    return Cylinder(outer_d / 2, p.RING_HEIGHT) - Cylinder(inner_d / 2, p.RING_HEIGHT)


def collar_layout() -> dict[str, float]:
    """Key positions of the IR collar, shared by ir_collar() and check.py.

    Frame: the tube axis is Z, the collar sits on Z=0 (its print face). From Z=0 up:
    the bottom grip bore, the ring (BB guide, beam at its mid-height), the top grip
    bore. The beam runs along X, BEAM_OFFSET off the axis on -Y; the clamp slots and
    screws are on +Y, away from it.
    """
    bore_r = (p.BARREL_OD + p.FIT_TOLERANCE) / 2  # Grip bores, one per barrel half.
    guide_r = p.BB_GUIDE_D / 2
    led_r = (p.IR_LED_DIAMETER + p.SOCKET_TOLERANCE) / 2
    photo_r = (p.PHOTOTRANSISTOR_DIAMETER + p.SOCKET_TOLERANCE) / 2
    socket_r = max(led_r, photo_r)
    beam_y = -p.BEAM_OFFSET
    # Off-axis, the guide surface along the beam is at sqrt(guide_r^2 - y^2), furthest out where y is
    # nearest the axis. Measured at the socket edge nearest the axis (wider than the window), the
    # wall in front of each shoulder is at least APERTURE_LEN everywhere.
    near_y = max(0.0, abs(beam_y) - socket_r)
    shoulder_x = math.sqrt(guide_r**2 - near_y**2) + p.APERTURE_LEN  # Both stop shoulders sit at this |X|.
    # On a thick barrel, push the sockets out so the wire grooves on the back faces keep MIN_WALL
    # to the grip bore (the window just gets longer).
    groove_y = max(0.0, abs(beam_y) - p.WIRE_CHANNEL_W / 2)  # Groove edge nearest the axis.
    groove_x = math.sqrt((bore_r + p.MIN_WALL) ** 2 - groove_y**2) + p.WIRE_CHANNEL_DEPTH
    shoulder_x = max(shoulder_x, groove_x - p.SOCKET_DEPTH)
    nut_r = (p.M3_NUT_AF + p.NUT_TOLERANCE) / math.sqrt(3)  # Hexagon corner radius.
    screw_y = bore_r + p.MIN_WALL + nut_r  # Nut trap clears the bore by MIN_WALL.
    ring_z0 = p.GRIP_LENGTH
    ring_z1 = p.GRIP_LENGTH + p.BARREL_GAP
    length = ring_z1 + p.GRIP_LENGTH
    return {
        "bore_r": bore_r,
        "guide_r": guide_r,
        "outer_r": bore_r + p.COLLAR_WALL,
        "length": length,
        "ring_z0": ring_z0,  # Shoulder the bottom half stops on.
        "ring_z1": ring_z1,  # Shoulder the top half stops on.
        "beam_z": (ring_z0 + ring_z1) / 2,
        "beam_y": beam_y,
        "led_r": led_r,  # LED socket, on -X.
        "photo_r": photo_r,  # Phototransistor socket, on +X.
        "socket_r": socket_r,
        "shoulder_x": shoulder_x,
        "back_x": shoulder_x + p.SOCKET_DEPTH,  # Back face, where the leads come out.
        "bar_hw": max(socket_r + p.SOCKET_WALL, p.WIRE_CHANNEL_W / 2 + p.MIN_WALL),
        "nut_r": nut_r,
        "screw_y": screw_y,
        "screw_z": (p.GRIP_LENGTH / 2, length - p.GRIP_LENGTH / 2),  # One screw per grip, at mid-grip.
        "ear_y": screw_y + nut_r + p.MIN_WALL,  # Outer face of the clamp ears.
        "ear_hx": p.CLAMP_SLOT / 2 + p.M3_NUT_THICKNESS + p.NUT_TOLERANCE + p.MIN_WALL,
        "channel_top": (ring_z0 + ring_z1) / 2 - socket_r - p.MIN_WALL / 2,
    }


def _yz_plane(x: float, y: float, z: float, into: float) -> Plane:
    """Plane facing along X (into = +1 or -1), local x = global Y."""
    return Plane(origin=(x, y, z), x_dir=(0, 1, 0), z_dir=(into, 0, 0))


def ir_collar() -> Part:
    """Sleeve that joins the two halves of the cut barrel and holds the IR LED and phototransistor.

    Each end is a grip bore for one barrel half, closed by its own C-clamp (slot on +Y,
    one M3 screw through two ears, nut in a trap). Between them, a closed ring: its faces
    are the stops both halves butt against, its bore guides the BBs across the gap, and
    the beam crosses it through the sockets' window. The slots stop at the ring, so the
    screws never squeeze the BB guide. One piece, so both sockets come out of the same
    print layers and stay coaxial. Print it standing on its end face (Z=0): every hole
    across the tube is then horizontal and small, the nut traps have a corner on top,
    and the ring overhang is short, so no supports.
    """
    assert p.SOCKET_DEPTH < p.IR_BODY_LENGTH, "the flange would hit the back before the shoulder"
    k = collar_layout()
    assert max(p.APERTURE_D, p.APERTURE_W) < 2 * min(k["led_r"], k["photo_r"]) - p.SOCKET_TOLERANCE, (
        "the aperture must be narrower than the component, or there is no shoulder to stop it"
    )
    assert k["channel_top"] > p.MIN_WALL, "collar too short for the wire channels"
    assert p.BEAM_OFFSET + p.APERTURE_W / 2 < k["guide_r"], "the window pokes past the BB guide"
    assert p.BARREL_ID < p.BB_GUIDE_D < p.BARREL_OD, "BB guide must be over the barrel bore, under its OD"
    assert k["guide_r"] + p.RING_CHAMFER < k["bore_r"], "chamfer eats the whole shoulder"
    assert p.BARREL_GAP / 2 >= k["socket_r"] + p.SOCKET_WALL - 1e-9, "sockets break into the grip bores"
    L, z0, y0 = k["length"], k["beam_z"], k["beam_y"]

    # Outer outline, seen from above: ring + bar holding the sockets (on the beam line) + clamp ears.
    outline = (
        Circle(k["outer_r"])
        + Pos(0, y0) * Rectangle(2 * k["back_x"], 2 * k["bar_hw"])
        + Pos(0, k["ear_y"] / 2) * Rectangle(2 * k["ear_hx"], k["ear_y"])
    )
    # Round the outer corners only: those where the ring meets the bar or the ears are concave,
    # not sharp in the hand, and the short edges next to them make the 2D fillet fail.
    corners = [v for v in outline.vertices() if abs(math.hypot(v.X, v.Y) - k["outer_r"]) > 1e-6]
    outline = fillet(corners, p.EDGE_FILLET)
    body = extrude(outline, L)

    # BB guide through the whole length, then a grip bore and a clamp slot from each end up to
    # the ring. The slots stop at the ring, so it stays a closed circle whatever the screws do.
    body -= Pos(0, 0, -1) * Cylinder(k["guide_r"], L + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = p.RING_CHAMFER
    for z_start, z_ring, up in ((-1, k["ring_z0"], 1), (L + 1, k["ring_z1"], -1)):
        grip = abs(z_ring - z_start)
        z_mid = (z_start + z_ring) / 2
        body -= Pos(0, 0, z_mid) * Cylinder(k["bore_r"], grip)
        body -= Pos(0, k["ear_y"] / 2, z_mid) * Box(p.CLAMP_SLOT, k["ear_y"] + 1, grip)
        # 45 deg chamfer on the guide edge: radius guide_r + c at the ring face, guide_r c into the ring.
        cone = Cone(k["guide_r"] + c + 0.01, k["guide_r"] - 0.01, c + 0.02)
        body -= Pos(0, 0, z_ring + up * (c / 2 + 0.005)) * (cone if up > 0 else Rot(180, 0, 0) * cone)

    # Sockets: LED on -X, phototransistor on +X, both on the beam line y0, open at the back.
    # Each ends on a flat shoulder at shoulder_x, the same on both sides.
    socket_len = p.SOCKET_DEPTH + 1  # Runs 1 mm past the back face for a clean cut.
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        x_mid = side * (k["shoulder_x"] + socket_len / 2)
        body -= Pos(x_mid, y0, z0) * Rot(0, 90, 0) * Cylinder(r, socket_len)

    # Aperture: one window straight through both sides of the ring, so the two cannot drift apart.
    # It is a chord of the BB guide.
    if p.APERTURE_W > p.APERTURE_D:
        window = SlotOverall(p.APERTURE_W, p.APERTURE_D)
    else:
        window = Circle(p.APERTURE_D / 2)
    reach = k["shoulder_x"] + 0.5
    body -= extrude(_yz_plane(-reach, y0, z0, 1) * window, 2 * reach)

    # Wire channels: a groove on each back face, from under the socket to the bottom end.
    for side in (-1, 1):
        x = side * (k["back_x"] - p.WIRE_CHANNEL_DEPTH / 2)
        h = k["channel_top"] + 1
        body -= Pos(x, y0, h / 2 - 1) * Box(p.WIRE_CHANNEL_DEPTH + 0.01, p.WIRE_CHANNEL_W, h)

    # One M3 screw across the ears of each clamp, head on -X, nut trapped in the +X ear.
    ear_span = 2 * k["ear_hx"] + 2
    nut_depth = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE
    # rotation=90 puts a hexagon corner on top (+Z), so the pocket roof prints without support.
    hexagon = RegularPolygon(k["nut_r"], 6, rotation=90)
    for zs in k["screw_z"]:
        body -= Pos(0, k["screw_y"], zs) * Rot(0, 90, 0) * Cylinder(p.M3_CLEARANCE / 2, ear_span)
        body -= extrude(_yz_plane(k["ear_hx"] + 1, k["screw_y"], zs, -1) * hexagon, nut_depth + 1)
    return body


def shaft_bore_profile(kind: str, offset: float) -> Sketch:
    """Cross-section of a hole for the encoder shaft, centred on the origin.

    kind "dflat": SHAFT_D + offset round, with the flat on +X at SHAFT_FLAT + offset
    from the opposite side. kind "round": a plain SHAFT_D + offset circle.
    """
    r = (p.SHAFT_D + offset) / 2
    if kind == "round":
        return Circle(r)
    assert kind == "dflat", f"unknown bore kind {kind!r}"
    flat_x = -r + p.SHAFT_FLAT + offset
    assert -r < flat_x < r, "SHAFT_FLAT must be smaller than SHAFT_D"
    w = flat_x + r + 1  # From 1 mm past the round side to the flat.
    return Circle(r) & Pos(flat_x - w / 2, 0) * Rectangle(w, 2 * r + 2)


def knob_layout() -> dict[str, float]:
    """Key sizes of the encoder knob, shared by encoder_knob() and check.py.

    Frame (print orientation): the axis is Z, the top face lies on Z=0 (the bed),
    the recess opens at Z=KNOB_HEIGHT and the bore goes down from the recess.
    """
    offset = p.SHAFT_TOLERANCE if p.KNOB_BORE == "dflat" else p.KNOB_PRESS_FIT
    bore_r = (p.SHAFT_D + offset) / 2
    nut_corner_r = p.ENCODER_NUT_AF / math.sqrt(3)
    # Pushed fully down, the shaft tip touches the bore end. The recess ceiling then
    # sits KNOB_SHAFT_GAP above the nut, and the skirt KNOB_PANEL_GAP above the panel.
    recess_depth = p.ENCODER_TOP_HEIGHT + p.KNOB_SHAFT_GAP - p.KNOB_PANEL_GAP
    bore_depth = p.SHAFT_FREE_LENGTH - p.KNOB_SHAFT_GAP
    recess_top = p.KNOB_HEIGHT - recess_depth  # Z of the recess ceiling (its floor while printing).
    return {
        "outer_r": p.KNOB_OD / 2,
        "bore_offset": offset,
        "bore_r": bore_r,
        "flat_x": -bore_r + p.SHAFT_FLAT + offset if p.KNOB_BORE == "dflat" else None,
        "bore_depth": bore_depth,
        "bore_end": recess_top - bore_depth,  # Z of the bore end, i.e. the cap thickness.
        "recess_r": nut_corner_r + p.KNOB_RECESS_CLEARANCE,
        "recess_depth": recess_depth,
        "recess_top": recess_top,
        "groove_r": (p.KNOB_RIDGE_WIDTH**2 / 4 + p.KNOB_RIDGE_DEPTH**2) / (2 * p.KNOB_RIDGE_DEPTH),
    }


def encoder_knob() -> Part:
    """Big ridged knob for the KY-040 encoder, to turn with gloves on.

    Print it top face down (Z=0 on the bed). The recess for the nut and the shaft
    bore both open upward, so every layer sits on the one below: no supports.
    The top-edge chamfer is a 45 deg slope at the bed, which also hides elephant's foot.
    """
    k = knob_layout()
    R, H = k["outer_r"], p.KNOB_HEIGHT
    assert k["bore_end"] >= p.MIN_WALL, "knob too short for the bore, the recess and a MIN_WALL cap: raise KNOB_HEIGHT"
    assert k["recess_depth"] > 0, "KNOB_PANEL_GAP leaves no recess"
    assert R - p.KNOB_RIDGE_DEPTH - k["recess_r"] >= p.MIN_WALL, "skirt wall too thin round the recess"
    pitch = 2 * math.pi * R / p.KNOB_RIDGES
    assert p.KNOB_RIDGE_WIDTH + 2 * p.KNOB_RIDGE_FILLET < pitch, "grooves too wide for their number"

    # Side: a circle with KNOB_RIDGES round grooves, every edge rounded.
    gr = k["groove_r"]
    outline = Circle(R)
    for i in range(p.KNOB_RIDGES):
        a = 2 * math.pi * i / p.KNOB_RIDGES
        d = R + gr - p.KNOB_RIDGE_DEPTH
        outline -= Pos(d * math.cos(a), d * math.sin(a)) * Circle(gr)
    outline = fillet(outline.vertices(), p.KNOB_RIDGE_FILLET)
    body = extrude(outline, H)

    # Top-edge chamfer: intersect with a cylinder chamfered at Z=0.
    blank = Cylinder(R + 0.01, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    blank = chamfer(blank.edges().sort_by(Axis.Z)[0], p.KNOB_TOP_CHAMFER)
    body &= blank

    # Recess for the nut and bushing, open at Z=H.
    body -= Pos(0, 0, H) * Cylinder(k["recess_r"], 2 * k["recess_depth"])

    # Shaft bore, down from the recess ceiling, with a lead-in cone.
    profile = shaft_bore_profile(p.KNOB_BORE, k["bore_offset"])
    body -= Pos(0, 0, k["bore_end"]) * extrude(profile, k["bore_depth"] + 0.5)
    c = p.KNOB_BORE_CHAMFER
    body -= Pos(0, 0, k["recess_top"] - c) * Cone(
        k["bore_r"], k["bore_r"] + c + 0.01, c + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return body


def coupon_layout() -> dict[str, float]:
    """Row positions of the fit coupon, shared by fit_coupon() and check.py.

    From +Y to -Y: socket rib, socket labels, barrel bores, their labels, BB guide
    bores, their labels, then a thicker strip with the D-flat knob bores, their labels,
    the round ones, their labels.
    """
    gap, text = p.COUPON_GAP, p.COUPON_TEXT_SIZE
    bore_d = p.BARREL_OD + max(p.COUPON_BORE_OFFSETS)
    knob_d = p.SHAFT_D + max(p.COUPON_SHAFT_OFFSETS + p.COUPON_PRESS_OFFSETS)
    row = knob_d / 2 + gap / 2 + text / 2  # From a knob bore row to its label row.
    bore_label_y = -(bore_d / 2 + gap / 2 + text / 2)
    guide_d = p.BB_GUIDE_D + max(p.COUPON_GUIDE_OFFSETS)
    guide_y = bore_label_y - text / 2 - gap / 2 - guide_d / 2
    guide_label_y = guide_y - guide_d / 2 - gap / 2 - text / 2
    strip_y = guide_label_y - text / 2 - gap / 2
    dflat_y = strip_y - gap / 2 - knob_d / 2
    press_y = dflat_y - 2 * row  # Below the D-flat labels.
    socket_label_y = bore_d / 2 + gap / 2 + text / 2
    rib_y0 = socket_label_y + text / 2 + gap / 2
    return {
        "width": (bore_d + gap) * len(p.COUPON_BORE_OFFSETS) + gap,
        "bore_d": bore_d,
        "bore_y": 0.0,
        "bore_label_y": bore_label_y,
        "guide_y": guide_y,
        "guide_label_y": guide_label_y,
        "socket_label_y": socket_label_y,
        "rib_y0": rib_y0,
        "strip_y": strip_y,  # The knob strip covers everything below this.
        "dflat_y": dflat_y,
        "press_y": press_y,
        "knob_label_dy": row,  # Each knob label sits this far below its hole.
        "y_min": press_y - row - text / 2 - gap / 2,
        "y_max": rib_y0 + p.SOCKET_DEPTH,
    }


def fit_coupon() -> Part:
    """Thin plate to print first: test holes for every fit, at several tolerances.

    Each hole is labelled with the offset it adds. Slide it on the barrel, push in the
    IR components and the encoder shaft, then copy the best offsets into FIT_TOLERANCE,
    SOCKET_TOLERANCE, SHAFT_TOLERANCE and KNOB_PRESS_FIT. Drop a BB through the BB
    guide row: it must fall through the 0 hole freely, or BB_GUIDE_D goes up.
    The socket holes are horizontal, in a rib, like in the printed collar. The knob
    bores are vertical, in a thicker strip, like in the knob.
    """
    t, text = p.COUPON_THICKNESS, p.COUPON_TEXT_SIZE
    k = coupon_layout()
    width, y_min, y_max, rib_y0 = k["width"], k["y_min"], k["y_max"], k["rib_y0"]
    sockets = [p.IR_LED_DIAMETER + o for o in p.COUPON_SOCKET_OFFSETS]
    rib_h = max(sockets) + 2 * p.MIN_WALL
    tk = p.COUPON_KNOB_THICKNESS

    outline = Pos(0, (y_min + y_max) / 2) * Rectangle(width, y_max - y_min)
    outline = fillet(outline.vertices(), p.EDGE_FILLET)
    rib_outline = outline & Pos(0, (rib_y0 + y_max) / 2 + 1) * Rectangle(width + 2, y_max - rib_y0 + 2)
    strip_outline = outline & Pos(0, (y_min + k["strip_y"]) / 2 - 1) * Rectangle(width + 2, k["strip_y"] - y_min + 2)
    part = extrude(outline, t) + extrude(rib_outline, rib_h) + extrude(strip_outline, tk)

    def label(value: float) -> str:
        return "0" if abs(value) < 1e-9 else f"{value:+.1f}".replace("0.", ".")

    def engrave(s: str, x: float, y: float, top: float = t) -> Part:
        return Pos(x, y, top - p.COUPON_TEXT_DEPTH) * extrude(Text(s, text), p.COUPON_TEXT_DEPTH + 0.1)

    x0 = -width / 2 + p.COUPON_GAP + k["bore_d"] / 2
    pitch = k["bore_d"] + p.COUPON_GAP
    for i, offset in enumerate(p.COUPON_BORE_OFFSETS):
        x = x0 + i * pitch
        part -= Pos(x, k["bore_y"], t / 2) * Cylinder((p.BARREL_OD + offset) / 2, t + 1)
        part -= engrave(label(offset), x, k["bore_label_y"])

    # BB guide bores: vertical, like the ring in the collar printed standing.
    for i, offset in enumerate(p.COUPON_GUIDE_OFFSETS):
        x = -width / 2 + width / len(p.COUPON_GUIDE_OFFSETS) * (i + 0.5)
        part -= Pos(x, k["guide_y"], t / 2) * Cylinder((p.BB_GUIDE_D + offset) / 2, t + 1)
        part -= engrave(label(offset), x, k["guide_label_y"])

    s_pitch = width / len(sockets)
    for i, (d, offset) in enumerate(zip(sockets, p.COUPON_SOCKET_OFFSETS)):
        x = -width / 2 + s_pitch * (i + 0.5)
        hole_len = p.SOCKET_DEPTH + 2
        part -= Pos(x, (rib_y0 + y_max) / 2, rib_h / 2) * Rot(90, 0, 0) * Cylinder(d / 2, hole_len)
        part -= engrave(label(offset), x, k["socket_label_y"])

    # Knob bores: D-flat ones (flat on +X) then round press-fit ones, through the strip.
    for kind, y, offsets in (
        ("dflat", k["dflat_y"], p.COUPON_SHAFT_OFFSETS),
        ("round", k["press_y"], p.COUPON_PRESS_OFFSETS),
    ):
        for i, offset in enumerate(offsets):
            x = -width / 2 + width / len(offsets) * (i + 0.5)
            part -= Pos(x, y, -0.5) * extrude(shaft_bore_profile(kind, offset), tk + 1)
            part -= engrave(label(offset), x, y - k["knob_label_dy"], tk)
    return part


# --- Interior: ramp and battery tray (#52) -------------------------------------
# Frame: X across the box, Y along it (+Y = mechanism end), Z up, floor at Z = 0.
# Every part is first built too wide, then clipped to the box interior, so the
# side clearance follows the wall taper and the floor fillet on its own.

X_WIDE = (-40.0, 120.0)  # Wider than the box at any height, before clipping.
Z_LOW = 20.0  # Below every sloped part, for the bodies that get cut by the ramp surface.


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Part:
    """Axis-aligned box from its ranges."""
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN))


def fuse(parts: list[Part]) -> Part:
    """Union of a list of solids."""
    out = parts[0]
    for q in parts[1:]:
        out += q
    return out


def section_y(y: float, pts: list[tuple[float, float]]) -> Face:
    """Polygon (x, z) in the plane Y = y."""
    return Face(Wire.make_polygon([Vector(x, y, z) for x, z in pts], close=True))


def section_x(x: float, pts: list[tuple[float, float]]) -> Face:
    """Polygon (y, z) in the plane X = x."""
    return Face(Wire.make_polygon([Vector(x, y, z) for y, z in pts], close=True))


def prism_y(pts: list[tuple[float, float]], y0: float, y1: float) -> Part:
    return loft([section_y(y0, pts), section_y(y1, pts)], ruled=True)


def prism_x(pts: list[tuple[float, float]], x0: float, x1: float) -> Part:
    return loft([section_x(x0, pts), section_x(x1, pts)], ruled=True)


def wall_x(z: float, side: int) -> float:
    """Inner surface of the left (side -1) or right (side +1) box wall at height z."""
    return p.BOX_CX + side * (p.BOX_W0 + p.BOX_TAPER * z) / 2


def interior(side: float, end: float = 0.0) -> Part:
    """Box interior shrunk by `side` on the side walls and `end` at the far end. The floor fillet
    is cleared along its chord, which lies outside the real curve."""

    def pt(z: float, s: int, inset: float) -> tuple[float, float]:
        return (wall_x(z, s) - s * (side + inset), z)

    pts = [
        pt(0, -1, p.FLOOR_FILLET_W),
        pt(0, 1, p.FLOOR_FILLET_W),
        pt(p.FLOOR_FILLET_H, 1, 0),
        pt(p.BOX_H, 1, 0),
        pt(p.BOX_H, -1, 0),
        pt(p.FLOOR_FILLET_H, -1, 0),
    ]
    return prism_y(pts, p.BOX_Y0 + end, p.BOX_Y1)


def funnel_reach() -> float:
    """Widest distance from the inlet band to a side of the sheet, in the funnel."""
    z = p.INLET_Z + 10
    left = p.INLET_X0 - (wall_x(z, -1) + p.RAMP_WALL_CLEARANCE)
    right = (wall_x(z, 1) - p.RAMP_WALL_CLEARANCE) - p.INLET_X1
    return max(left, right)


def funnel_steepening() -> float:
    """Extra slope of the inlet band inside the funnel. The sideways tilt grows along Y, which
    lifts the sides as they come forward; without this, a strip some 30 mm from each wall would
    be almost flat. With it, even the sheet edge at the wall keeps RAMP_SLOPE."""
    return funnel_reach() * math.tan(math.radians(p.FUNNEL_SLOPE)) / p.FUNNEL_LENGTH


def ramp_top(x: float, y: float) -> float:
    """Height of the ramp's top surface: the main slope (steeper in the inlet band over the
    funnel), plus the sideways funnel that grows from 0 to FUNNEL_SLOPE over FUNNEL_LENGTH,
    measured from the edges of the inlet band."""
    zc = p.INLET_Z + (p.INLET_Y - y) * math.tan(math.radians(p.RAMP_SLOPE))
    zc += funnel_steepening() * min(p.FUNNEL_LENGTH, max(0.0, p.RAMP_FRONT_Y - y))
    f = min(1.0, max(0.0, (y - (p.RAMP_FRONT_Y - p.FUNNEL_LENGTH)) / p.FUNNEL_LENGTH))
    d = max(p.INLET_X0 - x, x - p.INLET_X1, 0.0)
    return zc + f * d * math.tan(math.radians(p.FUNNEL_SLOPE))


def ramp_thickness_z() -> float:
    """Vertical sheet thickness giving at least RAMP_T square to the steepest part of the surface."""
    tilt = math.atan(math.hypot(math.tan(math.radians(p.RAMP_SLOPE)), math.tan(math.radians(p.FUNNEL_SLOPE))))
    return p.RAMP_T / math.cos(tilt)


def ramp_layer(y0: float, y1: float, dz_top: float, dz_bottom: float | None = None, z_bottom: float = 0.0) -> Part:
    """Solid under the ramp surface shifted by dz_top, down to the surface shifted by dz_bottom
    (a sheet) or, without it, down to the flat z_bottom. The surface is linear in Y between
    the stations, so a ruled loft through them is exact."""
    stations = [y0]
    stations += [y for y in (p.RAMP_FRONT_Y - p.FUNNEL_LENGTH, p.RAMP_FRONT_Y) if y0 < y < y1]
    stations.append(y1)
    xs = (X_WIDE[0], p.INLET_X0, p.INLET_X1, X_WIDE[1])

    def sec(y: float) -> Face:
        top = [(x, ramp_top(x, y) + dz_top) for x in xs]
        if dz_bottom is None:
            bottom = [(X_WIDE[1], z_bottom), (X_WIDE[0], z_bottom)]
        else:
            bottom = [(x, ramp_top(x, y) + dz_bottom) for x in reversed(xs)]
        return section_y(y, top + bottom)

    return loft([sec(y) for y in stations], ruled=True)


def under_ramp(z_bottom: float) -> Part:
    """Everything under the ramp surface (minus 0.3, so what is cut by it still fuses into the sheet)."""
    return ramp_layer(p.BOX_Y0 - 5, p.INLET_Y + 5, -0.3, z_bottom=z_bottom)


def drain_top(y: float) -> float:
    """Top of the IN drain sheet: IN_DRAIN_Z under the IN axis, falling toward -Y at IN_DRAIN_SLOPE."""
    return p.IN_DRAIN_Z + (y - p.IN_Y) * math.tan(math.radians(p.IN_DRAIN_SLOPE))


def front_y_left() -> float:
    """Top edge of the front wall left of the mechanism: far enough forward that the whole wall
    stays out of the left wire chase."""
    return p.MECH_Y0 - p.MECH_CLEARANCE - p.FRONT_T * math.sqrt(2)


def front_wall(x0: float, x1: float, y_top: float) -> Part:
    """45 deg wall rising from the sheet toward +Y, to the wing at MECH_TOP_Z on its edge y_top.
    BBs that reach it roll back down; it also prints without support (ramp_b stands on end)."""
    t = p.FRONT_T * math.sqrt(2)  # Its width along Y.
    wing_top = p.MECH_TOP_Z + p.WING_T

    def yf(z: float) -> float:
        return y_top - (p.MECH_TOP_Z - z)

    pts = [(yf(Z_LOW), Z_LOW), (y_top, p.MECH_TOP_Z), (y_top, wing_top), (yf(wing_top) + t, wing_top), (yf(Z_LOW) + t, Z_LOW)]
    return prism_x(pts, x0, x1)


def left_front_x1() -> float:
    """Right end of the forward-set front wall on the left: past the left chase and past the
    boss under the plate, which the wing lip must stay in front of."""
    return max(p.MECH_X0, p.PLATE_BOSS[0][1] + 0.5)


def wing_lip(x0: float, x1: float, y_top: float) -> Part:
    """Lip on the wing's front edge, leaning forward at 45 deg up to WING_LIP_GAP under the plate.
    With a full box the pile reaches the plate: without it, a layer of BBs would be pushed over
    the wings and stranded there. Leaning forward keeps it clear of the boss under the plate,
    and prints (ramp_b stands on end) as a 45 deg overhang."""
    t = p.FRONT_T * math.sqrt(2)
    top = p.PLATE_Z - p.WING_LIP_GAP
    rise = top - p.MECH_TOP_Z
    pts = [(y_top, p.MECH_TOP_Z), (y_top - rise, top), (y_top - rise + t, top), (y_top + t, p.MECH_TOP_Z)]
    return prism_x(pts, x0, x1)


def chute_wall(x0: float, x1: float) -> Part:
    """Side wall of the 31 mm chute into the inlet, from the front wall to the mechanism face."""
    pts = [(p.RAMP_FRONT_Y - (p.MECH_TOP_Z - Z_LOW), Z_LOW), (p.RAMP_FRONT_Y, p.MECH_TOP_Z),
           (p.RAMP_FRONT_Y, p.MECH_TOP_Z + p.WING_T), (p.INLET_Y, p.MECH_TOP_Z + p.WING_T), (p.INLET_Y, Z_LOW)]
    return prism_x(pts, x0, x1)


def split_plane() -> Plane:
    """Local frame at the split: origin on the sheet top on the split line, x' = X, y' down the
    slope (toward the mechanism), z' square to the sheet, up. The split face is y' = 0."""
    s = math.radians(p.RAMP_SLOPE)
    origin = (0.0, p.RAMP_SPLIT_Y, ramp_top(p.INLET_X0, p.RAMP_SPLIT_Y))
    return Plane(origin=origin, x_dir=(1, 0, 0), z_dir=(0, math.sin(s), math.cos(s)))


def local_prism(pts: list[tuple[float, float]], x0: float, x1: float) -> Part:
    """Prism along X from a (y', z') polygon in the split frame."""
    return Location(split_plane()) * prism_x(pts, x0, x1)


def joint_layout() -> dict[str, float]:
    """Tongue extent across X: the sheet width at the split, minus a shoulder each side."""
    z = ramp_top(p.INLET_X0, p.RAMP_SPLIT_Y)
    x0 = wall_x(z - ramp_thickness_z(), -1) + p.RAMP_WALL_CLEARANCE + p.JOINT_SHOULDER
    x1 = wall_x(z - ramp_thickness_z(), 1) - p.RAMP_WALL_CLEARANCE - p.JOINT_SHOULDER
    return {"x0": x0, "x1": x1, "screw_y": p.JOINT_LAP / 2}


def tongue(clearance: float = 0.0) -> Part:
    """The tongue, flush with the top, 45 deg at its end. With a clearance: the pocket that takes it."""
    k = joint_layout()
    c, L, D = clearance, p.JOINT_LAP, p.JOINT_DEPTH
    up = 1.0 if c else 0.0  # The pocket opens through the top.
    pts = [(-1.0, up), (L + c * math.sqrt(2) + D + up, up), (L + c * math.sqrt(2) - c, -D - c), (-1.0, -D - c)]
    return local_prism(pts, k["x0"] - c, k["x1"] + c)


def split_screws(in_tongue: bool) -> Part:
    """M3 holes square to the sheet: through the band below the pocket, or in the tongue with its nut trap."""
    k = joint_layout()
    r = p.M3_CLEARANCE / 2
    holes = []
    for x in p.SPLIT_SCREW_XS:
        if in_tongue:
            tip = -p.JOINT_BAND_T + p.SPLIT_SCREW_LEN + 0.5
            z0 = -p.JOINT_DEPTH - 1
            hole = Pos(x, k["screw_y"], z0) * Cylinder(r, tip - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
            nut_h = p.M3_NUT_THICKNESS + p.NUT_TOLERANCE + 1
            hole += Pos(x, k["screw_y"], z0) * extrude(RegularPolygon((p.M3_NUT_AF + p.NUT_TOLERANCE) / 2, 6, major_radius=False), nut_h)
        else:
            z0 = -p.JOINT_BAND_T - 2
            hole = Pos(x, k["screw_y"], z0) * Cylinder(r, -p.JOINT_DEPTH + 1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        holes.append(hole)
    return Location(split_plane()) * fuse(holes)


def ramp() -> Part:
    """The whole ramp, in the box frame, before the split."""
    global _RAMP
    if _RAMP is not None:
        return _RAMP
    tz = ramp_thickness_z()
    y_far = p.BOX_Y0 + p.RAMP_END_CLEARANCE
    under = under_ramp(Z_LOW)
    # Sheet, stopped short of the wire chases each side of the mechanism.
    part = ramp_layer(y_far, p.INLET_Y, 0.0, dz_bottom=-tz)
    cut_y = p.MECH_Y0 - p.MECH_CLEARANCE
    part -= box(X_WIDE[0], p.MECH_X0, cut_y, 50, 0, 100) + box(p.MECH_X1, X_WIDE[1], cut_y, 50, 0, 100)
    # Front walls up to the wings, either side of the chute, and the chute's side walls.
    xl = left_front_x1()
    walls = front_wall(X_WIDE[0], xl, front_y_left())
    walls += front_wall(xl, p.INLET_X0 - p.CHUTE_WALL, p.RAMP_FRONT_Y)
    walls += front_wall(p.INLET_X1 + p.CHUTE_WALL, p.MECH_X1, p.RAMP_FRONT_Y)
    walls += chute_wall(p.INLET_X0 - p.CHUTE_WALL, p.INLET_X0) + chute_wall(p.INLET_X1, p.INLET_X1 + p.CHUTE_WALL)
    # IN drain: one plane at IN_DRAIN_SLOPE from behind the IN axis down into the sheet, over the
    # right chase, and a web closing its side in front of the mechanism.
    td = p.RAMP_T / math.cos(math.radians(p.IN_DRAIN_SLOPE))
    yb, yl = p.IN_DRAIN_BACK_Y, -80.0
    walls += prism_x([(yl, drain_top(yl)), (yb, drain_top(yb)), (yb, drain_top(yb) - td), (yl, drain_top(yl) - td)],
                     p.MECH_X1 + p.MECH_CLEARANCE, X_WIDE[1])
    y_web = p.MECH_Y0
    walls += prism_x([(yl, drain_top(yl)), (y_web, drain_top(y_web)), (y_web, Z_LOW), (yl, Z_LOW)],
                     p.MECH_X1, p.MECH_X1 + p.MECH_CLEARANCE + p.IN_DRAIN_WEB)
    part += walls - under
    # Wings on the mechanism top: OUT barrel hole, open wire pass over the left chase.
    wing_z = (p.MECH_TOP_Z, p.MECH_TOP_Z + p.WING_T)
    wing = box(X_WIDE[0], p.MECH_X1 + p.MECH_CLEARANCE, p.RAMP_FRONT_Y, p.WING_Y1, *wing_z)
    wing += box(X_WIDE[0], xl, front_y_left(), p.RAMP_FRONT_Y + 1, *wing_z)
    wing -= Pos(p.OUT_X, p.OUT_Y, p.MECH_TOP_Z) * Cylinder(p.OUT_HOLE_D / 2, 20)
    wing -= box(X_WIDE[0], p.WIRE_PASS_X1, p.WIRE_PASS_Y0, 50, 0, 100)
    part += wing
    part += wing_lip(X_WIDE[0], xl, front_y_left()) + wing_lip(xl, p.MECH_X1 + p.MECH_CLEARANCE, p.RAMP_FRONT_Y)
    # Under the sheet: the leg on the floor, the ribs and the band at the split.
    support = box(X_WIDE[0], X_WIDE[1], y_far, y_far + p.LEG_T, 0, 100)
    ribs = fuse([box(x - p.RIB_T / 2, x + p.RIB_T / 2, y_far, p.RAMP_FRONT_Y - 1, p.RIB_BOTTOM_Z, 100)
                 for x in p.RIB_XS])
    support += ribs & ramp_layer(y_far - 1, p.INLET_Y, 50.0, dz_bottom=-p.RIB_DEPTH)
    band = local_prism([(-p.JOINT_BAND_LEN, 0), (p.JOINT_BAND_LEN, 0), (p.JOINT_BAND_LEN, -p.JOINT_BAND_T),
                        (-p.JOINT_BAND_LEN, -p.JOINT_BAND_T)], X_WIDE[0], X_WIDE[1])
    support += band & box(X_WIDE[0], X_WIDE[1], -300, 100, p.RIB_BOTTOM_Z, 100)
    part += support & under_ramp(0.0)
    _RAMP = part & interior(p.RAMP_WALL_CLEARANCE, p.RAMP_END_CLEARANCE)
    return _RAMP


_RAMP = None


def split_half(side: int) -> Part:
    """Half-space y' <= 0 (side -1, ramp_a) or y' >= 0 (side +1, ramp_b) in the split frame."""
    pts = [(0, -200), (side * 400, -200), (side * 400, 200), (0, 200)]
    return local_prism(pts, X_WIDE[0], X_WIDE[1])


def ramp_a() -> Part:
    """Far piece: the sheet from the far end to the split, the leg, and the tongue."""
    tongue_part = tongue() & interior(p.RAMP_WALL_CLEARANCE)
    return (ramp() & split_half(-1)) + tongue_part - split_screws(in_tongue=True)


def ramp_b() -> Part:
    """Near piece: funnel, chute, front walls, wings and IN drain, with the pocket for the tongue."""
    return (ramp() & split_half(1)) - tongue(p.JOINT_CLEARANCE) - split_screws(in_tongue=False)


def print_pose(part: Part, angle: float) -> Part:
    """Rotate about X by `angle`, then sit on the bed (Z = 0) centred on the origin.
    ramp_a: 180 + slope puts its top face (the BB surface) on the bed.
    ramp_b: 90 + slope stands it on its split face."""
    r = Rot(angle, 0, 0) * part
    bb = r.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * r


def strap_stations() -> list[tuple[float, float]]:
    """(Y of the strap, X of its left slot) for every strap station."""
    yc = (p.BAY_Y[0] + p.BAY_Y[1]) / 2
    return [(yc - p.STRAP_PITCH / 2, p.STRAP_X_LEFT), (yc + p.STRAP_PITCH / 2, p.STRAP_X_LEFT),
            (p.LANE_STRAP_Y, p.LANE_STRAP_X)]


def battery_tray() -> Part:
    """Floor tray for the battery: a floor on cross runners (the strap passes under it), the bay,
    the lane past the servo, the lead strip to the left chase, low lips and the strap slots.
    Printed as it sits, runners on the bed."""
    rects = [(p.BAY_X, p.BAY_Y), (p.LANE_X, p.LANE_Y), (p.LEAD_X, p.LEAD_Y)]
    floor_z = (p.TRAY_RUNNER_H, p.TRAY_FLOOR_Z)
    footprint = fuse([box(*xr, *yr, 0, p.TRAY_FLOOR_Z) for xr, yr in rects])
    part = footprint & box(X_WIDE[0], X_WIDE[1], -300, 100, *floor_z)
    # Cross runners, skipped where a strap passes under the floor.
    stations = strap_stations()
    keep = p.STRAP_SLOT[1] / 2 + p.TRAY_RUNNER_W
    runners = []
    y = p.BAY_Y[0] + p.TRAY_RUNNER_W / 2
    while y <= p.LANE_Y[1] - p.TRAY_RUNNER_W / 2:
        if all(abs(y - ys) > keep for ys, _ in stations):
            runners.append(box(X_WIDE[0], X_WIDE[1], y - p.TRAY_RUNNER_W / 2, y + p.TRAY_RUNNER_W / 2, 0, p.TRAY_RUNNER_H + 0.1))
        y += p.TRAY_RUNNER_PITCH
    runners.append(box(X_WIDE[0], X_WIDE[1], p.LANE_Y[1] - p.TRAY_RUNNER_W, p.LANE_Y[1], 0, p.TRAY_RUNNER_H + 0.1))
    part += fuse(runners) & footprint
    # Lips: back of the bay, front of the bay (left of the lane, right of the lead strip), lead ridge.
    lip_z = (p.TRAY_RUNNER_H, p.TRAY_FLOOR_Z + p.TRAY_LIP_H)
    part += box(X_WIDE[0], X_WIDE[1], p.BAY_Y[0], p.BAY_Y[0] + p.TRAY_LIP_T, *lip_z)
    part += box(p.LEAD_X[1] - p.TRAY_LIP_T, p.LANE_X[0], p.BAY_Y[1] - p.TRAY_LIP_T, p.BAY_Y[1], *lip_z)
    part += box(p.LEAD_X[1] - p.TRAY_LIP_T, p.LEAD_X[1], p.BAY_Y[1] - p.TRAY_LIP_T, p.LEAD_Y[1] - 1, *lip_z)
    # Strap slots: a closed slot on the left, a notch open to the wall on the right.
    sw, sl = p.STRAP_SLOT
    for ys, xs in stations:
        part -= box(xs - sw / 2, xs + sw / 2, ys - sl / 2, ys + sl / 2, -1, 20)
        part -= box(p.STRAP_X_RIGHT - sw / 2, X_WIDE[1], ys - sl / 2, ys + sl / 2, -1, 20)
    return part & interior(p.TRAY_WALL_CLEARANCE)


PARTS = {
    "test_ring": test_ring,
    "ir_collar": ir_collar,
    "fit_coupon": fit_coupon,
    "encoder_knob": encoder_knob,
    "ramp_a": lambda: print_pose(ramp_a(), 180 + p.RAMP_SLOPE),
    "ramp_b": lambda: print_pose(ramp_b(), 90 + p.RAMP_SLOPE),
    "battery_tray": battery_tray,
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name, build in PARTS.items():
        part = build()
        for path, export in (
            (OUT_DIR / f"{name}.stl", export_stl),
            (OUT_DIR / f"{name}.step", export_step),
        ):
            if not export(part, str(path)) or path.stat().st_size == 0:
                raise SystemExit(f"export failed: {path}")
            print(f"wrote out/{path.name}")


if __name__ == "__main__":
    main()
