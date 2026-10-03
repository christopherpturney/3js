"""Extract exact plan outlines from the SketchUp STL export into plan.json.

The SketchUp model is a flat (z=0) plan drawn in feet. SketchUp writes each
face's triangles consecutively, so runs of edge-connected triangles recover
the original faces. Faces are then classified (lawn, stone, mulch, ...) and
merged with shapely. Output coordinates stay in feet, plan X/Y.

Usage: python extract.py   (needs numpy + shapely)
"""
import json, struct
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

HERE = Path(__file__).parent
data = (HERE / "source/backyard.stl").read_bytes()
n = struct.unpack("<I", data[80:84])[0]
recs = [struct.unpack("<12fH", data[84 + 50 * i: 134 + 50 * i]) for i in range(n)]
norms = np.array([r[0:3] for r in recs])
tris = np.array([np.array(r[3:12]).reshape(3, 3) for r in recs])

# The scale figure ("Ty") is the only non-flat geometry; drop it.
flat = tris[:, :, 2].max(1) < 0.01

def key(v): return (round(v[0], 4), round(v[1], 4))

faces, cur, curv = [], [], set()
for i in np.where(flat)[0]:
    vs = {key(v) for v in tris[i]}
    if cur and len(vs & curv) >= 2 and np.sign(norms[i, 2]) == np.sign(norms[cur[-1], 2]):
        cur.append(i); curv |= vs
    else:
        if cur: faces.append(cur)
        cur, curv = [i], set(vs)
faces.append(cur)

def poly(face):
    return unary_union([Polygon(tris[i][:, :2]).buffer(1e-6) for i in face]).buffer(-1e-6)

polys = [poly(f) for f in faces]

# Face classification, read off the SketchUp scene thumbnail (materials don't survive STL).
LAWN = [24]
STONE = [27, 28, 29, 30, 31, 33, 34, 76]       # "Pavers Stone Walk"
MULCH = [5, 6, 7, 8, 26, 35, 36, 37, 38, 39]
CONCRETE = [25]                                  # "Polished Concrete"
ROOF = [44]                                      # "Roofing Shingles Multi"
STEPS = [0, 2, 1]                                # east deck stair treads, top to bottom
SHRUBS = list(range(9, 23))                      # 14 junipers
TREES = [3, 4]                                   # bark-textured circles at the yard edge
DECK = [i for i, p in enumerate(polys)
        if i >= 40 and i not in ROOF and p.area > 0.05 and p.centroid.x < 12.5 and p.centroid.y < 14.1]

def circle(i):
    b = polys[i].bounds
    return {"x": round((b[0] + b[2]) / 2, 4), "y": round((b[1] + b[3]) / 2, 4),
            "r": round(((b[2] - b[0]) + (b[3] - b[1])) / 4, 4)}

def rings(geom):
    geom = geom.simplify(0.002)
    out = []
    for p in getattr(geom, "geoms", [geom]):
        if p.area < 0.05: continue
        out.append({"outer": [[round(x, 4), round(y, 4)] for x, y in p.exterior.coords[:-1]],
                    "holes": [[[round(x, 4), round(y, 4)] for x, y in h.coords[:-1]]
                              for h in p.interiors if Polygon(h).area > 0.05]})
    return out

def merged(ids, extra=()):
    return unary_union([polys[i].buffer(0.003) for i in list(ids) + list(extra)]).buffer(-0.003)

plan = {
    "units": "ft",
    "source": "Backyard (New).skp via SketchUp for Web STL export",
    "lawn": rings(merged(LAWN)),
    "stone": rings(merged(STONE)),
    "mulch": rings(merged(MULCH, SHRUBS)),     # shrubs sit in the beds
    "concrete": rings(merged(CONCRETE)),
    "roof": rings(merged(ROOF)),
    "deck": rings(merged(DECK)),
    "deckPieces": [r for i in DECK for r in rings(polys[i])],
    "steps": [r for i in STEPS for r in rings(polys[i])],
    "shrubs": [circle(i) for i in SHRUBS],
    "trees": [circle(i) for i in TREES],
}
allg = unary_union([polys[i] for i in LAWN + STONE + MULCH + CONCRETE + ROOF + DECK + STEPS + SHRUBS])
plan["bounds"] = [round(v, 4) for v in allg.bounds]
(HERE / "plan.json").write_text(json.dumps(plan, separators=(",", ":")))

# Embed the same data in every page (index.html, civil.html) so the page works from any server or preview (no fetch).
import re
for page in sorted(HERE.glob("*.html")):
    html = page.read_text()
    if 'id="plan-data"' not in html: continue
    blob = json.dumps(plan, separators=(",", ":"))
    html, n = re.subn(r'(<script type="application/json" id="plan-data">).*?(</script>)',
                      lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    assert n == 1, f"plan-data block not found in {page.name}"
    page.write_text(html)

# Dimension readback
def bb(g):
    b = g.bounds; return f"{b[2]-b[0]:.2f} x {b[3]-b[1]:.2f} ft"
print("site extents ", bb(allg))
for k, ids in [("lawn", LAWN), ("stone", STONE), ("mulch", MULCH + SHRUBS), ("concrete", CONCRETE),
               ("roof", ROOF), ("deck", DECK), ("steps", STEPS)]:
    g = merged(ids)
    print(f"{k:9s} area {g.area:8.1f} sq ft   bbox {bb(g)}")
print("deck pieces", len(plan["deckPieces"]))
print("steps", [bb(polys[i]) for i in STEPS])
print("shrubs", len(plan["shrubs"]), "dia", sorted({round(2 * s['r'], 2) for s in plan["shrubs"]}))
print("trees", plan["trees"])
