#!/usr/bin/env python3
"""Embed the simplified APCO plan data into animation-lite.html (works from file://, no fetch).

Reads site.json, zones.json and striping.json (NOT patches.json), rounds every coordinate to
0.5 ft, drops near-collinear points on the curved islands/landscape, and rewrites the contents of
    <script type="application/json" id="lite-data">...</script>
in animation-lite.html.

Run:  python3 embed_lite.py        (safe to run repeatedly; output is identical each time)
"""
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "animation-lite.html"
TAG = "lite-data"


def load(name):
    return json.loads((HERE / name).read_text())


def num(v):
    r = round(v * 2) / 2
    if r == 0:
        r = 0.0  # no "-0"
    return int(r) if r == int(r) else r


def pt(p):
    return [num(p[0]), num(p[1])]


def dedupe(ring):
    out = []
    for p in ring:
        if not out or out[-1] != p:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    idx, dmax = 0, -1
    for i in range(1, len(pts) - 1):
        d = seg_dist(pts[i], a, b)
        if d > dmax:
            idx, dmax = i, d
    if dmax <= eps:
        return [a, b]
    return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)


def simplify_ring(ring, eps):
    """Douglas-Peucker on a closed ring (split at the point farthest from vertex 0)."""
    if len(ring) < 8:
        return ring
    far = max(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - ring[0][0], ring[i][1] - ring[0][1]))
    c1 = ring[: far + 1]
    c2 = ring[far:] + [ring[0]]
    return rdp(c1, eps)[:-1] + rdp(c2, eps)[:-1]


def poly(ring, eps=0.0):
    ring = [list(p) for p in ring]
    if eps:
        ring = simplify_ring(ring, eps)
    ring = dedupe([pt(p) for p in ring])
    return ring


def build():
    site = load("site.json")
    zones = load("zones.json")
    st = load("striping.json")

    zs = []
    for z in sorted(zones, key=lambda z: -z["sf"]):
        zs.append(
            {
                "l": z["label"],
                "c": z["count"],
                "s": z["sf"],
                "p": [poly(p) for p in z["polys"]],
                "a": pt(z["anchor"]),
            }
        )

    def line(l):
        return [pt(l[0]), pt(l[1])]

    return {
        "theta": round(site["theta_deg"], 1),
        "prop": poly(site["property"]),
        "bld": poly(site["building"]),
        "can": poly(site["canopy"]),
        "enc": poly(site["enclosure"]),
        "walks": [poly(p) for p in site["walks"]],
        "isl": [poly(p, 0.6) for p in site["islands"]],
        "land": [poly(p, 0.6) for p in site["landscape"]],
        "zones": zs,
        "str": {
            "stall": [line(l) for l in st["stall_lines"]],
            "div": [line(l) for l in st["dividers"]],
            "dash": [line(l) for l in st["dashed"]],
            "ada": {
                "sp": [[line(l) for l in pair] for pair in st["ada"]["spaces"]],
                "ai": [poly(p) for p in st["ada"]["aisles"]],
            },
            "cw": poly(st["crosswalk"]),
            "np": [poly(p) for p in st["no_parking"]],
        },
    }


def main():
    if not PAGE.exists():
        sys.exit("missing %s" % PAGE.name)
    data = build()
    text = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = PAGE.read_text()
    pattern = re.compile(r'(<script type="application/json" id="%s">)(.*?)(</script>)' % re.escape(TAG), re.S)
    if not pattern.search(html):
        sys.exit('missing <script type="application/json" id="%s"> block in %s' % (TAG, PAGE.name))
    html = pattern.sub(lambda m: m.group(1) + text + m.group(3), html, count=1)
    PAGE.write_text(html)
    print("embedded %d bytes of plan data into %s (%d bytes total)" % (len(text), PAGE.name, len(html.encode())))


if __name__ == "__main__":
    main()
