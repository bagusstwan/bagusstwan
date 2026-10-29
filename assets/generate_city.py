#!/usr/bin/env python3
"""Generate an animated isometric "Contribution City" SVG for a GitHub profile.

Usage: python generate_city.py <github-username> [output.svg]
Data is read from the public contribution calendar (no token needed).
"""
import math
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "bagusstwan"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/contribution-city.svg"

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


def short(n):
    return f"{n/1000:.1f}K" if n >= 1000 else str(n)


# ---------- 2. geometry ----------
W, H = 1152, 582
S = 14.0                      # tile edge length
CX = math.cos(math.radians(30)) * S   # half tile width
CY = 0.5 * S                          # half tile height
MAXH = 92.0
X0 = 330 + 7 * CX
Y0 = 105


def height(c):
    if c <= 0:
        return 1.6
    return 5 + (MAXH - 5) * (c / busiest) ** 0.9


PALETTE = {  # level: (top, left, right)
    0: ("#11605a", "#0d4b46", "#0a3d39"),
    1: ("#33c4b2", "#27a094", "#1f8a80"),
    2: ("#45d8c5", "#3cb9ab", "#2e9e92"),
    3: ("#66ebd9", "#6fd3c7", "#4eb0a4"),
    4: ("#8ef3e4", "#8fe0d5", "#68bdb2"),
}


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


# ---------- 3. build blocks (back to front) ----------
blocks = []
for d in sorted(days, key=lambda d: (d["week"] + d["day"], d["day"])):
    w, y = d["week"], d["day"]
    h = height(d["count"])
    px, py = X0 + (w - y) * CX, Y0 + (w + y) * CY   # top vertex of the ground tile
    top = (d["level"] if d["count"] > 0 else 0)
    ct, cl, cr = PALETTE[top]
    ty = py - h
    pts = f"{f(px)},{f(ty)} {f(px+CX)},{f(ty+CY)} {f(px)},{f(ty+2*CY)} {f(px-CX)},{f(ty+CY)}"
    if d["count"] <= 0:
        # flat ground tile: static, slightly raised slab
        blocks.append(
            f'<g class="z"><g transform="translate({f(px-CX)},{f(py+CY)}) skewY(30)"><rect y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cl}"/></g>'
            f'<g transform="translate({f(px)},{f(py+2*CY)}) skewY(-30)"><rect y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cr}"/></g>'
            f'<polygon points="{pts}" fill="{ct}"/></g>'
        )
        continue
    delay = (w / max(weeks - 1, 1)) * 2.2 + (y * 0.04)
    style = f'--h:{f(h)}px;animation-delay:{delay:.2f}s'
    blocks.append(
        f'<g class="b">'
        f'<g transform="translate({f(px-CX)},{f(py+CY)}) skewY(30)"><rect class="s" style="animation-delay:{delay:.2f}s" y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cl}"/></g>'
        f'<g transform="translate({f(px)},{f(py+2*CY)}) skewY(-30)"><rect class="s" style="animation-delay:{delay:.2f}s" y="-{f(h)}" width="{f(CX)}" height="{f(h)}" fill="{cr}"/></g>'
        f'<polygon class="t" style="{style}" points="{pts}" fill="{ct}"/>'
        f'</g>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution city of @{USER}: {total} contributions in the last year">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#062f2e"/>
    <stop offset="0.5" stop-color="#134e4a"/>
    <stop offset="1" stop-color="#062f2e"/>
  </linearGradient>
</defs>
<style>
  .lbl{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
  .sans{{font-family:"Segoe UI",system-ui,-apple-system,Helvetica,Arial,sans-serif}}
  /* cycle: rise -> hold -> sink, then repeat */
  .t{{animation:rise 12s cubic-bezier(.3,.7,.2,1) infinite both}}
  .s{{transform-box:fill-box;transform-origin:50% 100%;animation:grow 12s cubic-bezier(.3,.7,.2,1) infinite both}}
  @keyframes rise{{0%{{transform:translateY(var(--h,0px))}}16%,90%{{transform:translateY(0)}}100%{{transform:translateY(var(--h,0px))}}}}
  @keyframes grow{{0%{{transform:scaleY(0)}}16%,90%{{transform:scaleY(1)}}100%{{transform:scaleY(0)}}}}
  @media (prefers-reduced-motion:reduce){{.t,.s{{animation:none}}}}
</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="30" fill="url(#bg)" stroke="#2dd4bf" stroke-opacity=".45"/>
<g class="lbl" fill="#5eead4">
  <text x="52" y="80" font-size="13" font-weight="700" letter-spacing="3.5">CONTRIBUTION CITY</text>
</g>
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
open(OUT, "w", encoding="utf-8").write(svg)
print(f"{OUT}: {len(svg)/1024:.0f} KB | total={total} active={active} busiest={busiest}")
