"""Sanity checks on the IR collar, the encoder knob and the fit coupon.

Run: uv run python check.py
Probes points just inside and just outside each feature, so a wrong bore, a missing
shoulder, a socket off its axis, two sockets that are not coaxial or a knob bore off
its axis fail loudly.
"""

import math

from build123d import Axis, GeomType, Vector

import build
import params as p

BARREL_ODS = (8.5, 9.0, 9.5)  # The plausible range from the brief.
EPS = 0.05  # How far on each side of a wall we probe.


def cylinders(part) -> list:
    """Cylindrical faces of a part (the radius is None on some faces OCC reports)."""
    return [f for f in part.faces() if f.geom_type == GeomType.CYLINDER and f.radius is not None]


def solid_at(part, x: float, y: float, z: float) -> bool:
    return part.is_inside(Vector(x, y, z))


def guide_x(k: dict, y: float) -> float:
    """Where the BB guide surface sits along a beam parallel to X at height y."""
    return math.sqrt(max(0.0, k["guide_r"] ** 2 - y**2))


def wall_thickness(part, x: float, y0: float, z0: float, r: float, c: float, s: float) -> float:
    """Solid measured outward from a socket surface along (c, s) in the YZ plane, capped at 4 mm."""
    t = 0.0
    while t < 4.0 and solid_at(part, x, y0 + (r + t + 0.02) * c, z0 + (r + t + 0.02) * s):
        t += 0.02
    return t


def check_collar(od: float) -> None:
    p.BARREL_OD = od
    part = build.ir_collar()
    k = build.collar_layout()
    assert part.is_valid, "collar is not a valid solid"
    assert len(part.solids()) == 1, f"collar has {len(part.solids())} solids"
    z_lo, z_hi, L = k["ring_z0"], k["ring_z1"], k["length"]
    assert abs(L - (2 * p.GRIP_LENGTH + p.BARREL_GAP)) < 1e-9, "length is not two grips plus the gap"
    assert abs(z_hi - z_lo - p.BARREL_GAP) < 1e-9, "ring length is not the barrel gap"

    # Grip bores: hollow just inside their radius, solid just outside, all round, at mid-grip
    # (away from the ring) except across the clamp slot.
    slot_half_angle = math.degrees(math.asin((p.CLAMP_SLOT / 2 + EPS) / k["bore_r"]))
    for z in (z_lo / 2, (z_hi + L) / 2, 0.5, L - 0.5, z_lo - 0.5, z_hi + 0.5):
        for deg in range(0, 360, 15):
            if abs(deg - 90) <= slot_half_angle + 1:
                continue
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            r_in, r_out = k["bore_r"] - EPS, k["bore_r"] + EPS
            assert not solid_at(part, r_in * c, r_in * s, z), f"grip bore too small at {deg} deg, z={z:.1f}"
            assert solid_at(part, r_out * c, r_out * s, z), f"grip bore too large at {deg} deg, z={z:.1f}"
        assert not solid_at(part, 0, k["bore_r"] + EPS, z), f"clamp slot missing at z={z:.1f}"
    # Grip long enough to hold a half straight: over one barrel diameter.
    assert p.GRIP_LENGTH >= od, f"GRIP_LENGTH {p.GRIP_LENGTH} under the barrel OD {od}"

    # BB guide: over the barrel bore (a BB never meets a step going in), under the barrel OD
    # (so there is a shoulder), probed all round on its flat part, above and below the window.
    assert p.BB_GUIDE_D > p.BARREL_ID, "BB guide narrower than the barrel bore"
    assert p.BARREL_ID < od - 2 * 0.5, "barrel wall implausibly thin"
    flat = p.BARREL_GAP / 2 - p.RING_CHAMFER  # Flat part of the guide, each side of the beam.
    for z in (k["beam_z"] - flat + EPS, k["beam_z"] + flat - EPS):
        for deg in range(0, 360, 15):
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            r_in, r_out = k["guide_r"] - EPS, k["guide_r"] + EPS
            assert not solid_at(part, r_in * c, r_in * s, z), f"BB guide too small at {deg} deg"
            assert solid_at(part, r_out * c, r_out * s, z), f"BB guide too large at {deg} deg"
    # The ring is closed: the clamp slots stop at it, so the screws never squeeze the guide.
    for y in (k["guide_r"] + EPS, k["bore_r"] + EPS, k["ear_y"] - EPS):
        assert solid_at(part, 0, y, k["beam_z"]), f"ring cut by the clamp slot at y={y:.2f}"

    # Shoulders, both sides: all round, solid just inside the ring, hollow just outside it,
    # so each barrel half stops on a flat face, and the gap is set by the print.
    shoulder = k["bore_r"] - k["guide_r"] - p.RING_CHAMFER  # Flat width each half butts on.
    assert shoulder > 0.3, f"shoulder only {shoulder:.2f} wide"
    r_sh = (k["guide_r"] + p.RING_CHAMFER + k["bore_r"]) / 2
    for deg in range(0, 360, 15):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        x, y = r_sh * c, r_sh * s
        assert solid_at(part, x, y, z_lo + EPS) and not solid_at(part, x, y, z_lo - EPS), f"no bottom shoulder at {deg}"
        assert solid_at(part, x, y, z_hi - EPS) and not solid_at(part, x, y, z_hi + EPS), f"no top shoulder at {deg}"
        # Chamfer: the guide edge is cut back at both faces.
        rc = k["guide_r"] + p.RING_CHAMFER / 2
        assert not solid_at(part, rc * c, rc * s, z_lo + EPS), f"no bottom chamfer at {deg}"
        assert not solid_at(part, rc * c, rc * s, z_hi - EPS), f"no top chamfer at {deg}"

    # Sockets: each one is a cylinder along X on the beam line (y = beam_y, z = beam_z),
    # i.e. both on one chord of the guide, BEAM_OFFSET off the axis.
    y0, z0 = k["beam_y"], k["beam_z"]
    assert abs(abs(y0) - p.BEAM_OFFSET) < 1e-9, "beam not BEAM_OFFSET off the axis"
    sockets = [
        f
        for f in cylinders(part)
        if min(abs(f.radius - k["led_r"]), abs(f.radius - k["photo_r"])) < 1e-6
        and abs(abs(f.axis_of_rotation.direction.X) - 1) < 1e-6
    ]
    sockets = [f for f in sockets if abs(f.axis_of_rotation.position.Y - y0) < 1e-6]
    sides = sorted({round(f.center().X, 3) for f in sockets})
    assert len(sockets) == 2, f"expected 2 socket faces, found {len(sockets)}"
    for f in sockets:
        axis = f.axis_of_rotation
        assert abs(axis.position.Z - z0) < 1e-6, "socket axis not at beam height"
        assert abs(axis.position.Y - y0) < 1e-6, "socket axis off the beam line"
    assert abs(sides[0] + sides[1]) < 1e-6, f"sockets not symmetric: {sides}"

    # The window fits inside the BB guide, so the whole beam crosses the BB path.
    assert p.BEAM_OFFSET + p.APERTURE_W / 2 < k["guide_r"], "window pokes past the BB guide"
    # Ring wall above and below the window, measured at the guide edge (inside the chamfer).
    window_wall = p.BARREL_GAP / 2 - p.APERTURE_D / 2 - p.RING_CHAMFER
    assert window_wall >= p.MIN_WALL, f"ring wall around the window only {window_wall:.2f}"
    x_w = guide_x(k, y0) + 0.3  # Just into the ring, on the beam line.
    for side in (-1, 1):
        for dz in (p.APERTURE_D / 2 + EPS, p.BARREL_GAP / 2 - p.RING_CHAMFER - EPS):
            assert solid_at(part, side * x_w, y0, z0 + dz), f"ring wall missing above the window, dz={dz:.2f}"
            assert solid_at(part, side * x_w, y0, z0 - dz), f"ring wall missing below the window, dz={dz:.2f}"
    # Sockets inside the ring's height with SOCKET_WALL to spare, so none breaks into a grip bore.
    socket_to_grip = p.BARREL_GAP / 2 - k["socket_r"]
    assert socket_to_grip >= p.SOCKET_WALL - 1e-9, f"socket only {socket_to_grip:.2f} from a grip bore"
    # Clamp slots, screws and nut traps stay on +Y, clear of the beam line and its sockets.
    assert y0 + k["socket_r"] < -EPS, "sockets reach the clamp slot side"
    screw_low = k["screw_y"] - max(p.M3_CLEARANCE / 2, k["nut_r"])
    assert screw_low - (y0 + k["bar_hw"]) >= p.MIN_WALL, "screw or nut trap hits the socket bar"
    assert screw_low - k["bore_r"] >= p.MIN_WALL - 1e-9, "nut trap too close to the grip bore"
    for zs, z_in in zip(k["screw_z"], (z_lo, z_hi)):
        # Nut trap inside the collar with MIN_WALL to the end, screw hole entirely over its slot.
        assert min(zs, L - zs) - k["nut_r"] >= p.MIN_WALL - 1e-9, "nut trap too close to the collar end"
        assert abs(z_in - zs) - p.M3_CLEARANCE / 2 > 0, "screw reaches the ring, past its slot"
        assert not solid_at(part, 0, k["screw_y"], zs), "screw hole missing"
        assert not solid_at(part, k["ear_hx"] - EPS, k["screw_y"], zs), "nut trap missing"
    # Wire grooves: on the back faces, -Y side, clear of the grip bore by MIN_WALL.
    gx, gy = k["back_x"] - p.WIRE_CHANNEL_DEPTH, max(0.0, abs(y0) - p.WIRE_CHANNEL_W / 2)
    groove_wall = math.hypot(gx, gy) - k["bore_r"]
    assert groove_wall >= p.MIN_WALL - 1e-9, f"wire groove only {groove_wall:.2f} from the grip bore"
    for side in (-1, 1):
        x = side * (k["back_x"] - p.WIRE_CHANNEL_DEPTH / 2)
        assert not solid_at(part, x, y0, 0.5), "wire groove missing at the bottom end"
        assert not solid_at(part, x, y0, k["channel_top"] - EPS), "wire groove too short"
        assert solid_at(part, x, y0, k["channel_top"] + EPS), "wire groove runs into the socket"

    # Probe both sockets the same way: hollow inside, solid outside, all round.
    walls, shoulder_walls = [], []
    for side, r in ((-1, k["led_r"]), (1, k["photo_r"])):
        for x in (side * (k["shoulder_x"] + 0.2), side * (k["shoulder_x"] + p.SOCKET_DEPTH / 2)):
            for deg in range(0, 360, 30):
                c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
                assert not solid_at(part, x, y0 + (r - EPS) * c, z0 + (r - EPS) * s), "socket too small"
                assert solid_at(part, x, y0 + (r + EPS) * c, z0 + (r + EPS) * s), "socket too large"
                # Wall all round the socket: still solid MIN_WALL out from its surface.
                w = r + p.MIN_WALL - EPS
                assert solid_at(part, x, y0 + w * c, z0 + w * s), f"socket wall under MIN_WALL at {deg} deg"
                walls.append(wall_thickness(part, x, y0, z0, r, c, s))
        # Stop shoulder: solid just in front of it (outside the aperture), hollow just behind.
        ring = (r + p.APERTURE_D / 2) / 2
        assert solid_at(part, side * (k["shoulder_x"] - EPS), y0, z0 + ring), "no socket shoulder"
        assert not solid_at(part, side * (k["shoulder_x"] + EPS), y0, z0 + ring), "socket shoulder misplaced"
        # Aperture: open on the beam line through the wall, closed just above it and just beside it.
        x_ap = side * (guide_x(k, y0) + k["shoulder_x"]) / 2
        assert not solid_at(part, x_ap, y0, z0), "aperture blocked"
        assert solid_at(part, x_ap, y0, z0 + p.APERTURE_D / 2 + EPS), "aperture too tall"
        assert solid_at(part, x_ap, y0 + p.APERTURE_W / 2 + EPS, z0), "aperture too wide"
        # Window wall at least APERTURE_LEN long on its worst edge (the one nearest the axis),
        # and on the whole socket face.
        for y in (y0 + p.APERTURE_W / 2, y0 - p.APERTURE_W / 2, y0 + r, y0 - r):
            wall = k["shoulder_x"] - guide_x(k, y)
            assert wall >= p.APERTURE_LEN - 1e-9, f"wall in front of the shoulder {wall:.2f} at y={y:.2f}"
            shoulder_walls.append(wall)
        # Socket closed above and below along the tube: the light shield.
        x = side * (k["shoulder_x"] + p.SOCKET_DEPTH / 2)
        assert solid_at(part, x, y0, z0 + r + p.SOCKET_WALL / 2), "no wall above socket"
    # The beam line itself is clear from one shoulder to the other.
    for i in range(41):
        x = -k["shoulder_x"] + 2 * k["shoulder_x"] * i / 40
        assert not solid_at(part, x, y0, z0), f"beam blocked at x={x:.2f}"

    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - L) < 1e-6, "length wrong"
    print(
        f"BARREL_OD {od}: collar OK  grip d={2 * k['bore_r']:.2f} x {p.GRIP_LENGTH:.1f}  "
        f"guide d={2 * k['guide_r']:.2f} x {p.BARREL_GAP:.1f}  shoulder {shoulder:.2f}  "
        f"sockets at x={sides[0]:+.2f}/{sides[1]:+.2f} on y={y0:+.2f} z={z0:.2f}  "
        f"min socket wall {min(walls):.2f}  min window wall {min(shoulder_walls):.2f}  "
        f"ring wall by window {window_wall:.2f}  groove wall {groove_wall:.2f}  "
        f"size {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {part.volume:.0f} mm3"
    )


def check_knob(kind: str) -> None:
    p.KNOB_BORE = kind
    part = build.encoder_knob()
    k = build.knob_layout()
    assert part.is_valid, "knob is not a valid solid"
    assert len(part.solids()) == 1, f"knob has {len(part.solids())} solids"
    H, R = p.KNOB_HEIGHT, k["outer_r"]
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - H) < 1e-6, "knob height wrong"
    # The ridge tops are flattened by the fillets, so the widest one reaches a little under R.
    assert 2 * R - 0.1 < max(bb.size.X, bb.size.Y) <= 2 * R + 1e-3, f"knob OD wrong: {bb.size}"

    # Bore: one cylinder of the right radius whose axis is the Z axis.
    bores = [f for f in cylinders(part) if abs(f.radius - k["bore_r"]) < 1e-6]
    assert bores, "no bore cylinder"
    for f in bores:
        axis = f.axis_of_rotation
        assert abs(abs(axis.direction.Z) - 1) < 1e-6, "bore not vertical"
        assert abs(axis.position.X) < 1e-6 and abs(axis.position.Y) < 1e-6, "bore off the axis"

    # Probe the bore all round at mid-depth: hollow inside, solid outside, flat on +X.
    r, z = k["bore_r"], k["bore_end"] + k["bore_depth"] / 2
    flat_x = k["flat_x"]
    for deg in range(0, 360, 15):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if flat_x is not None and (r + EPS) * c > flat_x - EPS:
            continue  # Cut off by the flat, probed below.
        assert not solid_at(part, (r - EPS) * c, (r - EPS) * s, z), f"bore too small at {deg} deg"
        assert solid_at(part, (r + EPS) * c, (r + EPS) * s, z), f"bore too large at {deg} deg"
    if flat_x is not None:
        assert not solid_at(part, flat_x - EPS, 0, z), "flat too deep"
        assert solid_at(part, flat_x + EPS, 0, z), "flat missing"
        width = flat_x + r
        assert abs(width - (p.SHAFT_FLAT + p.SHAFT_TOLERANCE)) < 1e-6, f"flat at {width:.2f}"

    # Depth: hollow just above the bore end, solid just below (the cap).
    assert not solid_at(part, 0, 0, k["bore_end"] + EPS), "bore too short"
    assert solid_at(part, 0, 0, k["bore_end"] - EPS), "bore too deep"
    assert k["bore_end"] >= p.MIN_WALL, "cap thinner than MIN_WALL"
    assert abs(k["bore_depth"] - (p.SHAFT_FREE_LENGTH - p.KNOB_SHAFT_GAP)) < 1e-6, "bore depth wrong"

    # Recess: hollow just inside its radius, solid just outside, open at Z=H.
    zr = H - k["recess_depth"] / 2
    for deg in range(0, 360, 30):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        rr = k["recess_r"]
        assert not solid_at(part, (rr - EPS) * c, (rr - EPS) * s, zr), "recess too small"
        assert solid_at(part, (rr + EPS) * c, (rr + EPS) * s, zr), "recess too large"
    assert k["recess_r"] > p.ENCODER_NUT_AF / math.sqrt(3), "recess does not clear the nut corners"
    assert not solid_at(part, k["recess_r"] - EPS, 0, k["recess_top"] + EPS), "recess too shallow"
    assert solid_at(part, k["recess_r"] - EPS, 0, k["recess_top"] - EPS), "recess too deep"

    # Ridges: a groove centre is hollow halfway down the groove, the land between two is solid.
    zm = H / 2
    half = math.pi / p.KNOB_RIDGES
    assert not solid_at(part, R - p.KNOB_RIDGE_DEPTH / 2, 0, zm), "groove missing"
    assert solid_at(part, (R - EPS) * math.cos(half), (R - EPS) * math.sin(half), zm), "ridge missing"
    # Top chamfer: the rim corner on the bed (Z=0) is cut away.
    edge = p.KNOB_TOP_CHAMFER / 2
    assert not solid_at(part, (R - edge) * math.cos(half), (R - edge) * math.sin(half), edge / 2), "no chamfer"
    print(
        f"knob {kind}: OK  bore d={2 * r:.2f}"
        + (f" flat {flat_x + r:.2f}" if flat_x is not None else "")
        + f" depth {k['bore_depth']:.1f}  recess d={2 * k['recess_r']:.1f} x {k['recess_depth']:.1f}"
        f"  cap {k['bore_end']:.1f}  vol {part.volume:.0f} mm3"
    )


def check_coupon(od: float) -> None:
    p.BARREL_OD = od
    part = build.fit_coupon()
    k = build.coupon_layout()
    assert part.is_valid and len(part.solids()) == 1, "coupon is not one valid solid"
    radii = sorted(
        round(f.radius * 2, 3)
        for f in cylinders(part)
        if abs(f.axis_of_rotation.direction.Z) > 0.99
        and abs(f.radius - p.EDGE_FILLET) > 1e-6
        and abs(f.center().Y - k["bore_y"]) < 1e-3
    )
    want = sorted(round(od + o, 3) for o in p.COUPON_BORE_OFFSETS)
    assert radii == want, f"coupon bores {radii} != {want}"
    sockets = sorted(
        round(f.radius * 2, 3)
        for f in cylinders(part)
        if abs(f.axis_of_rotation.direction.Y) > 0.99
    )
    want_s = sorted(round(p.IR_LED_DIAMETER + o, 3) for o in p.COUPON_SOCKET_OFFSETS)
    assert sockets == want_s, f"coupon sockets {sockets} != {want_s}"

    # Knob bores: one row of D-flats, one of round ones, each through the thicker strip.
    def row(y: float) -> list:
        return sorted(
            round(f.radius * 2, 3)
            for f in cylinders(part)
            if abs(f.axis_of_rotation.direction.Z) > 0.99 and abs(f.axis_of_rotation.position.Y - y) < 1e-3
        )

    guides = row(k["guide_y"])
    want_g = sorted(round(p.BB_GUIDE_D + o, 3) for o in p.COUPON_GUIDE_OFFSETS)
    assert guides == want_g, f"coupon BB guide bores {guides} != {want_g}"
    dflat, press = row(k["dflat_y"]), row(k["press_y"])
    want_d = sorted(round(p.SHAFT_D + o, 3) for o in p.COUPON_SHAFT_OFFSETS)
    want_p = sorted(round(p.SHAFT_D + o, 3) for o in p.COUPON_PRESS_OFFSETS)
    assert dflat == want_d, f"coupon D-flat bores {dflat} != {want_d}"
    assert press == want_p, f"coupon round bores {press} != {want_p}"
    z = p.COUPON_KNOB_THICKNESS / 2
    for i, o in enumerate(p.COUPON_SHAFT_OFFSETS):
        x = -k["width"] / 2 + k["width"] / len(p.COUPON_SHAFT_OFFSETS) * (i + 0.5)
        r = (p.SHAFT_D + o) / 2
        flat_x = x - r + p.SHAFT_FLAT + o
        assert not solid_at(part, flat_x - EPS, k["dflat_y"], z), f"D-flat {o} flat too deep"
        assert solid_at(part, flat_x + EPS, k["dflat_y"], z), f"D-flat {o} flat missing"
        assert not solid_at(part, x - r + EPS, k["dflat_y"], z), f"D-flat {o} too small"
        assert solid_at(part, x - r - EPS, k["dflat_y"], z), f"D-flat {o} too large"
    bb = part.bounding_box()
    assert abs(bb.max.Z - max(p.COUPON_KNOB_THICKNESS, p.IR_LED_DIAMETER + max(p.COUPON_SOCKET_OFFSETS) + 2 * p.MIN_WALL)) < 1e-6
    print(
        f"BARREL_OD {od}: coupon OK  bores {radii}  guides {guides}  sockets {sockets}  "
        f"D-flats {dflat}  round {press}"
    )


# --- Interior: ramp and battery tray (#52) -------------------------------------


def top_hit(part, x: float, y: float, z: float = 200.0):
    """First surface met by a BB falling at (x, y): (z, normal), or None."""
    hits = [h for h in part.find_intersection_points(Axis((x, y, z), (0, 0, -1))) if h[0].Z <= z]  # The axis is infinite.
    if not hits:
        return None
    point, normal = max(hits, key=lambda h: h[0].Z)
    return point.Z, normal


def overlap(a, b) -> float:
    """Volume shared by two solids."""
    common = a & b
    return sum(s.volume for s in common.solids()) if common.solids() else 0.0


def keep_out(ranges) -> object:
    (x0, x1), (y0, y1), (z0, z1) = ranges
    return build.box(x0, x1, y0, y1, z0, z1)


def wall_with_fillet(z: float, side: int) -> float:
    """Usable X at height z next to a wall, with the floor fillet modelled as a quarter ellipse."""
    w, h = p.FLOOR_FILLET_W, p.FLOOR_FILLET_H
    inset = 0.0
    if z < h:
        inset = w - w * math.sqrt(max(0.0, 1 - ((h - z) / h) ** 2))
    return build.wall_x(z, side) - side * inset


def check_battery(name: str, x0: float, y0: float, size: tuple, ramp, tray) -> None:
    length, width, height = size
    z0 = p.TRAY_FLOOR_Z
    env = build.box(x0, x0 + width, y0, y0 + length, z0, z0 + height)
    for part, what in ((ramp, "ramp"), (tray, "tray")):
        assert overlap(env, part) < 1e-3, f"{name} battery hits the {what}"
    assert overlap(env, keep_out(p.SERVO_KEEPOUT)) < 1e-3, f"{name} battery hits the servo"
    assert y0 + length < p.MECH_Y0, f"{name} battery hits the mechanism"
    for z in (z0, z0 + height):
        assert x0 >= wall_with_fillet(z, -1) and x0 + width <= wall_with_fillet(z, 1), f"{name} battery hits a wall at z={z:.1f}"


def check_interior() -> None:
    ramp, a, b, tray = build.ramp(), build.ramp_a(), build.ramp_b(), build.battery_tray()
    for part, name in ((ramp, "ramp"), (a, "ramp_a"), (b, "ramp_b"), (tray, "battery_tray")):
        assert part.is_valid, f"{name} is not a valid solid"
        assert len(part.solids()) == 1, f"{name} has {len(part.solids())} solids"
    assert 5.0 <= p.RAMP_SLOPE <= 6.0, "RAMP_SLOPE out of the 5-6 deg range"
    assert 10.0 <= p.FUNNEL_SLOPE <= 12.0, "FUNNEL_SLOPE out of the 10-12 deg range"
    assert p.IN_DRAIN_SLOPE >= 15.0, "IN drain under 15 deg"

    # Exit: the top is at INLET_Z at INLET_Y right across the inlet, and the sheet ends there.
    for x in (p.INLET_X0 + 0.5, (p.INLET_X0 + p.INLET_X1) / 2, p.INLET_X1 - 0.5):
        z, _ = top_hit(ramp, x, p.INLET_Y - 0.05, p.INLET_Z + 5)  # Under the wing.
        assert abs(z - p.INLET_Z) < 0.2, f"exit top at {z:.2f}, not {p.INLET_Z}, x={x}"
        assert not solid_at(ramp, x, p.INLET_Y + 0.1, p.INLET_Z - 1), "ramp goes past INLET_Y"
    assert p.MECH_FACE_Y - p.INLET_Y < p.BB_MIN_D / 4, "gap between ramp end and mechanism face could catch a BB"

    # Slopes, measured on the solid.
    z1, _ = top_hit(ramp, 45, -180)
    z2, _ = top_hit(ramp, 45, -110)
    main = math.degrees(math.atan((z1 - z2) / 70))
    assert abs(main - p.RAMP_SLOPE) < 0.1, f"main slope {main:.2f} deg"
    yf = -20.0
    f = (yf - (p.RAMP_FRONT_Y - p.FUNNEL_LENGTH)) / p.FUNNEL_LENGTH
    za, _ = top_hit(ramp, 10, yf)
    zb, _ = top_hit(ramp, 20, yf)
    cross = math.degrees(math.atan((za - zb) / 10))
    want = math.degrees(math.atan(f * math.tan(math.radians(p.FUNNEL_SLOPE))))
    assert abs(cross - want) < 0.1, f"funnel slope {cross:.2f} deg at y={yf}, want {want:.2f}"

    # Sheet thickness, probed through the sheet.
    tz = build.ramp_thickness_z()
    for x, y in ((10, -150), (45, -60), (75, -170), (45, 3)):
        z = build.ramp_top(x, y)
        assert solid_at(ramp, x, y, z - 0.2) and solid_at(ramp, x, y, z - tz + 0.2), f"sheet too thin at {x},{y}"
        assert not solid_at(ramp, x, y, z + 0.2), f"something on the sheet at {x},{y}"
    for t, name in ((p.RAMP_T, "RAMP_T"), (p.RIB_T, "RIB_T"), (p.WING_T, "WING_T"), (p.FRONT_T, "FRONT_T"),
                    (p.LEG_T, "LEG_T"), (p.TRAY_FLOOR_T, "TRAY_FLOOR_T"), (p.TRAY_LIP_T, "TRAY_LIP_T"),
                    (p.IN_DRAIN_WEB, "IN_DRAIN_WEB"), (p.CHUTE_WALL, "CHUTE_WALL")):
        assert t >= p.MIN_WALL, f"{name} {t} under MIN_WALL"

    # BB traps. Every column a BB can fall down, from the far end to behind the IN drain, lands on
    # the ramp (no hole to the battery), and on a slope: the only flat is the wing top over the
    # mechanism, under the plate.
    flats, n = [], 0
    y = p.BOX_Y0 + p.RAMP_END_CLEARANCE + 1.5
    while y < p.IN_DRAIN_BACK_Y - 1:
        x = build.wall_x(p.INLET_Z, -1) + p.RAMP_WALL_CLEARANCE + 1.5
        while x < build.wall_x(p.INLET_Z, 1) - p.RAMP_WALL_CLEARANCE - 1.5:
            in_pass = x < p.WIRE_PASS_X1 + 1 and y > p.WIRE_PASS_Y0 - 1
            in_out = math.hypot(x - p.OUT_X, y - p.OUT_Y) < p.OUT_HOLE_D / 2 + 1
            if not (in_pass or in_out):
                hit = top_hit(ramp, x, y, p.PLATE_Z - 0.1 if y > p.PLATE_Y0 else p.BOX_H)
                assert hit is not None, f"BB falls through the ramp at x={x:.1f} y={y:.1f}"
                z, normal = hit
                tilt = math.degrees(math.acos(min(1.0, abs(normal.Z))))
                on_wing = z > p.MECH_TOP_Z + p.WING_T - 0.01 and build.front_y_left() <= y and x <= p.MECH_X1 + p.MECH_CLEARANCE  # Behind the lip.
                no_room = y > p.PLATE_Y0 and p.PLATE_Z - z < p.BB_MIN_D  # Under the plate, too low for a BB.
                if tilt < p.RAMP_SLOPE - 0.2 and not (on_wing or no_room):
                    flats.append((round(x, 1), round(y, 1), round(z, 1)))
                n += 1
            x += 3.0
        y += 3.0
    assert not flats, f"flat spots a BB could rest on: {flats[:10]}"
    for gap, what in ((p.RAMP_WALL_CLEARANCE, "wall gap"), (p.MECH_CLEARANCE, "mechanism gap"),
                      ((p.OUT_HOLE_D - p.BARREL_OD) / 2, "gap round the OUT barrel")):
        assert gap < p.BB_MIN_D / 4, f"{what} {gap} could catch a BB"
    in_clear = p.PLATE_Z - build.drain_top(p.IN_Y)
    back_gap = p.PLATE_Z - build.drain_top(p.IN_DRAIN_BACK_Y)
    assert in_clear >= p.BB_D + 1, f"only {in_clear:.1f} under the IN barrel"
    assert back_gap < p.BB_MIN_D, f"a BB can get behind the IN drain ({back_gap:.1f} mm)"
    z, _ = top_hit(ramp, p.IN_X + 2, p.IN_Y)
    assert abs(z - build.drain_top(p.IN_Y)) < 0.05, "IN drain not under the IN barrel"

    # Interfaces: nothing in the mechanism (the wings rest on its top), the servo, the wire chases,
    # the plate and what hangs under it, or the walls.
    mech = build.box(p.MECH_X0, p.MECH_X1, p.MECH_FACE_Y, p.MECH_Y1, 0, p.MECH_TOP_Z - 0.01)
    mech += build.box(p.MECH_X0, p.MECH_X1, p.MECH_Y0, p.MECH_FACE_Y, 0, p.MECH_STEP_Z)
    drain_under = build.drain_top(p.MECH_Y0) - p.RAMP_T / math.cos(math.radians(p.IN_DRAIN_SLOPE)) - 0.01
    (cx0, cx1), (cy0, cy1), (cz0, cz1) = p.CHASE_RIGHT
    zones = {
        "mechanism": mech,
        "servo": keep_out(p.SERVO_KEEPOUT),
        "left chase": keep_out(p.CHASE_LEFT),
        "right chase under the IN drain": build.box(cx0, cx1, cy0, cy1, cz0, min(cz1, drain_under)),
        "right chase behind the IN drain": build.box(cx0 + p.MECH_CLEARANCE, cx1, p.IN_DRAIN_BACK_Y + 0.3, cy1, cz0, p.PLATE_Z),
        "plate": build.box(-50, 130, -50, 50, p.PLATE_Z, 120),
        "plate boss": keep_out(p.PLATE_BOSS),
    }
    for name, zone in zones.items():
        for part, pname in ((ramp, "ramp"), (tray, "tray")):
            assert overlap(part, zone) < 1e-3, f"{pname} intrudes into the {name}"
    wall_room = build.interior(p.RAMP_WALL_CLEARANCE - 0.05, p.RAMP_END_CLEARANCE - 0.05)
    assert (ramp - wall_room).volume < 1e-3, "ramp closer to the walls than RAMP_WALL_CLEARANCE"
    assert (tray - build.interior(p.TRAY_WALL_CLEARANCE - 0.05)).volume < 1e-3, "tray too close to the walls"
    assert p.MECH_TOP_Z + p.WING_T < p.PLATE_BOSS[2][0], "wing hits what hangs under the plate"
    pass_w = p.WIRE_PASS_X1 - (build.wall_x(p.MECH_TOP_Z, -1) + p.RAMP_WALL_CLEARANCE)
    pass_l = p.WING_Y1 - p.WIRE_PASS_Y0
    assert pass_w >= p.WIRE_PASS_MIN[0] and pass_l >= p.WIRE_PASS_MIN[1], f"wire pass {pass_w:.1f} x {pass_l:.1f}"
    assert not solid_at(ramp, -8, 20, p.MECH_TOP_Z + 1), "wire pass at (-8, 20) closed"
    assert not solid_at(ramp, p.OUT_X + p.OUT_HOLE_D / 2 - 0.1, p.OUT_Y, p.MECH_TOP_Z + 1), "OUT hole too small"
    assert solid_at(ramp, p.OUT_X + p.OUT_HOLE_D / 2 + 0.3, p.OUT_Y, p.MECH_TOP_Z + 1), "OUT hole too large"
    for x in (10, 40, 65):
        assert solid_at(ramp, x, 20, p.MECH_TOP_Z + 0.2), f"wing missing over the mechanism at x={x}"

    # Battery bay: clear height everywhere over the bay, and the three pack shapes.
    bay = build.box(*p.BAY_X, *p.BAY_Y, p.TRAY_FLOOR_Z, p.TRAY_FLOOR_Z + p.BAY_HEIGHT) & build.interior(0)
    assert overlap(bay, ramp) < 1e-3, f"ramp comes lower than {p.BAY_HEIGHT} mm over the bay"
    lane = build.box(p.SERVO_KEEPOUT[0][1], p.LANE_X[1], *p.LANE_Y, p.TRAY_FLOOR_Z, p.TRAY_FLOOR_Z + 22) & build.interior(0)
    assert overlap(lane, ramp) + overlap(lane, keep_out(p.SERVO_KEEPOUT)) < 1e-3, "lane under 22 mm"
    stick_x = p.SERVO_KEEPOUT[0][1] + 0.2
    check_battery("stick", stick_x, p.LANE_Y[1] - 1.5 - p.BATTERY_STICK[0], p.BATTERY_STICK, ramp, tray)
    check_battery("brick", 4.0, -190.0, p.BATTERY_BRICK, ramp, tray)
    check_battery("nunchuck", 5.0, -175.0, p.BATTERY_NUNCHUCK, ramp, tray)
    # Strap slots: open where they should be, floor round them.
    zf = (p.TRAY_RUNNER_H + p.TRAY_FLOOR_Z) / 2
    stations = build.strap_stations()
    assert len(stations) >= 3
    ys = sorted(y for y, _ in stations[:2])
    assert abs(ys[1] - ys[0] - p.STRAP_PITCH) < 1e-6
    for y, x in stations:
        assert not solid_at(tray, x, y, zf), f"strap slot missing at {x},{y}"
        assert solid_at(tray, x - p.STRAP_SLOT[0] / 2 - 0.5, y, zf), f"no floor left of the slot at {x},{y}"
        assert not solid_at(tray, (p.STRAP_X_RIGHT + p.BAY_X[1]) / 2, y, zf), f"right strap notch missing at y={y}"
        for dy in (-p.STRAP_SLOT[1] / 2 - 1, 0, p.STRAP_SLOT[1] / 2 + 1):
            assert not solid_at(tray, (x + p.STRAP_X_RIGHT) / 2, y + dy * 0.9, p.TRAY_RUNNER_H / 2), "runner in the strap's way"
    assert p.STRAP_SLOT[1] >= p.STRAP_W + 1 and p.STRAP_SLOT[0] >= 3.0, "strap slot too small"

    # Split joint.
    assert overlap(a, b) < 1e-3, "ramp_a and ramp_b overlap"
    k = build.joint_layout()
    assert p.JOINT_BAND_T - p.SPLIT_SCREW_LEN - 0.5 >= p.MIN_WALL, "screw tip too close to the top"
    assert p.JOINT_BAND_T - p.JOINT_DEPTH >= p.MIN_WALL + 1, "band under the pocket too thin"
    plane = build.split_plane()
    for x in p.SPLIT_SCREW_XS:
        assert k["x0"] + 4 < x < k["x1"] - 4, f"split screw at {x} outside the tongue"
        assert all(abs(x - r) > p.RIB_T / 2 + p.M3_NUT_AF for r in p.RIB_XS), f"split screw at {x} on a rib"
        under = plane.from_local_coords((x + p.M3_CLEARANCE, k["screw_y"], -p.JOINT_BAND_T + 0.3))  # Beside the hole.
        assert solid_at(b, under.X, under.Y, under.Z), f"band does not reach the screw head at x={x}"
        hole = plane.from_local_coords((x, k["screw_y"], -p.JOINT_BAND_T + 1))
        assert not solid_at(b, hole.X, hole.Y, hole.Z), f"no screw hole in ramp_b at x={x}"
        nut = plane.from_local_coords((x, k["screw_y"], -p.JOINT_DEPTH + 1))
        assert not solid_at(a, nut.X, nut.Y, nut.Z), f"no nut trap in the tongue at x={x}"
        top = plane.from_local_coords((x, k["screw_y"], -0.5))
        assert solid_at(a, top.X, top.Y, top.Z), f"screw breaks through the top at x={x}"
    end = plane.from_local_coords((0, p.JOINT_LAP + p.JOINT_DEPTH, 0))
    assert end.Y < p.RAMP_FRONT_Y - p.FUNNEL_LENGTH, "tongue reaches into the funnel (ramp_a top no longer flat)"

    # Print: each piece fits the bed in its print orientation, and sits on a broad face.
    pieces = {
        "ramp_a": build.print_pose(a, 180 + p.RAMP_SLOPE),
        "ramp_b": build.print_pose(b, 90 + p.RAMP_SLOPE),
        "battery_tray": tray,
    }
    for name, part in pieces.items():
        bb = part.bounding_box()
        assert bb.size.X <= p.PRINT_BED and bb.size.Y <= p.PRINT_BED, f"{name} does not fit the bed: {bb.size}"
        assert bb.size.Z <= p.PRINT_HEIGHT, f"{name} too tall: {bb.size.Z:.0f}"
        assert abs(bb.min.Z) < 1e-6, f"{name} not on the bed"
        bed = sum(f.area for f in part.faces() if f.bounding_box().max.Z < 1e-3)
        assert bed > 300, f"{name} has only {bed:.0f} mm2 on the bed"
        print(f"  {name}: {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm, {bed:.0f} mm2 on the bed")
    zs = [f.bounding_box().max.Z for f in pieces["ramp_a"].faces() if f.area > 5000]
    assert any(z < 1e-3 for z in zs), "ramp_a top face is not on the bed"
    print(f"interior OK  slope {main:.2f} deg  funnel {cross:.2f} deg at y={yf:.0f}  exit z={p.INLET_Z}  "
          f"{n} BB columns probed  IN clearance {in_clear:.1f}  bay {p.BAY_HEIGHT:.0f} mm")


if __name__ == "__main__":
    original = p.BARREL_OD
    for od in BARREL_ODS:
        check_collar(od)
        check_coupon(od)
    p.BARREL_OD = original
    bore = p.KNOB_BORE
    for kind in ("dflat", "round"):
        check_knob(kind)
    p.KNOB_BORE = bore
    check_interior()
    print("all checks passed")
