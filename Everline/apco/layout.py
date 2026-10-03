"""Draft site layout for APCO, 243 Route 130, Bordentown NJ.

Frame: feet, rotated so the building's west face is vertical ("plan north" = up).
True north is THETA_DEG clockwise... see site_ref.json (theta_deg = rotation applied to
north-up coordinates). Property corners are least-squares fitted to the four
Google Maps measurements (308.00 / 355.65 / 359.64 / 400.36 ft). Everything else is
traced by eye from the scaled aerial and is a DRAFT for field confirmation.
"""
import json
from pathlib import Path
HERE = Path(__file__).parent
import math
def strip(cx, cy, length, width, ang):
    """Rectangle centred at (cx, cy), long axis at `ang` degrees (CCW from plan east)."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    hl, hw = length / 2, width / 2
    return [[round(cx + sx * hl * ux + sy * hw * vx, 2), round(cy + sx * hl * uy + sy * hw * vy, 2)]
            for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]

def fillet(pts, r=2.5, seg=6):
    """Round every corner of a polygon with radius r (clamped to half the shorter edge)."""
    out, n = [], len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1 = (a[0] - b[0], a[1] - b[1]); v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        u1, u2 = (v1[0] / l1, v1[1] / l1), (v2[0] / l2, v2[1] / l2)
        ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        if ang > math.pi * 0.97: out.append(list(b)); continue          # straight: no fillet
        rr = min(r, 0.5 * min(l1, l2) * math.tan(ang / 2))
        d = rr / math.tan(ang / 2)
        p1 = (b[0] + u1[0] * d, b[1] + u1[1] * d); p2 = (b[0] + u2[0] * d, b[1] + u2[1] * d)
        bis = (u1[0] + u2[0], u1[1] + u2[1]); bl = math.hypot(*bis)
        h = rr / math.sin(ang / 2); cx, cy = b[0] + bis[0] / bl * h, b[1] + bis[1] / bl * h
        a1, a2 = math.atan2(p1[1] - cy, p1[0] - cx), math.atan2(p2[1] - cy, p2[0] - cx)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            t = a1 + da * k / seg; out.append([round(cx + rr * math.cos(t), 2), round(cy + rr * math.sin(t), 2)])
    return out

ref = json.loads((HERE / "site_ref.json").read_text())
C = ref["corners"]
NW, NE, SE, SW = C["NW"], C["NE"], C["SE"], C["SW"]

def lerp_y(a, b, x):  # y on line a-b at x
    return a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
def lerp_x(a, b, y):  # x on line a-b at y
    return a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
yN = lambda x: lerp_y(NW, NE, x)    # Route 130 frontage
yS = lambda x: lerp_y(SW, SE, x)    # Municipal Dr frontage
xE = lambda y: lerp_x(NE, SE, y)    # east line (Wawa side)
xW = lambda y: lerp_x(SW, NW, y)    # west line
ec = lambda y: 147.1 + (198.9 - y) * (18.3 / 310.6)   # east planting strip centre line, from markup

site = {
  "property": [NW, NE, SE, SW],
  # Footprint where the walls meet the ground, from the high-res aerial (22). The measured
  # 132.75 ft runs from the north face (y 52.5) to the outer edge of the south walk (y -80.25).
  "building": [[-72, 52.5], [13, 52.5], [13, 73], [36, 73], [36, 68], [75, 68], [75, 21], [40.5, 21], [40.5, -17.5],
               [15, -17.5], [15, -73.5], [-72, -73.5], [-72, -5], [-80, -5], [-80, 20], [-72, 20]],   # incl. west entrance tower
  "canopy": [[74, 48], [122, 48], [122, 75], [74, 75]],
  "walks": [
    # sidewalk wrapping the north, west and south faces (narrows south of the ADA crosswalk)
    [[-89, 57.5], [0, 57.5], [13, 69], [13, 52.5], [-72, 52.5], [-72, 20], [-80, 20], [-80, -5], [-72, -5], [-72, -73.5],
     [15, -73.5], [15, -81], [-80, -81], [-80, -38], [-89, -38]],
    # east entrance plaza: under the east wing, strip to the drive-thru, triangle in the SE inside corner
    [[40.5, 21], [78, 21], [78, -20], [72.5, -20], [72.5, 1], [46, 1], [46, -15], [20, -45], [18, -45], [18, -60], [15, -60],
     [15, -17.5], [40.5, -17.5]],
    [[-29, -81], [-12.5, -81], [-12.5, -89], [-29, -89]],                  # pad south of the building
    [[101, -20.5], [125, -20.5], [125, -39], [101, -39]],                  # dumpster pad
    [[0, 87.5], [7.5, 87.5], [7.5, 98.5], [0, 98.5]],                      # pad beside the NE building island
  ],
  # Revised 2026-10-02 from Chris's markups: 19 (pavement vs planting) and 21 (island outlines).
  # Shapes are drawn clean from the markup's intent, with curb-radius corners.
  # Angles measured island by island from the sharpest aerial (image 1), 2026-10-02.
  # Rows follow their nearest property line, not the building: north rows ~2.2 deg (Route 130),
  # west lot ~-2.3 deg (square to its stall lines), NE median/island lean with the east line.
  "islands": [fillet(p, r) for p, r in [
    # west island (hi-res aerial 22): west curb leans out (9 ft wide at the north, 17 ft at the south),
    # east curb straight at x -131; hook east at the north end, longer foot east at the south end
    ([[-141, 190.5], [-112, 190.5], [-112, 184], [-131.5, 184], [-130.5, 85], [-108, 85], [-108, 77], [-147, 77]], 3),
    # north row-end islands, parallel to Route 130
    (strip(-67, 189, 42, 7, 2.2), 3.5),
    (strip(-2, 190, 40, 7, 2.2), 3.5),
    (strip(51, 189.5, 26, 8, 2.2), 4),
    # islands north of the building
    (strip(-62, 83.5, 46, 7, 5.2), 3.5),
    (strip(2, 89.5, 46, 7, 16.5), 3.5),                  # single diagonal strip (was drawn as a Z)
    # NE median (narrow, leaning with the east line) and NE island
    ([[65.4, 165], [71.4, 165], [77.25, 80], [71.25, 80]], 3),
    ([[101.5, 186], [130, 187.5], [134, 184], [138.5, 124], [134, 120], [116, 120], [108, 127]], 4),
    # west lot islands, square to the west-lot stall lines
    (strip(-127, 51, 26, 6, -2.3), 3),
    (strip(-134, -45.5, 26, 6, -2.3), 3),
    # SW island with a tail angling toward the SW corner (hi-res aerial 22)
    ([[-137, -117], [-112, -117], [-112, -129], [-130, -131], [-157, -137.5], [-158, -134.5], [-137, -127.5]], 3),
    # south of the building
    (strip(-8.75, -111.5, 43, 6, 3.4), 3),
    # east: one island wrapping the dumpster pad (top block, strip along the east drive, SE block)
    ([[91, 4], [130, 9.5], [136, 4], [140, -84], [128, -91.5], [105.5, -94], [105, -72], [126, -69], [126, -21], [91, -20]], 3),
  ]],
  "round_islands": [],
  "enclosure": [[110, -24], [124, -24], [124, -38], [110, -38]],
  "landscape": [
    # Route 130 strip: ~11 ft deep, NW drive to the main entrance
    fillet([[-130, yN(-130)], [45, yN(45)], [45, yN(45) - 11], [-130, yN(-130) - 11]], 4),
    # NE corner: landscape from the main entrance to the property corner, joining the east strip (no NE drive)
    fillet([[70, yN(70)], NE, [max(xE(200), ec(200) + 5), 200], [145.5, 200], [145.5, 209], [78, 209], [70, 215]], 3),
    # east strip along the Wawa line, ~10 ft wide, to the SE entrance
    [[145.5, 200], [max(xE(200), ec(200) + 5), 200], [max(xE(-112), ec(-112) + 5), -112], [161, -112]],   # west curb scanned
    # Municipal Dr strip (markup 21 confirms the paving edge)
    [[SW[0], SW[1]], [130, yS(130)], [130, -115], [SW[0], -152]],   # north curb scanned
    # west strip: grass 5-6 ft inside the west line, NW drive to Municipal Dr (scanned)
    [[xW(214), 214], [-162.6, 214], [-181.5, -150], [xW(-150), -150]],
  ],
  "entrances": {
    "NW drive (Rte 130)": [-165, -130],          # confirmed, street view 02
    "Main entrance (Rte 130)": [45, 70],
    "SE drive (Municipal Dr)": [130, 165],       # confirmed, street view 09; only Municipal Dr access
  },
  "measured_lines": {"bldg_sw_to_sw_corner": [[-72, -80.25], SW], "west_to_east_along_bldg_north": ref["m7"]},
  "dims": {"north": 308.00, "east": 355.65, "south": 359.64, "west": 400.36,
           "bldg_west_face": 132.75, "bldg_sw_to_sw_corner": 149.53, "west_to_east_along_bldg_north": 199.12},
  "theta_deg": ref["theta_deg"],
}
(HERE / "site.json").write_text(json.dumps(site, indent=1))
print("wrote site.json")
