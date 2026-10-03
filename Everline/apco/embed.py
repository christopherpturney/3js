#!/usr/bin/env python3
"""Embed the APCO plan data into animation.html (no fetch needed; works from file:// or a server).

Reads site.json, patches.json (+ patches-placed.json overrides by name) and striping.json, then
replaces the contents of the three <script type="application/json"> blocks in animation.html:
    id="site-data", id="patches-data", id="striping-data"

Run:  python3 embed.py        (safe to run repeatedly)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "animation.html"


def load(name):
    return json.loads((HERE / name).read_text())


def merged_patches():
    data = load("patches.json")
    placed_path = HERE / "patches-placed.json"
    if placed_path.exists():
        placed = json.loads(placed_path.read_text())
        rows = placed["patches"] if isinstance(placed, dict) else placed
        by_name = {r["name"]: r for r in rows}
        for p in data["patches"]:
            o = by_name.get(p["name"])
            if o:
                for k in ("xy", "rot", "status"):
                    if k in o:
                        p[k] = o[k]
    return data


def block(tag_id, payload):
    # compact JSON; "</" is escaped so the payload can never close the script element early
    text = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    return tag_id, text


def main():
    html = PAGE.read_text()
    for tag_id, text in (
        block("site-data", load("site.json")),
        block("patches-data", merged_patches()),
        block("striping-data", load("striping.json")),
    ):
        pattern = re.compile(
            r'(<script type="application/json" id="%s">)(.*?)(</script>)' % re.escape(tag_id), re.S
        )
        if not pattern.search(html):
            sys.exit("missing <script type=\"application/json\" id=\"%s\"> block in animation.html" % tag_id)
        html = pattern.sub(lambda m, t=text: m.group(1) + t + m.group(3), html, count=1)
    PAGE.write_text(html)
    print("embedded site, patches (%d), striping into %s" % (len(merged_patches()["patches"]), PAGE.name))


if __name__ == "__main__":
    main()
