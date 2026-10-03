"""Existing striping, read row by row off the high-res aerial (source/measurements/22-hires-aerial.webp).

Each stall row is a set of evenly spaced stall lines plus an optional centre divider.
Plan feet, same frame as site.json. Output: striping.json. The aerial predates the
Wawa construction, so the 2025 layout may differ slightly; treat it as the restripe basis.
"""
import json, math
from pathlib import Path

HERE = Path(__file__).parent

def row(x0, x1, ys, ang=0.0, pivot=None):
    """Stall lines from x0 to x1 at each y, rotated by ang degrees about pivot (x, y)."""
    out = []
    for y in ys:
        pts = [[x0, y], [x1, y]]
        if ang:
            px, py = pivot; a = math.radians(ang); c, s = math.cos(a), math.sin(a)
            pts = [[px + (x - px) * c - (yy - py) * s, py + (x - px) * s + (yy - py) * c] for x, yy in pts]
        out.append([[round(v, 2) for v in p] for p in pts])
    return out

def steps(start, step, n):
    return [round(start - step * k, 2) for k in range(n)]

W_ANG, W_PIV = -2.4, (-132.5, -35)            # west lot rows lean with the west line
lines, dividers, dashed = [], [], []
# north lot
lines += row(-130, -114, steps(173.75, 9.95, 9))                    # A: east side of the west island
lines += row(-85, -49, steps(175, 10, 9));  dividers.append([[-67.5, 184], [-67.5, 95]])     # B
lines += row(-19, 20, steps(177.5, 10, 9)); dividers.append([[-1.25, 180], [-1.25, 97.5]])   # C
lines += row(47.5, 64, steps(175, 8.75, 10))                        # D: west side of the NE median
# west lot double row (dashed centre line), split by the ADA crosswalk
lines += row(-150, -114, steps(39, 10, 7), W_ANG, W_PIV)
lines += row(-150, -114, steps(-56, 10, 7), W_ANG, W_PIV)
dashed.append(row(-132.5, -132.5, [0], 0)[0] and [[-129, 47], [-136, -118]])
# building-side row: short beside the west walk, full depth south of the building
lines += row(-92.5, -80, steps(-47.5, 8.8, 4))
lines += row(-92.5, -56, steps(-82.7, 8.8, 5)); dividers.append([[-73, -84], [-73, -118]])
# south lot, east of the transformer pad
lines += row(-28, 7, [-91, -100]); dividers.append([[-12.5, -84], [-12.5, -108]])
# SE lot
lines += row(55, 75, [-47.5]) + row(40, 75, steps(-56, 8.1, 5)); dividers.append([[57.5, -47.5], [57.5, -95]])
# plaza stalls (north-south lines)
lines += [[[53.75, 1], [53.75, -18]], [[62.5, 1], [62.5, -18]]]

ada = {
    # west lot: two spaces each side of the hatched crosswalk, which doubles as the access aisle
    "spaces": [row(-150, -132.5, [-21, -29], W_ANG, W_PIV), row(-132.5, -114, [-21, -29], W_ANG, W_PIV),
               row(-150, -132.5, [-35, -44], W_ANG, W_PIV), row(-132.5, -114, [-35, -44], W_ANG, W_PIV),
               [[[47.5, 105], [64, 105]], [[47.5, 96.25], [64, 96.25]]]],          # NE median van space
    "aisles": [[[50, 87], [64, 87], [64, 96.25], [50, 96.25]]],
}
crosswalk = [[-150, -29.3], [-88, -28.2], [-88, -34], [-150, -35.1]]    # hatched, west lot to the entrance tower
no_park = [[[40, -47.5], [55, -47.5], [40, -58]]]                       # hatched triangle, SE lot

out = {"stall_lines": lines, "dividers": dividers, "dashed": dashed, "ada": ada, "crosswalk": crosswalk,
       "no_parking": no_park, "line_width_in": 4, "source": "high-res aerial 22, read by row"}
(HERE / "striping.json").write_text(json.dumps(out, indent=1))
print(len(lines), "stall lines,", len(dividers), "dividers")
