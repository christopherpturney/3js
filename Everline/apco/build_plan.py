"""Render site.json + patches.json into index.html: a draft civil site layout sheet.

1 SVG unit = 1 ft. Plan frame is rotated so the building's west face is vertical;
the north arrow shows true north. Run after layout.py:  python build_plan.py
"""
import json, math
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
site = json.loads((HERE / "site.json").read_text())
patches = json.loads((HERE / "patches.json").read_text())
for cand in [HERE / "patches-placed.json", Path.home() / "Downloads" / "patches-placed.json"]:
    if cand.exists():
        saved = {q["name"]: q for q in json.loads(cand.read_text())["patches"]}
        for q in patches["patches"]:
            if q["name"] in saved:
                q.update({k: saved[q["name"]][k] for k in ("xy", "rot", "status") if k in saved[q["name"]]})
        print("using saved placement from", cand)
        break
under = json.loads((HERE / "aerial-underlay.json").read_text())

BX0, BX1, BY0, BY1 = -230, 210, -215, 275          # drawing extents (ft)

def P(p): return f"{p[0]:.2f},{-p[1]:.2f}"
def poly(pts, cls): return f'<polygon class="{cls}" points="{" ".join(P(p) for p in pts)}"/>'

def text_on(a, b, label, off, cls="dimt", size=4.6):
    """Label centred on segment a-b, pushed `off` ft to its left, kept upright."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    x, y = mx + nx * off, my + ny * off
    ang = -math.degrees(math.atan2(dy, dx))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    return (f'<text class="{cls}" x="{x:.2f}" y="{-y:.2f}" font-size="{size}" '
            f'transform="rotate({ang:.2f} {x:.2f} {-y:.2f})" text-anchor="middle" dominant-baseline="middle">{escape(label)}</text>')

def dim_line(a, b, off, label):
    """Dimension: extension lines, dimension line with 45-degree ticks, label."""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L; ux, uy = dx / L, dy / L
    A = (a[0] + nx * off, a[1] + ny * off); B = (b[0] + nx * off, b[1] + ny * off)
    sgn = 1 if off > 0 else -1
    ext = lambda p, q: f'<line class="ext" x1="{p[0] + nx * sgn * 1.5:.2f}" y1="{-(p[1] + ny * sgn * 1.5):.2f}" x2="{q[0] + nx * sgn * 3:.2f}" y2="{-(q[1] + ny * sgn * 3):.2f}"/>'
    tick = lambda p: (f'<line class="dim" x1="{p[0] - (ux + nx) * 1.8:.2f}" y1="{-(p[1] - (uy + ny) * 1.8):.2f}" '
                      f'x2="{p[0] + (ux + nx) * 1.8:.2f}" y2="{-(p[1] + (uy + ny) * 1.8):.2f}"/>')
    return (ext(a, A) + ext(b, B) + f'<line class="dim" x1="{A[0]:.2f}" y1="{-A[1]:.2f}" x2="{B[0]:.2f}" y2="{-B[1]:.2f}"/>'
            + tick(A) + tick(B) + text_on(A, B, label, 3.2 * sgn))

def ftin(v):
    return f"{v:,.2f}'"

g = []
# aerial underlay (hidden by default; toggle in UI)
g.append(f'<image id="aerial" href="aerial-underlay.jpg" x="{under["x0"]}" y="{-under["y1"]}" '
         f'width="{under["x1"] - under["x0"]}" height="{under["y1"] - under["y0"]}" preserveAspectRatio="none" opacity="0"/>')
# pavement = inside property (white); everything else layered on top
g.append(poly(site["property"], "pave"))
for L in site["landscape"]: g.append(poly(L, "land"))
for L in site["islands"]: g.append(poly(L, "land"))
for x, y, r in site["round_islands"]: g.append(f'<circle class="land" cx="{x}" cy="{-y}" r="{r}"/>')
for w in site["walks"]: g.append(poly(w, "walk"))
g.append(poly(site["building"], "bldg"))
g.append(poly(site["canopy"], "canopy"))
g.append(poly(site["enclosure"], "encl"))
g.append(poly(site["property"], "prop"))
g.append('<g id="repairs"></g>')

# property line dimensions (measured)
NW, NE, SE, SW = site["property"]
D = site["dims"]
for a, b, v in [(NW, NE, D["north"]), (NE, SE, D["east"]), (SE, SW, D["south"]), (SW, NW, D["west"])]:
    g.append(text_on(a, b, ftin(v), 6.5, "dimt"))
# building west face
bw = site["building"]
g.append(dim_line((-89, -80.25), (-89, 52.5), 14, ftin(D["bldg_west_face"])))
# measured check lines
for key, val in [("bldg_sw_to_sw_corner", D["bldg_sw_to_sw_corner"]), ("west_to_east_along_bldg_north", D["west_to_east_along_bldg_north"])]:
    a, b = site["measured_lines"][key]
    g.append(f'<line class="meas" x1="{a[0]:.2f}" y1="{-a[1]:.2f}" x2="{b[0]:.2f}" y2="{-b[1]:.2f}"/>')
    g.append(text_on(a, b, f"MEAS. {ftin(val)}", 3.2, "meast", 3.8))

# streets and labels
g.append(text_on(NW, NE, "ROUTE 130", 20, "street", 7))
g.append(text_on(SW, SE, "MUNICIPAL DRIVE", -20, "street", 7))
g.append(f'<text class="lbl" x="-27" y="18" font-size="6" text-anchor="middle">EXISTING BUILDING</text>')
g.append(f'<text class="lbl2" x="100" y="-58" font-size="3.6" text-anchor="middle">CANOPY</text>'.replace('x="100" y="-58"', 'x="100" y="-61.5"'))
for name, (cx, cy) in {"NW DRIVE": (-147, 212), "MAIN ENTRANCE": (57, 222), "SE ENTRANCE": (147, -112)}.items():
    g.append(f'<text class="lbl2" x="{cx}" y="{-cy}" font-size="3.8" text-anchor="middle">{name}</text>')
for lab, (cx, cy) in {"LANDSCAPE": (-40, 222)}.items():
    g.append(f'<text class="lbl3" x="{cx}" y="{-cy}" font-size="3.6" text-anchor="middle">{lab}</text>')

# graphic scale
sx, sy = -215, -205
bar = [f'<rect x="{sx + i * 25}" y="{-sy - 2}" width="25" height="2" class="{"sb1" if i % 2 == 0 else "sb0"}"/>' for i in range(4)]
bar += [f'<text class="dimt" x="{sx + v}" y="{-sy + 5.5}" font-size="3.8" text-anchor="middle">{v}</text>' for v in (0, 50, 100)]
bar.append(f'<text class="dimt" x="{sx + 112}" y="{-sy + 5.5}" font-size="3.8">FT</text>')
g += bar

svg = (f'<svg id="plan" viewBox="{BX0} {-BY1} {BX1 - BX0} {BY1 - BY0}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Draft site layout">'
       '<defs>'
       '<pattern id="h45" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3" stroke="#C9CDD1" stroke-width=".35"/></pattern>'
       '<pattern id="plant" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r=".45" fill="#9AA0A6"/><circle cx="3.7" cy="3.7" r=".45" fill="#9AA0A6"/></pattern>'
       '<pattern id="rep" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1.6" height="1.6" fill="#3A3F45"/><line x1="0" y1="0" x2="0" y2="1.6" stroke="#121417" stroke-width=".7"/></pattern>'
       '</defs>' + "".join(g) + '</svg>')

# repair schedule
rows = "".join(f'<tr data-i="{i}"><td>{i + 1:02d}</td><td>{escape(p["name"])} <span class="st"></span></td><td class="n">{p["w"]:g} × {p["l"]:g}</td><td class="n">{p["area"]:g}</td></tr>'
               for i, p in enumerate(patches["patches"]))
patch_json = json.dumps([{k: q[k] for k in ("name", "w", "l", "area", "zone", "xy", "rot", "status")} for q in patches["patches"]])
theta = site["theta_deg"]    # plan frame = true frame rotated by theta; true north points -theta clockwise on screen

EDITOR_JS = r"""
// ---- repair placement editor ----
const DRAFT = __PATCHES__;
const KEY = 'apco-repairs-v1';
let P = JSON.parse(JSON.stringify(DRAFT));
try { const s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s && s.length === P.length) P = s; } catch (e) {}
const layer = document.getElementById('repairs'), NS = 'http://www.w3.org/2000/svg';
const rowsEl = [...document.querySelectorAll('tbody tr')];
let sel = -1, editing = false;
const corners = (q) => { const a = q.rot * Math.PI / 180, ux = Math.cos(a), uy = Math.sin(a), vx = -uy, vy = ux, hl = q.l / 2, hw = q.w / 2;
  return [[-1,-1],[1,-1],[1,1],[-1,1]].map(([s, t]) => [q.xy[0] + s*hl*ux + t*hw*vx, q.xy[1] + s*hl*uy + t*hw*vy]); };
function draw() {
  layer.innerHTML = '';
  P.forEach((q, i) => {
    const pg = document.createElementNS(NS, 'polygon');
    pg.setAttribute('points', corners(q).map(([x, y]) => `${x.toFixed(2)},${(-y).toFixed(2)}`).join(' '));
    pg.setAttribute('class', 'rep' + (q.status === 'draft' ? ' draft' : '') + (i === sel ? ' sel' : ''));
    pg.dataset.i = i; layer.appendChild(pg);
    const off = Math.max(q.w, q.l) / 2 + 3.2, a = (q.rot + 90) * Math.PI / 180;
    const tx = q.xy[0] + Math.cos(a) * Math.max(q.w / 2 + 3.2, 3.6), ty = q.xy[1] + Math.sin(a) * Math.max(q.w / 2 + 3.2, 3.6);
    const g = document.createElementNS(NS, 'g'); g.setAttribute('class', 'tag' + (i === sel ? ' sel' : '')); g.dataset.i = i;
    g.innerHTML = `<circle cx="${tx.toFixed(2)}" cy="${(-ty).toFixed(2)}" r="2.6"/><text x="${tx.toFixed(2)}" y="${(-ty + 1.05).toFixed(2)}" text-anchor="middle">${i + 1}</text>`;
    layer.appendChild(g);
  });
  rowsEl.forEach((r, i) => { r.classList.toggle('sel', i === sel); r.querySelector('.st').textContent = P[i].status === 'draft' ? 'draft' : ''; });
}
const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(P)); } catch (e) {} };
const select = (i) => { sel = i; draw(); };
const editBtn = document.getElementById('editBtn');
editBtn.addEventListener('click', () => { editing = !editing; editBtn.setAttribute('aria-pressed', editing);
  svg.classList.toggle('editing', editing); document.querySelector('.draw').classList.toggle('editing-on', editing); });
rowsEl.forEach((r, i) => r.addEventListener('click', () => select(i)));
const toPlan = (e) => { const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; const p = pt.matrixTransform(svg.getScreenCTM().inverse()); return [p.x, -p.y]; };
let drag = null;
layer.addEventListener('pointerdown', (e) => {
  const i = +(e.target.closest('[data-i]')?.dataset.i ?? -1); if (i < 0) return;
  select(i); if (!editing) return;
  const p = toPlan(e); drag = { i, dx: P[i].xy[0] - p[0], dy: P[i].xy[1] - p[1] }; svg.setPointerCapture(e.pointerId); e.preventDefault();
});
svg.addEventListener('pointermove', (e) => { if (!drag) return; const p = toPlan(e);
  P[drag.i].xy = [+(p[0] + drag.dx).toFixed(2), +(p[1] + drag.dy).toFixed(2)]; P[drag.i].status = 'placed'; draw(); });
svg.addEventListener('pointerup', () => { if (drag) { drag = null; persist(); } });
const rotate = (d) => { if (sel < 0 || !editing) return; P[sel].rot = (P[sel].rot + d + 360) % 360; P[sel].status = 'placed'; persist(); draw(); };
document.getElementById('rotL').addEventListener('click', () => rotate(15));
document.getElementById('rotR').addEventListener('click', () => rotate(-15));
document.addEventListener('keydown', (e) => { if (e.key === 'r' || e.key === 'R') rotate(e.shiftKey ? 15 : -15);
  if (e.key === '[') rotate(1); if (e.key === ']') rotate(-1); });
document.getElementById('resetBtn').addEventListener('click', () => { if (!confirm('Discard your placements and go back to the drafts?')) return;
  P = JSON.parse(JSON.stringify(DRAFT)); persist(); draw(); });
document.getElementById('saveBtn').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({ source: 'APCO plan editor', saved: new Date().toISOString(), patches: P }, null, 1)], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'patches-placed.json'; a.click();
  document.getElementById('editMsg').textContent = 'Saved patches-placed.json to Downloads.';
});
window.__repairs = () => P;
draw();
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>APCO Site Layout</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;700&family=Overpass+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{ --page:#F6F7F8; --sheet:#FFFFFF; --ink:#121417; --g1:#8A9096; --g2:#C9CDD1; --g3:#EEF0F1; --accent:#F2B705;
  --sans:'Overpass', 'Helvetica Neue', Arial, sans-serif; --mono:'Overpass Mono', ui-monospace, Menlo, monospace; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; background:var(--page); color:var(--ink); font-family:var(--sans); }}
.sheet {{ display:flex; gap:0; margin:16px; background:var(--sheet); border:1px solid var(--ink); min-height:calc(100vh - 32px); }}
.draw {{ flex:1; min-width:0; position:relative; border-right:1px solid var(--ink); }}
#plan {{ display:block; width:100%; height:calc(100vh - 34px); }}
.side {{ width:340px; flex:none; display:flex; flex-direction:column; }}
.blk {{ border-bottom:1px solid var(--ink); padding:10px 12px; }}
.lab {{ font:500 9px/1 var(--mono); letter-spacing:.14em; text-transform:uppercase; color:var(--g1); margin-bottom:5px; }}
.val {{ font:600 14px/1.25 var(--sans); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; }}
.grid2 > div {{ padding:9px 12px; border-bottom:1px solid var(--ink); }}
.grid2 > div:nth-child(odd) {{ border-right:1px solid var(--ink); }}
.draft {{ font:500 10px/1.3 var(--mono); letter-spacing:.1em; text-transform:uppercase; }}
.draft b {{ background:var(--accent); padding:1px 4px; font-weight:500; }}
.tools {{ position:absolute; left:12px; top:12px; display:flex; gap:8px; align-items:center; }}
.btn {{ font:500 10px/1 var(--mono); letter-spacing:.14em; text-transform:uppercase; background:#fff; color:var(--ink);
  border:1px solid var(--ink); border-radius:0; height:26px; padding:0 10px; cursor:pointer; }}
.btn:hover {{ background:var(--g3); }} .btn[aria-pressed="true"] {{ background:var(--accent); }}
input[type=range] {{ width:110px; accent-color:var(--ink); }}
.legend {{ display:grid; grid-template-columns:34px 1fr; gap:6px 10px; align-items:center; font:400 12px/1.2 var(--sans); }}
.legend svg {{ width:34px; height:14px; }}
ol {{ margin:0; padding-left:16px; font:400 11.5px/1.45 var(--sans); }}
table {{ width:100%; border-collapse:collapse; font:400 11px/1.3 var(--sans); }}
th {{ font:500 9px/1 var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--g1); text-align:left; padding:4px 4px; border-bottom:1px solid var(--ink); }}
td {{ padding:3px 4px; border-bottom:1px solid var(--g3); }}
td.n, th.n {{ text-align:right; font-family:var(--mono); white-space:nowrap; }}
td:first-child {{ font-family:var(--mono); color:var(--g1); }}
tfoot td {{ border-top:1px solid var(--ink); border-bottom:0; font-weight:700; }}
.sched {{ overflow:auto; flex:1; }}
.north {{ display:flex; align-items:center; gap:12px; }}
/* plan styles (1 unit = 1 ft) */
.pave {{ fill:#fff; stroke:none; }}
.prop {{ fill:none; stroke:var(--ink); stroke-width:1.6; stroke-dasharray:16 4 3 4; vector-effect:non-scaling-stroke; }}
.bldg {{ fill:url(#h45); stroke:var(--ink); stroke-width:1.8; vector-effect:non-scaling-stroke; }}
.canopy {{ fill:none; stroke:var(--ink); stroke-width:1; stroke-dasharray:6 3; vector-effect:non-scaling-stroke; }}
.walk {{ fill:var(--g3); stroke:var(--g1); stroke-width:.8; vector-effect:non-scaling-stroke; }}
.land {{ fill:url(#plant); stroke:#5F6368; stroke-width:.9; vector-effect:non-scaling-stroke; }}
.encl {{ fill:#fff; stroke:var(--ink); stroke-width:.9; vector-effect:non-scaling-stroke; }}
.dim, .ext {{ stroke:var(--ink); stroke-width:.7; vector-effect:non-scaling-stroke; }}
.ext {{ stroke:var(--g1); }}
.meas {{ stroke:var(--g1); stroke-width:.8; stroke-dasharray:4 3; vector-effect:non-scaling-stroke; }}
.dimt {{ font-family:var(--mono); fill:var(--ink); paint-order:stroke; stroke:#fff; stroke-width:1.4; }}
.meast {{ font-family:var(--mono); fill:var(--g1); paint-order:stroke; stroke:#fff; stroke-width:1.2; }}
.street {{ font-family:var(--sans); font-weight:700; letter-spacing:.25em; fill:var(--g1); }}
.lbl {{ font-family:var(--sans); font-weight:700; letter-spacing:.12em; fill:var(--ink); paint-order:stroke; stroke:#fff; stroke-width:1.2; }}
.lbl2 {{ font-family:var(--mono); letter-spacing:.08em; fill:var(--ink); paint-order:stroke; stroke:#fff; stroke-width:1.2; }}
.lbl3 {{ font-family:var(--mono); letter-spacing:.12em; fill:#5F6368; paint-order:stroke; stroke:#fff; stroke-width:1.2; }}
.aerial-on .pave {{ fill-opacity:0; }} .aerial-on .walk, .aerial-on .encl {{ fill-opacity:.25; }}
.rep {{ fill:url(#rep); stroke:var(--ink); stroke-width:1.1; vector-effect:non-scaling-stroke; }}
.rep.draft {{ stroke-dasharray:3 2; }}
.rep.sel {{ fill:var(--accent); stroke-width:1.8; }}
.tag circle {{ fill:#fff; stroke:var(--ink); stroke-width:.8; vector-effect:non-scaling-stroke; }}
.tag text {{ font-family:var(--mono); font-size:3.1px; fill:var(--ink); }}
.tag.sel circle {{ fill:var(--accent); }}
.tag line {{ stroke:var(--ink); stroke-width:.6; vector-effect:non-scaling-stroke; }}
#plan.editing .rep, #plan.editing .tag {{ cursor:grab; }}
tbody tr {{ cursor:pointer; }} tbody tr.sel td {{ background:#FFF4CC; }}
.st {{ font:500 8.5px/1 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--g1); }}
.edit-bar {{ display:none; gap:6px; align-items:center; font:400 11px/1.3 var(--sans); }}
.editing-on .edit-bar {{ display:flex; flex-wrap:wrap; }}
.sb1 {{ fill:var(--ink); }} .sb0 {{ fill:#fff; stroke:var(--ink); stroke-width:.5; vector-effect:non-scaling-stroke; }}
@media (max-width: 860px) {{
  .sheet {{ flex-direction:column; margin:16px; }}
  .draw {{ border-right:0; border-bottom:1px solid var(--ink); }}
  #plan {{ height:auto; aspect-ratio:{BX1 - BX0}/{BY1 - BY0}; }}
  .side {{ width:auto; }}
  .tools {{ position:static; padding:10px 12px 0; flex-wrap:wrap; }}
}}
</style></head>
<body>
<div class="sheet">
  <div class="draw">
    <div class="tools">
      <button class="btn" id="aerialBtn" aria-pressed="false">Aerial</button>
      <input type="range" id="aerialOp" min="0" max="100" value="55" aria-label="Aerial opacity">
      <button class="btn" id="editBtn" aria-pressed="false">Edit repairs</button>
      <span class="edit-bar">
        <button class="btn" id="rotL" title="Rotate left 15&deg; (Shift+R)">&#8634; 15&deg;</button>
        <button class="btn" id="rotR" title="Rotate right 15&deg; (R)">&#8635; 15&deg;</button>
        <button class="btn" id="saveBtn" title="Download patches-placed.json">Save</button>
        <button class="btn" id="resetBtn" title="Back to the drafted positions">Reset</button>
        <span id="editMsg">Drag a repair to move it. Click a row to find it.</span>
      </span>
    </div>
    {svg}
  </div>
  <aside class="side">
    <div class="blk"><div class="lab">Contractor</div><div class="val">Pavement Pros LLC</div></div>
    <div class="grid2">
      <div><div class="lab">Owner</div><div class="val">APCO</div></div>
      <div><div class="lab">Prepared from</div><div class="val">Owner measurements, aerial</div></div>
      <div><div class="lab">Project</div><div class="val">243 Route 130, Bordentown NJ</div></div>
      <div><div class="lab">Title</div><div class="val">Existing site layout</div></div>
      <div><div class="lab">Date</div><div class="val" style="font-family:var(--mono);font-weight:500">2026-10-02</div></div>
      <div><div class="lab">Scale</div><div class="val" style="font-family:var(--mono);font-weight:500">Graphic</div></div>
    </div>
    <div class="blk draft"><b>Draft</b> &nbsp;For field verification. Not a survey.</div>
    <div class="blk north">
      <svg width="44" height="44" viewBox="-22 -22 44 44" aria-label="North arrow">
        <g transform="rotate({-theta:.2f})"><circle r="19" fill="none" stroke="#121417" stroke-width="1"/>
        <path d="M0,-17 L6,8 L0,3 L-6,8 Z" fill="#121417"/><text y="-6" x="0" font-size="7" text-anchor="middle" fill="#fff" font-family="Overpass" font-weight="700">N</text></g>
      </svg>
      <div style="font:400 11.5px/1.4 var(--sans)">Plan is rotated {abs(theta):.1f}&deg; so the building sits square on the sheet. The arrow shows true north.</div>
    </div>
    <div class="blk">
      <div class="lab">Legend</div>
      <div class="legend">
        <svg viewBox="0 0 34 14"><line x1="1" y1="7" x2="33" y2="7" stroke="#121417" stroke-width="1.6" stroke-dasharray="10 3 2 3"/></svg><span>Property line (measured)</span>
        <svg viewBox="0 0 34 14"><rect x="1" y="2" width="32" height="10" fill="#fff" stroke="#121417" stroke-width="1.6"/><path d="M4 12 L12 2 M12 12 L20 2 M20 12 L28 2" stroke="#C9CDD1"/></svg><span>Building</span>
        <svg viewBox="0 0 34 14"><rect x="1" y="2" width="32" height="10" fill="none" stroke="#121417" stroke-dasharray="4 2"/></svg><span>Canopy</span>
        <svg viewBox="0 0 34 14"><rect x="1" y="2" width="32" height="10" fill="#EEF0F1" stroke="#8A9096"/></svg><span>Concrete walk</span>
        <svg viewBox="0 0 34 14"><rect x="1" y="2" width="32" height="10" fill="#fff" stroke="#5F6368"/><circle cx="8" cy="7" r="1" fill="#9AA0A6"/><circle cx="17" cy="7" r="1" fill="#9AA0A6"/><circle cx="26" cy="7" r="1" fill="#9AA0A6"/></svg><span>Landscape / island</span>
        <svg viewBox="0 0 34 14"><rect x="9" y="2" width="16" height="10" fill="#3A3F45" stroke="#121417" stroke-width="1.2"/></svg><span>Asphalt repair (solid = confirmed, dashed = draft)</span>
        <svg viewBox="0 0 34 14"><line x1="1" y1="7" x2="33" y2="7" stroke="#8A9096" stroke-dasharray="4 3"/></svg><span>Map measurement check line</span>
      </div>
    </div>
    <div class="blk">
      <div class="lab">Notes</div>
      <ol>
        <li>Property lines from Google Maps measurements; corners fitted so all four sides match exactly.</li>
        <li>Building, islands, walks and drives traced from scaled aerial imagery and checked against a high-resolution aerial, about &plusmn;2 ft.</li>
        <li>Building footprint taken at the walls, not the roof. The measured 132.75' runs from the north face to the outer edge of the south walk.</li>
        <li>Drives confirmed from street view: NW drive and main entrance on Route 130; one entrance on Municipal Drive at the SE corner.</li>
        <li>Planting and islands revised from two field markups; island angles measured from the aerial (rows follow their nearest property line, not the building).</li>
        <li>Repair sizes from the proposal. Locations are drafted from each area's name until confirmed in the editor.</li>
      </ol>
    </div>
    <div class="blk sched">
      <div class="lab">Asphalt repair schedule (cut &amp; replace)</div>
      <table><thead><tr><th>#</th><th>Location</th><th class="n">Size (ft)</th><th class="n">SF</th></tr></thead>
      <tbody>{rows}</tbody>
      <tfoot><tr><td></td><td>{len(patches["patches"])} areas</td><td></td><td class="n">{patches["total_sqft"]:g}</td></tr></tfoot></table>
    </div>
  </aside>
</div>
<script>
const img = document.getElementById('aerial'), btn = document.getElementById('aerialBtn'), op = document.getElementById('aerialOp');
let on = false;
const svg = document.getElementById('plan');
// the aerial underlay is Google imagery and is not published; hide its controls when it is absent
{{ const t = new Image(); t.onerror = () => {{ btn.hidden = true; op.hidden = true; img.remove(); }}; t.src = 'aerial-underlay.jpg'; }}
const sync = () => {{ img.setAttribute('opacity', on ? op.value / 100 : 0); btn.setAttribute('aria-pressed', on); svg.classList.toggle('aerial-on', on); }};
btn.addEventListener('click', () => {{ on = !on; sync(); }});
op.addEventListener('input', () => {{ on = true; sync(); }});

__EDITOR__
</script>
</body></html>
"""
(HERE / "index.html").write_text(page.replace("__EDITOR__", EDITOR_JS).replace("__PATCHES__", patch_json))
print("wrote index.html", len(page) // 1024, "KB")
