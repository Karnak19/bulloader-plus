"""Every dimension of the BULLOADER+ parts, in millimetres.

Change values here, never in build.py. Anything marked `TODO: measure` is a
placeholder until the real part is in hand.
"""

# --- Printing ---------------------------------------------------------------
FIT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance added to every hole that fits around a real part.
MIN_WALL = 1.6  # Thinnest wall we print (4 perimeters at 0.4 mm nozzle).
EDGE_FILLET = 0.8  # Rounding of the outer edges along the tube, so nothing is sharp in the hand.

# --- Inner barrel (cut in two, the IR collar joins the halves) ----------------
BARREL_OD = 8.55  # Outer diameter of the 120 mm inner barrel: a standard AEG inner barrel. Confirm with calipers (#16).
BARREL_ID = 6.05  # Bore of that barrel, the usual 6.05 mm AEG bore. The printed BB guide must be wider.

# --- IR barrier ---------------------------------------------------------------
IR_LED_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm IR LED.
PHOTOTRANSISTOR_DIAMETER = 3.0  # TODO: measure. Body of the 3 mm phototransistor.
IR_BODY_LENGTH = 4.0  # TODO: measure. Straight body of each component, from the start of the dome to the flange.

# --- IR collar ----------------------------------------------------------------
# The barrel is cut in two. The collar is a sleeve: each end grips one half, and a
# printed ring between them sets the gap and guides the BBs across it. The beam
# crosses that ring, so nothing is drilled. Printed standing on its end face, tube
# axis vertical: the bores come out round and both sockets are built in the same
# layers, so they stay coaxial.
SOCKET_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance on the 3 mm sockets.
SOCKET_DEPTH = 3.5  # Guide length up to the stop shoulder. Below IR_BODY_LENGTH, so the flange stays outside.
SOCKET_WALL = 1.6  # Wall around each socket.
APERTURE_D = 1.5  # Height of the window between socket and bore, along the tube. Narrower = sharper beam (#12).
APERTURE_W = 1.5  # Width of that window across the tube. Equal to APERTURE_D: round hole; wider: horizontal slit.
APERTURE_LEN = 1.2  # Length of the window, i.e. the thinnest wall between the stop shoulder and the BB guide.
BEAM_OFFSET = 2.0  # Beam moved sideways off the tube axis (#12). BBs travel touching, and where two touch the
# axis is still solid, so a beam through the axis is never let through. Off-axis it sees the gap between two
# balls: about 83 % of the light at 2.0 mm, against 4 % on the axis. Keep it + APERTURE_W / 2 inside BB_GUIDE_D.
BB_GUIDE_D = 6.2  # Bore of the printed ring the BBs cross. Over BARREL_ID, so a hole printed a bit small still
# clears a 5.95-6 mm BB; the step back into the 6.05 barrel is what the chamfer on the cut ends is for.
BARREL_GAP = 6.5  # Ring length = gap between the two barrel halves = tube to remove when cutting. Holds the
# 3.2 mm socket with SOCKET_WALL above and below (6.4), so no socket breaks into a grip bore; that also leaves
# well over MIN_WALL of ring above and below the 1.5 mm window.
GRIP_LENGTH = 10.0  # Bore gripping each barrel half. Over one barrel diameter, so the halves stay coaxial, and
# long enough for the M3 nut trap (6.7 mm tall) with MIN_WALL to the end.
RING_CHAMFER = 0.5  # 45 deg chamfer on both edges of the BB guide. Shortens the overhang under the ring when
# printing, and takes off the edge a BB could catch on.
COLLAR_WALL = 2.0  # Radial wall around the grip bores.
WIRE_CHANNEL_W = 3.4  # Groove for one pair of leads (2.54 mm pitch + wire), from under each socket to the bottom end.
WIRE_CHANNEL_DEPTH = 1.5  # Depth of that groove.
CLAMP_SLOT = 1.5  # Gap of each C-clamp, closed by its M3 screw. Far more than the bore clearance it has to take up.

# --- Hardware ---------------------------------------------------------------
M3_CLEARANCE = 3.4  # Through-hole for an M3 screw.
M3_NUT_AF = 5.5  # M3 hex nut, across flats.
M3_NUT_THICKNESS = 2.4  # M3 hex nut thickness.
NUT_TOLERANCE = 0.3  # Clearance on the nut trap, so the nut presses in by hand.

# --- Rotary encoder (KY-040 module, EC11-type encoder) ----------------------
# Defaults come from the common EC11 datasheet values (Alps EC11 series and its
# clones, the encoder on most KY-040 boards): 6 mm shaft, D-cut flat leaving
# 4.5 mm, M7 x 0.75 bushing with a hex nut, shaft 15-30 mm long from the mounting
# face depending on the version. KY-040 sellers ship both a D-flat and an
# 18-tooth knurled "half shaft", so measure yours.
SHAFT_D = 6.0  # TODO: measure. Outer diameter of the shaft.
SHAFT_FLAT = 4.5  # TODO: measure. Across the D-flat: from the flat to the opposite side (EC11: 4.5).
ENCODER_TOP_HEIGHT = 2.0  # TODO: measure. Highest fixed part (nut + washer, or bushing tip) above the panel.
SHAFT_FREE_LENGTH = 12.0  # TODO: measure. Shaft above that highest fixed thing (nut or bushing tip), expected 12-15.
ENCODER_NUT_AF = 10.0  # TODO: measure. Hex nut on the M7 bushing, across flats (9-10 on KY-040 kits).

# --- Encoder knob -----------------------------------------------------------
# Printed top face down on the bed: the recess and the bore open upward, so no
# overhang at all except the 45 deg chamfer at the bed.
SHAFT_TOLERANCE = 0.2  # TODO: calibrate with fit_coupon. Clearance on the D-flat bore (diameter and flat).
KNOB_BORE = "dflat"  # "dflat" for a D-flat shaft, "round" for a knurled shaft (press fit).
KNOB_PRESS_FIT = -0.1  # TODO: calibrate with fit_coupon. Round bore = SHAFT_D + this; under size so it grips.
KNOB_OD = 24.0  # Outer diameter over the ridges. Also the minimum clearance around the panel hole (#18).
KNOB_HEIGHT = 15.0  # Overall height. Must fit the recess, the bore and a MIN_WALL cap.
KNOB_RIDGES = 18  # Number of grooves round the side.
KNOB_RIDGE_DEPTH = 1.2  # Depth of each groove: deep enough to feel through a glove.
KNOB_RIDGE_WIDTH = 2.8  # Width of each groove at the surface (land between grooves is what is left).
KNOB_RIDGE_FILLET = 0.4  # Rounds the groove edges, so the ridges grip without being sharp.
KNOB_TOP_CHAMFER = 1.2  # 45 deg chamfer on the top edge (prints on the bed, also stops elephant's foot).
KNOB_SHAFT_GAP = 1.0  # Bore depth = SHAFT_FREE_LENGTH - this, so the knob never bottoms on the nut.
KNOB_RECESS_CLEARANCE = 0.8  # Radial clearance around the nut corners in the recess underneath.
KNOB_PANEL_GAP = 1.0  # Gap left between the knob's skirt and the panel when it is pushed fully down.
KNOB_BORE_CHAMFER = 0.5  # Lead-in chamfer at the bore entrance, helps find the shaft.

# --- Fit coupon (print it first, then update the tolerances above) -----------
COUPON_THICKNESS = 3.0  # Plate thickness, i.e. how long the barrel and BB guide test bores are.
COUPON_BORE_OFFSETS = (-0.2, 0.0, 0.2, 0.4)  # Bore = BARREL_OD + offset. The best slide gives FIT_TOLERANCE.
COUPON_GUIDE_OFFSETS = (-0.1, 0.0, 0.1)  # BB guide = BB_GUIDE_D + offset. A BB must drop through the 0 one freely.
COUPON_SOCKET_OFFSETS = (0.0, 0.1, 0.2)  # Socket = IR_LED_DIAMETER + offset. The best hold gives SOCKET_TOLERANCE.
COUPON_SHAFT_OFFSETS = (0.1, 0.2, 0.3)  # D-flat bore = SHAFT_D/SHAFT_FLAT + offset. The best fit gives SHAFT_TOLERANCE.
COUPON_PRESS_OFFSETS = (-0.2, -0.1, 0.0, 0.1)  # Round bore = SHAFT_D + offset. Tightest one that goes on: KNOB_PRESS_FIT.
COUPON_KNOB_THICKNESS = 6.0  # The knob test bores go through a thicker strip, so the grip is felt over some length.
COUPON_GAP = 3.0  # Material between two test holes.
COUPON_TEXT_SIZE = 3.0  # Height of the engraved labels.
COUPON_TEXT_DEPTH = 0.4  # Engraving depth (2 layers at 0.2).

# --- Smoke-test ring (M0 only, proves the build pipeline) --------------------
RING_WALL = 2.0  # Radial wall thickness of the test ring.
RING_HEIGHT = 5.0  # Height of the test ring along the barrel axis.

# =============================================================================
# Interior: new BB ramp and battery tray (#52)
# =============================================================================
# Frame for everything below: X across the box, Y along it (+Y = mechanism end),
# Z up, box floor at Z = 0. Interface numbers were measured on the original
# assembly (kept locally in cad/original/, never committed); only functional
# dimensions are reused, never shapes.

# --- Printer ------------------------------------------------------------------
PRINT_BED = 220.0  # Square bed size. Every printed piece must fit it in its print orientation.
PRINT_HEIGHT = 200.0  # Usable build height, for the pieces printed standing.

# --- BBs ------------------------------------------------------------------------
BB_D = 6.0  # Nominal BB.
BB_MIN_D = 5.95  # Smallest BB we expect. A gap under this can never let a BB through.

# --- Box: Plano .30 cal ammo can, interior -------------------------------------
BOX_CX = 35.7  # X of the box centre line.
BOX_W0 = 98.5  # Interior width at the floor.
BOX_TAPER = 0.072  # Width gained per mm of height: the side walls lean out about 2.1 deg each.
BOX_Y0 = -203.95  # Far end wall (no floor fillet along it).
BOX_Y1 = 38.13  # Mechanism end wall.
BOX_H = 165.0  # Interior height.
FLOOR_FILLET_W = 4.0  # Fillet between floor and side walls: this wide...
FLOOR_FILLET_H = 10.0  # ...and this tall. Our parts clear its chord, which is outside the real curve.

# --- Original mechanism and plate (stay as they are) ---------------------------
MECH_X0, MECH_X1 = 0.0, 70.0  # Mechanism footprint, standing free on the floor.
MECH_Y0, MECH_Y1 = 0.4, 29.0
MECH_TOP_Z = 73.0  # Its flat top. The ramp's wings rest on it.
MECH_FACE_Y = 8.0  # Its front face, above the servo block...
MECH_STEP_Z = 37.5  # ...whose top is here; in front of the face, under it, the block reaches MECH_Y0.
INLET_X0, INLET_X1 = 29.5, 60.5  # BB inlet notch in the top front, 31 mm wide.
INLET_Y = 7.7  # The ramp delivers here: its end, 0.3 short of the front face...
INLET_Z = 56.0  # ...at this height (top of the ramp), the top of the inlet chute.
OUT_X, OUT_Y = 23.97, 17.12  # OUT barrel axis (bore 8.75 in the mechanism).
IN_X, IN_Y = 70.42, 17.15  # IN barrel axis: BBs poured in drop from the plate here.
PLATE_Z = 81.5  # Underside of the plate...
PLATE_Y0 = -40.87  # ...which covers the box from here to the mechanism end.
PLATE_BOSS = ((-12.3, 4.0), (-0.5, 12.0), (75.5, PLATE_Z))  # Something hangs under the plate here (X, Y, Z ranges).
SERVO_KEEPOUT = ((7.0, 62.0), (-29.0, 3.0), (16.0, 36.0))  # Servo on the mechanism front face, with margin.
CHASE_LEFT = ((-13.6, 0.0), (0.4, 32.0), (0.0, MECH_TOP_Z))  # Wire chase beside the mechanism, kept free.
CHASE_RIGHT = ((70.0, 85.0), (0.4, 32.0), (0.0, MECH_TOP_Z))  # Right chase. Its top front is roofed by the IN drain
# (see below), so wires go up behind it: check.py keeps the whole chase free below the drain and a full-height pass
# behind IN_DRAIN_BACK_Y.

# --- Ramp -----------------------------------------------------------------------
# One sloped sheet from the far end of the box to the mechanism inlet. Over its last
# FUNNEL_LENGTH it also tilts sideways toward the 31 mm inlet, so BBs along the walls
# are not stranded. It stands on a leg at the far end and hangs from wings resting on
# the mechanism top at the near end. Nothing above the sheet is flat: every surface a
# BB can reach falls toward the inlet.
RAMP_SLOPE = 5.5  # Main slope toward the mechanism (deg). The original was 4.8; 5-6 rolls more surely.
FUNNEL_SLOPE = 11.0  # Sideways slope toward the inlet at the end of the funnel (deg).
FUNNEL_LENGTH = 60.0  # The sideways slope grows from 0 to FUNNEL_SLOPE over this length, ending at RAMP_FRONT_Y.
# Over that length the inlet band itself gets steeper (about 13.5 deg), so that the sides, lifted by the growing
# sideways tilt, still fall at RAMP_SLOPE toward the mechanism: no flat strip anywhere (check.py probes it).
RAMP_T = 2.4  # Sheet thickness (6 perimeters).
RAMP_WALL_CLEARANCE = 1.0  # Gap to the box walls: room for the taper and print error, far too small for a BB.
RAMP_END_CLEARANCE = 0.5  # Gap to the far end wall.
MECH_CLEARANCE = 0.3  # Gap to the mechanism faces.
RAMP_FRONT_Y = 0.0  # Top edge of the front walls, where the wings start. Stays in front of the chases (Y 0.4).
FRONT_T = 2.4  # Front walls, 45 deg so they print without support and BBs roll off them.
CHUTE_WALL = 2.0  # Side walls of the 31 mm chute that leads into the inlet.
WING_T = 2.0  # Wings over the mechanism top: Z 73-75, under the plate boss at 75.5.
WING_Y1 = 29.0  # Back edge of the wings (end of the mechanism top).
WING_LIP_GAP = 1.0  # Lip on the wings' front edge, up to this far under the plate: no BB gets over the wings.
OUT_HOLE_D = 10.0  # Hole for the OUT barrel in the wing (original 9.6).
WIRE_PASS_X1 = 3.0  # Wire pass over the left chase: the wing stops left of this X...
WIRE_PASS_Y0 = 14.0  # ...and behind this Y, leaving an open notch for Mini-Tamiya / XT30 plugs.
WIRE_PASS_MIN = (16.0, 12.0)  # Smallest plug outline the pass must clear (X, Y).
IN_DRAIN_SLOPE = 15.0  # Sheet under the IN barrel, falling toward the ramp (deg).
IN_DRAIN_Z = 74.0  # Its top under the IN axis: 7.5 mm below the plate, so BBs drop out freely.
IN_DRAIN_BACK_Y = 27.0  # Its back edge. There the gap to the plate is under BB_MIN_D, so no BB gets behind.
IN_DRAIN_WEB = 2.4  # Web closing the side of the drain, under it, in front of the mechanism.
LEG_T = 3.0  # Leg at the far end, standing on the floor.
RIB_T = 2.4  # Ribs under the sheet, along Y.
RIB_XS = (2.0, 24.0, 46.0, 68.0)  # Rib positions. Their bottom is flat at RIB_BOTTOM_Z (set below the tray)...
RIB_DEPTH = 14.0  # ...but they never go deeper than this under the top surface.

# Split. The ramp is about 232 mm long and has walls on both faces near the mechanism,
# so it is printed in two pieces. ramp_a (far end, with the leg) prints top face down,
# so the BB surface is the smooth bed face. ramp_b (funnel, chute, wings, drain)
# prints standing on its split face. Joint: a tongue on ramp_a, flush with the top,
# slides into a pocket in ramp_b's thickened band; three M3 x 6 screws from below go
# through the band into nuts trapped in the tongue. The pocket's walls locate it
# side to side, its floor in height, its 45 deg end along the ramp.
RAMP_SPLIT_Y = -95.0  # Where the split face crosses the sheet top (the face is square to the sheet).
JOINT_LAP = 15.0  # Tongue length along the sheet, to the start of its 45 deg end.
JOINT_DEPTH = 6.0  # Tongue thickness below the top surface.
JOINT_BAND_T = 9.0  # Sheet thickened to this under the joint, square to the sheet.
JOINT_BAND_LEN = 26.0  # Band length each side of the split.
JOINT_SHOULDER = 6.0  # Band left at each side of the pocket.
JOINT_CLEARANCE = 0.2  # Clearance between tongue and pocket (sides, floor, end).
SPLIT_SCREW_XS = (13.0, 35.0, 57.0)  # Screw positions, between the ribs.
SPLIT_SCREW_LEN = 6.0  # M3 x 6, head under the band.

# --- Battery tray -----------------------------------------------------------------
# A floor tray under the ramp for any 2S airsoft LiPo (stick, brick, nunchuck). It
# stands on cross runners, so a velcro strap passes under it from slot to slot.
TRAY_RUNNER_H = 2.5  # Runners under the floor: the strap's passage.
TRAY_RUNNER_W = 3.0
TRAY_RUNNER_PITCH = 20.0  # Runner spacing, skipped where a strap passes.
TRAY_FLOOR_T = 2.0
TRAY_FLOOR_Z = TRAY_RUNNER_H + TRAY_FLOOR_T  # Top of the floor, where the battery sits.
TRAY_WALL_CLEARANCE = 1.0
BAY_X = (-10.0, 82.0)  # Main bay, clipped to the walls.
BAY_Y = (-198.0, -32.0)
BAY_HEIGHT = 50.0  # Clear height over the floor, up to the ramp's ribs.
LANE_X = (50.0, 82.0)  # Low lane beside the servo, so a 185 mm stick fits. Above the servo's bottom only X > 62.
LANE_Y = (-32.0, 0.0)
LEAD_X = (-10.0, 6.0)  # Strip along the left wall, from the bay to the left chase, for the battery lead.
LEAD_Y = (-32.0, 0.0)
TRAY_LIP_H = 6.0  # Low lips at the back and front of the bay, and the ridge along the lead strip.
TRAY_LIP_T = 2.0
STRAP_W = 20.0  # Velcro strap width.
STRAP_SLOT = (3.5, 22.0)  # Slot across (X) and along (Y).
STRAP_PITCH = 120.0  # The two bay strap stations, centred on the bay.
STRAP_X_LEFT = -3.0  # Left slot of each station (centre).
STRAP_X_RIGHT = 77.0  # Right of this, each station has a notch open to the wall: the strap goes up between battery and wall.
LANE_STRAP_X = 55.0  # Left slot of the lane station (its right side is the same open notch).
LANE_STRAP_Y = -16.0

RIB_BOTTOM_Z = TRAY_FLOOR_Z + BAY_HEIGHT  # Nothing of the ramp goes below this over the bay (except the leg).

# Batteries the bay must take (length, width, height), and where check.py puts them.
BATTERY_STICK = (185.0, 20.0, 20.0)  # Lane + bay, right against the wall, past the servo.
BATTERY_BRICK = (140.0, 48.0, 30.0)
BATTERY_NUNCHUCK = (115.0, 34.0, 10.0)
