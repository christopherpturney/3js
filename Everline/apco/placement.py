"""Draft positions for the 35 cut & replace repairs, from their names in the proposal.

The proposal photos are close-ups with no surroundings, so locations are inferred from
the area names and marked status "draft" until someone who walked the lot confirms them
in the plan editor (index.html -> Edit repairs -> Save). A saved patches-placed.json
(from ~/Downloads or this folder) always wins over these drafts.

Zones (plan feet, building west face vertical):
  Back drive lane   east drive between the NE/east islands and the Wawa-side strip
  Back entrance     SE entrance throat on Municipal Dr
  Drive through     drive-thru lanes south of the canopy
  Entrance          main entrance off Route 130 and the aisle just inside it
  Long drive lane   west aisle along the west strip (the longest aisle on the lot)
  Near back door    pavement beside the east entrance plaza
  Parking area front  west lot in front of the entrance tower
rot = direction of the patch's long side (l), degrees CCW from plan east.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "patches.json").read_text())

def east_drive_x(y):          # centreline of the east drive
    return 142 + (150 - y) * 0.03

def west_aisle_x(y):          # centreline of the west aisle
    return (-168.5 - (100 - y) * 0.052 + -147) / 2

SPOTS = {
    "Back drive lane":  [(east_drive_x(y), y, 91.5) for y in (182, 152, 124, 98, 70, 44, 16, -14, -44, -78)],
    "Back entrance":    [(139, -101, 90), (147, -109, 0), (139, -116, 0)],
    "Drive through":    [(88, 22, 90), (100, 33, 0), (108, 14, 0), (116, 26, 0)],
    "Entrance":         [(56, 219, 90), (64, 211, 0), (49, 208, 90), (60, 203, 0), (72, 205, 90), (44, 200, 0),
                         (82, 201, 0), (30, 201, 0), (92, 205, 0), (18, 202, 0), (100, 198, 0), (6, 200, 0), (70, 197, 0)],
    "Long drive lane":  [(west_aisle_x(y), y, 92.5) for y in (125, 30, -40)],
    "Near back door":   [(82, -9, 90)],
    "Parking area front": [(-104, 4, 0)],
}

def zone(name):
    if name.startswith("Long drive"): return "Long drive lane"
    return re.sub(r"\s+\d+$", "", name)

def order(name):
    m = re.search(r"(\d+)$", name)
    return int(m.group(1)) if m else 1

used = {}
for p in data["patches"]:
    z = zone(p["name"])
    if z == "Long drive lane":
        k = {"Long drive lane": 0, "Long drive lane 2": 1, "Long drive 3": 2}[p["name"]]
    else:
        k = order(p["name"]) - 1
    x, y, rot = SPOTS[z][k]
    if p["w"] > p["l"]: rot = (rot + 90) % 360    # rot follows l; keep the long side along the lane
    p.update(zone=z, xy=[round(x, 2), round(y, 2)], rot=rot, status="draft")
    used.setdefault(z, []).append(k)

(HERE / "patches.json").write_text(json.dumps(data, indent=1))
print({z: len(v) for z, v in used.items()}, "->", sum(map(len, used.values())), "placed")
