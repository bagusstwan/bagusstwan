#!/usr/bin/env python3
"""Generate an animated isometric "Contribution City" for a GitHub profile.

Usage:
  python generate_city.py <username> [out.svg] [out.html]

- out.svg  : animated SVG for the README (rise animation + outline "blink")
- out.html : interactive page (same SVG inline) with hover tooltips
Data comes from the public contribution calendar (no token needed).
"""
import math
import random
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "bagusstwan"
OUT_SVG = sys.argv[2] if len(sys.argv) > 2 else "assets/contribution-city.svg"
OUT_HTML = sys.argv[3] if len(sys.argv) > 3 else "docs/index.html"

# ---------- 1. fetch data ----------
req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "Mozilla/5.0"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
cells = re.findall(
    r'<td[^>]*data-date="([\d-]+)"[^>]*id="(contribution-day-component-(\d+)-(\d+))"[^>]*data-level="(\d)"',
    html,
)
tips = dict(
    re.findall(r'<tool-tip[^>]*for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>', html)
)


def count_of(cid):
    m = re.match(r"(\d+|No) contribution", tips.get(cid, "").strip())
    return 0 if not m or m.group(1) == "No" else int(m.group(1))


days = [
    dict(date=d, day=int(r), week=int(c), level=int(l), count=count_of(cid))
    for d, cid, r, c, l in cells
]
if not days:
    sys.exit("No contribution data found")

total = sum(d["count"] for d in days)
active = sum(1 for d in days if d["count"] > 0)
busiest = max(d["count"] for d in days)
weeks = max(d["week"] for d in days) + 1
short = lambda n: f"{n/1000:.1f}K" if n >= 1000 else str(n)
f = lambda x: f"{x:.1f}".rstrip("0").rstrip(".")

# ---------- 2. geometry ----------
W, H = 1152, 582
S = 14.0
CX = math.cos(math.radians(30)) * S
CY = 0.5 * S
MAXH = 92.0
X0 = 330 + 7 * CX
Y0 = 105

PALETTE = {  # level: (top, left, right)
    0: ("#11605a", "#0d4b46", "#0a3d39"),
    1: ("#33c4b2", "#27a094", "#1f8a80"),
    2: ("#45d8c5", "#3cb9ab", "#2e9e92"),
    3: ("#66ebd9", "#6fd3c7", "#4eb0a4"),
    4: ("#8ef3e4", "#8fe0d5", "#68bdb2"),
}


def height(c):
    return 1.6 if c <= 0 else 5 + (MAXH - 5) * (c / busiest) ** 0.9


# ---------- 3. blocks (painter's order: back to front) ----------
rnd = random.Random(7)
blocks = []
for d in sorted(days, key=lambda d: (d["week"] + d["day"], d["day"])):
    w, y = d["week"], d["day"]
    h = height(d["count"])
    px, py = X0 + (w - y) * CX, Y0 + (w + y) * CY
    ty = py - h
    pts = f"{f(px)},{f(ty)} {f(px+CX)},{f(ty+CY)} {f(px)},{f(ty+2*CY)} {f(px-CX)},{f(ty+CY)}"
    ct, cl, cr = PALETTE[d["level"] if d["count"] > 0 else 0]
    left = f'<g transform="translate({f(px-CX)},{f(py+CY)}) skewY(30)"><rect {{c}} y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cl}"/></g>'
    right = f'<g transform="translate({f(px)},{f(py+2*CY)}) skewY(-30)"><rect {{c}} y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cr}"/></g>'
    data = f'data-date="{d["date"]}" data-count="{d["count"]}"'
    if d["count"] <= 0:
        blocks.append(
            f'<g class="z" {data}>{left.format(c="")}{right.format(c="")}<polygon points="{pts}" fill="{ct}"/></g>'
        )
        continue
    rise_delay = (w / max(weeks - 1, 1)) * 2.2 + y * 0.04
    vars_ = f"--h:{f(h)}px;--d:{rise_delay:.2f}s"
    if rnd.random() < 0.55:          # only some blocks blink
        bp = rnd.uniform(9, 18)      # blink cycle length (s)
        bd = rnd.uniform(-0.6 * bp, 0)  # start offset (negative = already mid-cycle)
        vars_ += f";--bp:{bp:.1f}s;--bd:{bd:.1f}s"
        cls = "b k"
    else:
        cls = "b"
    blocks.append(
        f'<g class="{cls}" style="{vars_}" {data}>'
        f'{left.format(c=chr(99)+"lass=" + chr(34) + "s" + chr(34))}{right.format(c=chr(99)+"lass=" + chr(34) + "s" + chr(34))}'
        f'<polygon class="t" points="{pts}" fill="{ct}"/></g>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution city of @{USER}: {total} contributions in the last year">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#062f2e"/><stop offset="0.5" stop-color="#134e4a"/><stop offset="1" stop-color="#062f2e"/>
  </linearGradient>
</defs>
<style>
  .lbl{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
  .sans{{font-family:"Segoe UI",system-ui,-apple-system,Helvetica,Arial,sans-serif}}
  .b polygon,.b rect{{stroke:#a7f8ec;stroke-width:1;stroke-linejoin:round;stroke-opacity:0}}
  /* rise animation (+ outline blink for blocks marked .k) */
  .t{{animation:rise 12s cubic-bezier(.3,.7,.2,1) var(--d,0s) infinite both}}
  .s{{transform-box:fill-box;transform-origin:50% 100%;animation:grow 12s cubic-bezier(.3,.7,.2,1) var(--d,0s) infinite both}}
  .k .t{{animation:rise 12s cubic-bezier(.3,.7,.2,1) var(--d,0s) infinite both,blink var(--bp) ease-in-out var(--bd) infinite}}
  .k .s{{animation:grow 12s cubic-bezier(.3,.7,.2,1) var(--d,0s) infinite both,blink var(--bp) ease-in-out var(--bd) infinite}}
  @keyframes rise{{0%{{transform:translateY(var(--h,0px))}}16%,90%{{transform:translateY(0)}}100%{{transform:translateY(var(--h,0px))}}}}
  @keyframes grow{{0%{{transform:scaleY(0)}}16%,90%{{transform:scaleY(1)}}100%{{transform:scaleY(0)}}}}
  @keyframes blink{{0%,76%{{fill-opacity:1;stroke-opacity:0}}81%,89%{{fill-opacity:.05;stroke-opacity:1}}94%,100%{{fill-opacity:1;stroke-opacity:0}}}}
  @media (prefers-reduced-motion:reduce){{.t,.s,.k .t,.k .s{{animation:none}}}}
</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="30" fill="url(#bg)" stroke="#2dd4bf" stroke-opacity=".45"/>
<text class="lbl" x="52" y="80" font-size="13" font-weight="700" letter-spacing="3.5" fill="#5eead4">CONTRIBUTION CITY</text>
<g class="sans">
  <text x="52" y="126" font-size="40" font-weight="800" fill="#ccfbf1">{short(total)}</text>
  <text x="52" y="156" font-size="16" font-weight="600" fill="#5eead4">contributions in the last year</text>
  <text x="52" y="197" font-size="15" font-weight="600" fill="#5eead4">{active} active days</text>
  <text x="52" y="222" font-size="15" font-weight="600" fill="#5eead4">Busiest day: {busiest}</text>
</g>
<text class="lbl" x="52" y="515" font-size="13" fill="#5eead4">@{USER}</text>
{"".join(blocks)}
</svg>
'''

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Contribution City · @{USER}</title>
<style>
  html,body{{margin:0;background:#04201f;color:#99f6e4;font-family:"Segoe UI",system-ui,sans-serif}}
  main{{max-width:1152px;margin:0 auto;padding:24px 12px}}
  svg{{width:100%;height:auto;display:block}}
  .b,.z{{cursor:pointer}}
  .b:hover .t,.z:hover polygon{{filter:brightness(1.4)}}
  #tip{{position:fixed;pointer-events:none;z-index:9;background:#042f2e;color:#ccfbf1;border:1px solid #2dd4bf;
        padding:6px 10px;border-radius:8px;font-size:13px;white-space:nowrap;opacity:0;transition:opacity .08s;
        box-shadow:0 6px 20px rgba(0,0,0,.45)}}
  #tip b{{color:#5eead4}}
  footer{{text-align:center;font-size:13px;opacity:.7;margin-top:12px}}
  footer a{{color:#5eead4}}
</style></head>
<body><main>
{svg}
<footer>Arahkan kursor ke sebuah blok untuk melihat jumlah kontribusi · <a href="https://github.com/{USER}">github.com/{USER}</a></footer>
</main>
<div id="tip"></div>
<script>
(function(){{
  var tip=document.getElementById('tip');
  function label(g){{
    var n=+g.getAttribute('data-count'), p=g.getAttribute('data-date').split('-');
    var dt=new Date(Date.UTC(+p[0],+p[1]-1,+p[2]));
    var s=dt.toLocaleDateString('en-US',{{timeZone:'UTC',month:'short',day:'numeric',year:'numeric'}});
    return (n? '<b>'+n+' contribution'+(n>1?'s':'')+'</b>' : '<b>No contributions</b>')+' on '+s;
  }}
  function show(e){{
    var g=e.target.closest&&e.target.closest('[data-date]');
    if(!g){{tip.style.opacity=0;return;}}
    tip.innerHTML=label(g);
    tip.style.opacity=1;
    var x=Math.min(e.clientX+14, innerWidth-tip.offsetWidth-8), y=e.clientY-tip.offsetHeight-14;
    tip.style.left=Math.max(8,x)+'px'; tip.style.top=(y<8?e.clientY+18:y)+'px';
  }}
  document.addEventListener('pointermove',show);
  document.addEventListener('pointerdown',show);
  document.addEventListener('pointerleave',function(){{tip.style.opacity=0}});
}})();
</script></body></html>
'''

import os
for path, content in ((OUT_SVG, svg), (OUT_HTML, page)):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    print(f"{path}: {len(content)/1024:.0f} KB")
print(f"total={total} active={active} busiest={busiest}")
