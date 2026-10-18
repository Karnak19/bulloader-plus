# CAD

Parts for BULLOADER+, written in [build123d](https://github.com/gumyr/build123d). Every dimension
lives in `params.py`; `build.py` only describes shapes.

## Build

```sh
cd cad
uv run python build.py
```

uv fetches Python 3.12 and build123d on the first run (build123d does not support older Pythons).
Each part is written to `out/<name>.stl` (for slicing) and `out/<name>.step` (for other CAD tools).
`out/` is gitignored.

To add a part: write a function in `build.py` that returns a shape, then add one line to `PARTS`.

To check the IR collar and the coupon over the whole plausible barrel range (8.5, 9.0 and 9.5 mm),
and the encoder knob with both bore types:

```sh
uv run python check.py
```

On the collar it probes both grip bores, the clamp slots (and that they stop at the ring), the
ring's two shoulders and its BB guide, both sockets, their shoulders and the window, the walls
around them, the screws and the wire grooves, and fails if the sockets are not on one line
`BEAM_OFFSET` off the axis. On the knob it probes the bore (size, flat, depth, on the
axis), the recess, the ridges and the top chamfer.

On the interior (ramp and tray) it checks the ramp exit height and position, both slopes measured
on the solid, the sheet thickness, that nothing enters the mechanism, the servo, the wire chases,
the plate or the walls, that a BB dropped anywhere lands on a slope, the three battery shapes, the
strap slots, the split joint and its screws, and that every piece fits `PRINT_BED`.

## Parts

| Part           | What it is                                                                  |
| -------------- | --------------------------------------------------------------------------- |
| `fit_coupon`   | Print this first. Test bores and sockets at several tolerances, labelled.   |
| `ir_collar`    | Joins the two halves of the cut barrel and holds the IR LED and phototransistor. |
| `encoder_knob` | Big ridged knob for the KY-040 encoder, to turn with gloves on.             |
| `ramp_a`       | Far half of the new BB ramp, with its leg on the floor (#52).               |
| `ramp_b`       | Near half of the ramp: funnel, chute into the mechanism, wings, IN drain.   |
| `battery_tray` | Floor tray under the ramp for any 2S airsoft LiPo, held by a velcro strap.  |
| `test_ring`    | M0 smoke test of the build pipeline.                                        |

### `fit_coupon`

A plate with four barrel bores (`BARREL_OD` −0.2, 0, +0.2, +0.4), three BB guide bores
(`BB_GUIDE_D` −0.1, 0, +0.1), a rib with three horizontal
sockets (`IR_LED_DIAMETER` +0, +0.1, +0.2), and a thicker strip with the encoder shaft bores: three
D-flats (`SHAFT_D` and `SHAFT_FLAT` +0.1, +0.2, +0.3) and four round ones (`SHAFT_D` −0.2, −0.1,
0, +0.1). Each hole has its offset engraved next to it. Print it the same way and in the same
filament as the collar and the knob, then:

- slide it on the barrel: the label of the bore that slides on without play is your `FIT_TOLERANCE`;
- drop a BB through the BB guide bores: it must fall freely through the one marked 0. If it only
  goes through +.1, add 0.1 to `BB_GUIDE_D`;
- push the LED and the phototransistor in: the label of the socket that holds them straight without
  forcing is your `SOCKET_TOLERANCE`;
- D-flat shaft: push it into the D-flat row. The label of the one that goes on by hand without
  wobble is your `SHAFT_TOLERANCE`;
- knurled shaft: push it into the round row. The label of the tightest one that still goes on is
  your `KNOB_PRESS_FIT`, and set `KNOB_BORE = "round"`.

The sockets are horizontal on purpose: they are horizontal in the collar too, and a printer makes
horizontal holes a little smaller than vertical ones.

### `ir_collar`

The output inner barrel is metal, so infrared can't get through it. Rather than drilling it, you
cut it in two and the collar joins the halves: a sleeve, with a grip bore for one half at each end
and a printed ring in the middle. The beam crosses that ring, so there is nothing to drill.

- **Grip bores.** `BARREL_OD + FIT_TOLERANCE`, `GRIP_LENGTH` (10 mm) long at each end. That's over
  one barrel diameter, so each half sits straight, and it leaves room for the nut trap with
  `MIN_WALL` to the end.
- **Ring.** Between the grips, `BARREL_GAP` (6.5 mm) long. Its two faces are the shoulders both
  halves butt against, so the gap and the alignment come from the print, not from how far you
  push. Its bore is the BB guide, `BB_GUIDE_D` (6.2 mm): a bit over the 6.05 mm barrel bore, so a
  hole printed slightly small still never pinches a 5.95 to 6 mm BB. Both guide edges have a 45°
  chamfer (`RING_CHAMFER`), which also shortens the overhang under the ring when printing. 6.5 mm
  is what it takes to hold the 3.2 mm sockets with `SOCKET_WALL` above and below, so no socket
  breaks into a grip bore; that leaves 2 mm of ring above and below the window.
- **Clamps.** One C-clamp per half: a slot along each grip on +Y, two ears, an M3 × 10 screw (head
  on the LED side) and its nut pressed into a hexagonal trap. The slots stop at the ring, so the
  ring stays a closed circle: tightening the screws squeezes the barrel halves, never the BB guide.
  A single slot over the whole length would close the guide too, and one screw in the middle would
  not hold two separate tubes. One piece rather than two shells, because both sockets are then
  printed in the same layers and stay coaxial whatever the screws do. The nut traps have a corner
  on top, so they print without support.
- **Sockets.** The LED goes in from the outside on one side, the phototransistor on the other, both
  in the ring. Each stops on a flat shoulder at the same distance from the BB guide, with a small
  window (`APERTURE_D`) between the shoulder and the guide. The window narrows the beam: a thin
  beam sees the gap between two touching BBs better (see #12) and lets in less stray light. Set
  `APERTURE_W` wider than `APERTURE_D` to get a horizontal slit with more light but the same
  sharpness along the tube.
- **Beam off the axis.** The beam does not cross the tube through its centre but `BEAM_OFFSET`
  (2 mm) to the side, on the opposite side from the clamp slots. The BBs travel touching each
  other, and where two touch, the centre line is still solid, so a beam through the axis never sees
  light. Off the axis it sees the gap between two balls: with a 1.5 mm window, about 83 % of the
  light passes at 2 mm, against 4 % on the axis. The window must stay inside the BB guide
  (`BEAM_OFFSET + APERTURE_W / 2` under `BB_GUIDE_D / 2`), which `check.py` checks.
- **Light shield.** The sockets are closed all round, the leads come out at the back, and the beam
  crosses inside the ring, with the barrel halves pushed in on both sides: no light gets to the
  phototransistor except down the bore.
- **Wires.** Each pair of leads bends down at the back of its socket into a groove that runs to the
  bottom end of the collar. The grooves keep `MIN_WALL` to the grip bore (on a thick barrel the
  sockets move out a little to keep it).

Overall, at `BARREL_OD` 8.55: about 15.5 × 20.6 mm across and 26.5 mm long. Where the collar goes
on the barrel comes from #12.

**Cutting the barrel.** Remove `BARREL_GAP` (6.5 mm) of tube in total, where the collar will sit:
two cuts 6.5 mm apart, or one cut then trim one half by 6.5 mm. The collar puts that gap back, so
the reassembled barrel keeps its original length. Cut square, with a tube cutter if you have one
(else a hacksaw in a mitre box). Deburr inside and out, and put a light chamfer on the **inner**
edge of both cut ends (a deburring tool, or a countersink bit turned by hand): BBs come out of the
6.2 mm guide into the 6.05 mm barrel, and the chamfer keeps them from catching on that step. Blow
the chips out, push each half in until it stops on the ring, and tighten both screws.

**Before printing:**

1. Measure `BARREL_OD` with calipers, and the bodies of the two components (`IR_LED_DIAMETER`,
   `PHOTOTRANSISTOR_DIAMETER`, `IR_BODY_LENGTH`).
2. Print `fit_coupon`, set `FIT_TOLERANCE` and `SOCKET_TOLERANCE`, and check a BB drops freely
   through the BB guide hole marked 0.
3. Run `uv run python check.py`, then `uv run python build.py`.

**Printing:** stand the collar on its flat end face (Z = 0, the end the wire grooves open onto).
No supports. Use a **dark, opaque filament** (black PETG or PLA): white or light colours let infrared
through the walls and can blind the phototransistor in sunlight. For extra shading, slide black
heat-shrink over the back of the phototransistor and its leads.

### `encoder_knob`

A 24 mm knob, 15 mm tall, for the KY-040's bare 6 mm shaft. It is turned with gloves on, so it is
big and has 18 rounded grooves, 1.2 mm deep, round its side: deep enough to feel through a glove,
with rounded edges so they do not dig in. The top edge has a 1.2 mm chamfer.

- **Bore.** D-flat by default (`KNOB_BORE = "dflat"`): `SHAFT_D` and `SHAFT_FLAT`, both plus
  `SHAFT_TOLERANCE`. Many KY-040s have an 18-tooth knurled shaft instead: set `KNOB_BORE = "round"`
  for a plain round bore `KNOB_PRESS_FIT` under size, pressed on. A small lead-in chamfer helps find
  the shaft.
- **Depth.** The bore is `KNOB_SHAFT_GAP` (1 mm) shorter than the free shaft, so when it is pushed
  fully down the shaft tip touches the bore end, and the knob never bottoms on the nut.
- **Recess.** Underneath, a round recess clears the nut corners (`ENCODER_NUT_AF`). Pushed fully
  down, the skirt sits `KNOB_PANEL_GAP` (1 mm) above the panel, so it never rubs.
- **Panel cutout (#18).** Leave at least `KNOB_OD` / 2 plus a finger's room around the encoder hole.

**Printing:** top face down on the bed (the STL is already that way up). The recess and the bore
both open upward, so every layer sits on the one below; the only slope is the 45° top chamfer at the
bed, which also hides elephant's foot. No supports. Any filament; four perimeters make the ridges
solid.

### Interior: `ramp_a`, `ramp_b` and `battery_tray` (#52)

A new interior for the Plano box, drawn from scratch. It keeps the original mechanism and plate,
and only reuses where they are (heights, positions, clearances), measured on the original
assembly. Every number is in the "Interior" part of `params.py`.

**Ramp.** One sloped sheet from the far end of the box to the mechanism inlet.

- **Slope.** `RAMP_SLOPE` 5.5° toward the mechanism (the original had 4.8°). The top ends at Z 56
  at Y 7.7, right across the 31 mm inlet, 0.3 mm short of the mechanism face.
- **Funnel.** Over the last `FUNNEL_LENGTH` (60 mm) the sheet also tilts sideways toward the inlet,
  up to `FUNNEL_SLOPE` (11°), so BBs along the walls are not stranded. Over that length the
  centre band gets steeper (about 13.5°): without it, the sides, lifted as the sideways tilt
  grows, would be almost flat about 30 mm from each wall. With it, every point of the sheet,
  up to the walls, still falls at 5.5° or more.
- **Front walls and chute.** Either side of the inlet, a wall at 45° rises from the sheet to the
  wings. A BB that reaches it rolls back down and along it into a 31 mm chute that leads into
  the inlet. Left of the mechanism the wall sits further forward, so it stays out of the wire
  chase.
- **Wings.** They rest on the mechanism top (Z 73 to 75), with a 10 mm hole for the OUT barrel and
  an open notch at the back left (about 18 × 15 mm) for wires and plugs coming up the left chase.
  A lip on their front edge leans forward at 45° up to 1 mm under the plate. With a full box the
  pile reaches the plate, and without the lip a layer of BBs would be pushed over the wings and
  stay there. Over the mechanism there is nothing else, so the room under the plate stays free for
  the electronics (phase 2).
- **IN drain.** BBs poured through the IN barrel fall right of the mechanism. They land on a sheet
  at 15° that runs from behind the IN axis down into the main sheet, 7.5 mm below the plate under
  the barrel. At its back edge the gap to the plate is under one BB, so none gets behind it. It
  roofs the front of the right wire chase from Z 67 up: wires go up that chase behind the drain
  (Y 27 to 32), or below Z 67.
- **No BB traps.** `check.py` drops a BB every 3 mm over the whole box and checks it lands on the
  ramp and on a slope. The only flat place is the wing top, closed off by the lip. Every gap is
  under 1.5 mm: 1 mm to the walls, 0.5 mm at the far end, 0.3 mm at the mechanism.
- **Support.** A leg across the far end stands on the floor, clear of the floor fillet, and four
  ribs run under the sheet. Their bottom is flat 50 mm above the tray floor, and they are never
  deeper than 14 mm.

**Split.** The ramp is 232 mm long and has walls on both faces near the mechanism, so it is
printed in two pieces, split 95 mm in front of the mechanism, square to the sheet. `ramp_a` has a
tongue (6 mm thick, flush with the top) that slides into a pocket in a thickened band of
`ramp_b`. The pocket's sides line it up across, its floor in height, its 45° end along the ramp.
Three M3 × 6 screws go up from under the band into M3 nuts pressed into the tongue. Sand the seam
on the top if it catches a fingernail going toward the mechanism.

**Battery tray.** A floor that stands on cross runners 2.5 mm tall, so a velcro strap passes under
it. Its top is at Z 4.5. It has:

- the main bay (about 90 × 166 mm, with 50 mm clear above);
- a lane beside the servo (X 62 to 82, 22 mm tall and more), so a 185 mm stick goes in along the
  right wall, past the servo;
- a strip along the left wall for the battery lead, out to the left wire chase;
- low lips at the back and front of the bay;
- three strap stations, two in the bay 120 mm apart and one in the lane. Each has a slot on the
  left and a notch open to the right wall: a 20 mm strap goes down the slot, under the floor, up
  the notch, then over the battery.

`check.py` fits a 185 × 20 × 20 stick (lane and bay), a 140 × 48 × 30 brick and a
115 × 34 × 10 nunchuck. The battery stays in the box: it charges in place through the XT30 and
the balance port on the plate remix (#18).

**Printing.** No supports for any of them.

- `ramp_a` (about 103 × 130 × 85 mm): the STL is already the right way up, top face (the BB
  surface) on the bed, so it comes out smooth. The leg and ribs point up.
- `ramp_b` (102 × 30 × 124 mm): standing on its split face, the STL is already that way up. It is
  tall and its base is small (about 400 mm²): use a brim (8 mm) and a slow first layer. Every
  slope on it is 45° or steeper.
- `battery_tray` (97 × 198 × 11 mm): as it sits, runners on the bed. The floor bridges about
  17 mm between runners, and about 37 mm where a strap passes.

PETG is best for the ramp: PLA can creep in a hot car with 3 to 4 kg of BBs on it. Every piece
fits a 220 × 220 bed (`PRINT_BED`); `check.py` checks it.

**Assembly.**

1. Put the tray on the box floor, runners down, its back against the far end.
2. Thread a strap through each station you need, lay the battery in, lead toward the front left,
   and tighten the strap. Run the lead along the left strip, then up the left chase to the plate.
3. Screw `ramp_a` and `ramp_b` together (three M3 × 6 and nuts), then lower the ramp in: the leg
   behind the tray, the wings on the mechanism top, the OUT barrel through its hole.
4. Put the plate back on.

**Needs a real-world test.** Do BBs keep rolling at 5.5° when the box is half empty, and none stay
stuck in the funnel near the walls? Does the IN drain take BBs away without a jam (we do not
know how far the IN barrel sticks out under the plate)? Does the strap hold with the notch
against the wall? Does the long thin `ramp_a` warp on the bed (use a brim if its corners lift)?

## License rule

The original BULLOADER is under the MakerWorld Exclusive License. Its files go in `original/`, and
the remixed control panel goes in `remix/`. Both folders are gitignored: **never commit them**, not
even exported STL/STEP of the remix. Parts designed from scratch here (IR collar, electronics
cradle, encoder knob) are fine to commit.

## Still to measure

Placeholders marked `TODO: measure` in `params.py`:

- `BARREL_OD`: outer diameter of the 120 mm inner barrel (8.55 mm on a standard AEG barrel;
  `check.py` covers 8.5 to 9.5).
- `IR_LED_DIAMETER`: body of the IR LED (nominal 3.0 mm).
- `PHOTOTRANSISTOR_DIAMETER`: body of the phototransistor (nominal 3.0 mm).
- `IR_BODY_LENGTH`: straight body of each component, from the start of the dome to the flange
  (about 4 mm). `SOCKET_DEPTH` must stay below it, so the flange never hits the back before the
  front reaches the shoulder.

For the encoder knob, with calipers on the encoder fitted to the panel. The defaults are the
common EC11 datasheet values (Alps EC11 and its clones, the encoder on most KY-040 boards):

- `SHAFT_D`: shaft diameter (6.0 mm). On a knurled shaft, measure over the teeth.
- `SHAFT_FLAT`: on a D-flat shaft, from the flat to the opposite side (4.5 mm on EC11).
- `ENCODER_TOP_HEIGHT`: height above the panel of the highest fixed part, the nut and washer or
  the bushing tip if it sticks out past the nut (about 2 mm).
- `SHAFT_FREE_LENGTH`: shaft length above that highest fixed part (about 12 to 15 mm). If it is
  longer than the knob can take, the build stops and asks for a taller `KNOB_HEIGHT`.
- `ENCODER_NUT_AF`: the hex nut on the M7 bushing, across flats (9 to 10 mm).

And tolerances to calibrate with `fit_coupon`: `FIT_TOLERANCE`, `SOCKET_TOLERANCE`, and either
`SHAFT_TOLERANCE` (D-flat shaft) or `KNOB_PRESS_FIT` (knurled shaft).

The electronics cradle dimensions (perfboard, ESP32, buck) will be added once the parts arrive.
