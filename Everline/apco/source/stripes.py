"""Detect existing painted striping on the high-res aerial (source/hires-plan-frame.jpg)."""
import cv2, numpy as np, json, sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
im = cv2.imread('source/hires-plan-frame.jpg'); H, W = im.shape[:2]
K, X0, Y1 = 4, -200, 250
s = json.load(open('site.json'))
block = unary_union([Polygon(p).buffer(1.0) for p in s["islands"] + s["landscape"] + s["walks"] + [s["building"]]])
pave = Polygon(s["property"]).difference(block).buffer(-0.5)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
local = g - cv2.GaussianBlur(g, (0, 0), 6)
white = ((local > 28) & (hsv[..., 1] < 60) & (g > 150)).astype(np.uint8) * 255
mask = np.zeros_like(white)
P = lambda c: np.array([[(x - X0) * K, (Y1 - y) * K] for x, y in c], np.int32)
for gm in getattr(pave, 'geoms', [pave]):
    cv2.fillPoly(mask, [P(gm.exterior.coords)], 255)
    for h in gm.interiors: cv2.fillPoly(mask, [P(h.coords)], 0)
white &= mask
lines = cv2.HoughLinesP(white, 1, np.pi / 360, threshold=18, minLineLength=int(5 * K), maxLineGap=int(1.2 * K))
segs = [[[round(X0 + x1 / K, 2), round(Y1 - y1 / K, 2)], [round(X0 + x2 / K, 2), round(Y1 - y2 / K, 2)]] for x1, y1, x2, y2 in lines.reshape(-1, 4)]
print(len(segs), "segments")
vis = cv2.cvtColor(white, cv2.COLOR_GRAY2BGR) // 3
for a, b in segs:
    cv2.line(vis, tuple(P([a])[0]), tuple(P([b])[0]), (0, 0, 255), 2)
cv2.imwrite(f'{OUT}/stripes_raw.png', cv2.resize(vis, (W // 2, H // 2)))
json.dump(segs, open(f'{OUT}/stripes_raw.json', 'w'))

# ---- regularise: group E-W stall lines into columns, fill a regular spacing ----
import math
cand = []
for a, b in segs:
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx)); ang = ((ang + 90) % 180) - 90
    if 7 <= L <= 24 and abs(ang) < 14:
        x0_, x1_ = sorted([a[0], b[0]]); ym = (a[1] + b[1]) / 2
        cand.append(dict(x0=x0_, x1=x1_, xm=(x0_ + x1_) / 2, y=ym, ang=ang, L=L))
cand.sort(key=lambda c: c["xm"])
cols = []
for c in cand:
    for col in cols:
        if abs(col["xm"] - c["xm"]) < 5 and min(col["x1"], c["x1"]) - max(col["x0"], c["x0"]) > 4:
            col["m"].append(c); n = len(col["m"]); col["xm"] = sum(q["xm"] for q in col["m"]) / n
            col["x0"] = min(col["x0"], c["x0"]); col["x1"] = max(col["x1"], c["x1"]); break
    else:
        cols.append(dict(xm=c["xm"], x0=c["x0"], x1=c["x1"], m=[c]))
rows = []
def runs(m):                     # split a column where stall lines stop for more than 25 ft
    m = sorted(m, key=lambda q: q["y"]); out = [[m[0]]]
    for q in m[1:]:
        (out[-1] if q["y"] - out[-1][-1]["y"] <= 25 else out.append([q]) or out[-1]).append(q) if q["y"] - out[-1][-1]["y"] <= 25 else None
    return out
for col in cols:
    groups, cur = [], []
    for q in sorted(col["m"], key=lambda q: q["y"]):
        if cur and q["y"] - cur[-1]["y"] > 25: groups.append(cur); cur = []
        cur.append(q)
    groups.append(cur)
    for m in groups:
        if len(m) < 3: continue
        ys = sorted({round(q["y"], 1) for q in m}); ys2 = [ys[0]]
        for y in ys[1:]:
            if y - ys2[-1] > 3: ys2.append(y)
        gaps = [b - a for a, b in zip(ys2, ys2[1:])]
        base = sorted(g for g in gaps if 8 <= g <= 11)
        sp = base[len(base) // 2] if base else 9.0
        x0s = sorted(q["x0"] for q in m); x1s = sorted(q["x1"] for q in m)
        xa, xb = x0s[len(x0s) // 4], x1s[3 * len(x1s) // 4]
        angs = sorted(q["ang"] for q in m); ang = angs[len(angs) // 2]
        n = max(1, round((ys2[-1] - ys2[0]) / sp)); sp = (ys2[-1] - ys2[0]) / n
        rows.append(dict(x0=round(xa, 2), x1=round(xb, 2), ang=round(ang, 2), spacing=round(sp, 2),
                         y=[round(ys2[0] + k * sp, 2) for k in range(n + 1)], hits=len(m)))
for r in rows: print(f"x {r['x0']:7.1f}..{r['x1']:7.1f}  ang {r['ang']:5.1f}  sp {r['spacing']:5.2f}  lines {len(r['y']):3d}  y {r['y'][0]:7.1f}..{r['y'][-1]:7.1f}  hits {r['hits']}")
json.dump(rows, open(f'{OUT}/stall_rows.json', 'w'), indent=1)
