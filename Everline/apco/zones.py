"""Group the 35 repairs into work zones for the simplified animation (zones.json).

Each zone is drawn as a soft cloud around its repairs instead of exact rectangles,
because the repair positions are approximate. Uses patches-placed.json if present.
"""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, MultiPoint
from shapely.ops import unary_union

HERE = Path(__file__).parent
patches = json.loads((HERE / "patches.json").read_text())["patches"]
for cand in [HERE / "patches-placed.json", Path.home() / "Downloads" / "patches-placed.json"]:
    if cand.exists():
        saved = {q["name"]: q for q in json.loads(cand.read_text())["patches"]}
        for q in patches: q.update({k: saved[q["name"]][k] for k in ("xy", "rot", "status") if q["name"] in saved and k in saved[q["name"]]})
        break

def rect(q):
    a = math.radians(q["rot"]); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    x, y = q["xy"]; hl, hw = q["l"] / 2, q["w"] / 2
    return Polygon([(x + s * hl * ux + t * hw * vx, y + s * hl * uy + t * hw * vy) for s, t in [(-1, -1), (1, -1), (1, 1), (-1, 1)]])

LABEL = {"Entrance": "Main entrance", "Back drive lane": "East drive lane", "Drive through": "Drive-thru",
         "Back entrance": "Municipal Dr entrance", "Long drive lane": "West drive aisle",
         "Near back door": "East door", "Parking area front": "Front parking"}
site = json.loads((HERE / "site.json").read_text())
LOT = Polygon(site["property"]).difference(unary_union([Polygon(site["building"])] + [Polygon(w) for w in site["walks"]] +
      [Polygon(l) for l in site["landscape"]])).buffer(0)
zones = {}
for q in patches: zones.setdefault(q["zone"], []).append(q)
out = []
for z, qs in zones.items():
    shape = unary_union([rect(q).buffer(7, join_style=2) for q in qs])
    hull = MultiPoint([c for q in qs for c in rect(q).exterior.coords]).convex_hull.buffer(7)
    # long, thin zones follow the lane; compact zones use the hull
    g = hull if hull.area < 3.2 * shape.area or len(qs) < 3 else shape.buffer(4).buffer(-2)
    g = g.intersection(LOT).simplify(1.0)               # keep zones on the pavement
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    c = g.representative_point()
    out.append({"zone": z, "label": LABEL.get(z, z), "count": len(qs), "sf": round(sum(q["area"] for q in qs)),
                "polys": [[[round(x, 1), round(y, 1)] for x, y in p.exterior.coords[:-1]] for p in polys],
                "anchor": [round(c.x, 1), round(c.y, 1)],
                "draft": any(q.get("status") == "draft" for q in qs)})
out.sort(key=lambda o: -o["sf"])
(HERE / "zones.json").write_text(json.dumps(out, indent=1))
for o in out: print(f'{o["label"]:24s} {o["count"]:3d} areas {o["sf"]:4d} SF  polys {len(o["polys"])}')
print("total", sum(o["sf"] for o in out), "SF")
