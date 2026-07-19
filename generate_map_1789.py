#!/usr/bin/env python3
"""Overlay Etienne Cabos' life journey onto the historical 1789 map of the
Holy Roman Empire (docs/images/karte-1789.png).

The base map uses a conic-style historical projection, so the station points
are georeferenced with a 2nd-order polynomial transform fitted to eleven
clearly labelled cities on the map itself (residuals ~14 px on a 2362 px-wide
image; verified against Halle, Frankfurt, Berlin, ...).

Produces docs/images/karte-1789-weg.png (DE) and karte-1789-weg-en.png (EN).
The original base map is never modified.
"""
import base64
import math
import numpy as np
import cairosvg

BASE = "docs/images/karte-1789.png"
W, H = 2362, 1928

# --- georeferencing (lon,lat -> pixel), fitted to 11 map cities ------------
CX = [1515.673919082562, 201.51538207376188, -83.70642911586361,
      -0.19948706598012103, -1.5344005805884704, 0.9916268962743368]
CY = [8619.605844652955, -56.676652259205106, -106.21226777141489,
      -1.378504898297244, 1.7281340457661827, -0.98998634352083]


def px(lon, lat):
    v = [1, lon, lat, lon * lon, lon * lat, lat * lat]
    x = sum(a * b for a, b in zip(v, CX))
    y = sum(a * b for a, b in zip(v, CY))
    return x, y


# --- stations --------------------------------------------------------------
COORD = {
    "caussade": (1.53, 44.16),   # off-map (far south) -> enters at bottom edge
    "stettin": (14.55, 53.43),
    "isenburg": (8.70, 50.05),
    "rotterdam": (4.48, 51.92),
    "berlin": (13.40, 52.52),
    "halle": (11.97, 51.48),
}

# main chronological legs (curved). side = bow direction, frac = amount
ROUTE = ["caussade", "stettin", "isenburg", "rotterdam", "berlin"]
CURVES = {0: ("up", 0.10), 1: ("up", 0.12), 2: ("up", 0.14), 3: ("down", 0.16)}

# station label text per language: (dx, dy, anchor, title, sub)
LABELS = {
    "de": {
        "stettin": (14, -6, "start", "Stettin", "Soldat · Heirat 1772–79"),
        "isenburg": (-14, -20, "end", "Isenburg", "Reisepass 1780"),
        "rotterdam": (-14, -6, "end", "Rotterdam", "Bürger 1780–92"),
        "berlin": (16, 22, "start", "Berlin", "Zahnarzt ab 1793 · † 1808"),
        "halle": (14, 16, "start", "Halle", "Zahnarzt-Anzeigen 1794/98"),
        "caussade_corner": "Caussade (Frankreich) · geb. 1737",
        "title": "Etiennes Lebensweg 1737–1808",
    },
    "en": {
        "stettin": (14, -6, "start", "Stettin", "Soldier · married 1772–79"),
        "isenburg": (-14, -20, "end", "Isenburg", "Travel pass 1780"),
        "rotterdam": (-14, -6, "end", "Rotterdam", "Citizen 1780–92"),
        "berlin": (16, 22, "start", "Berlin", "Dentist from 1793 · d. 1808"),
        "halle": (14, 16, "start", "Halle", "Dentist ads 1794/98"),
        "caussade_corner": "Caussade (France) · b. 1737",
        "title": "Etienne's life journey 1737–1808",
    },
}

ROUTE_COL = "#7d1416"
DOT_COL = "#7d1416"
INK = "#241610"
HALO = "#ffffff"


def control(p0, p1, side, frac):
    x0, y0 = p0
    x1, y1 = p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    # perpendicular
    nx, ny = -dy / length, dx / length
    if side == "down":
        nx, ny = -nx, -ny
    return mx + nx * length * frac, my + ny * length * frac


def quad(p0, c, p1, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]
    return x, y


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def halo_text(x, y, text, size, fill=INK, anchor="middle", weight="700",
              italic=False, halo_w=5.0, halo=HALO):
    st = "italic" if italic else "normal"
    fam = "DejaVu Sans"
    base = (f'font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'font-style="{st}" text-anchor="{anchor}" '
            f'x="{x:.1f}" y="{y:.1f}"')
    t = esc(text)
    return (f'<text {base} fill="{halo}" stroke="{halo}" stroke-width="{halo_w}" '
            f'stroke-linejoin="round">{t}</text>'
            f'<text {base} fill="{fill}">{t}</text>')


def clip_to_canvas(p_out, p_in):
    """Return the point where segment p_out(off-canvas)->p_in enters canvas."""
    x0, y0 = p_out
    x1, y1 = p_in
    best_t = 0.0
    for edge in ("x0", "x1", "y0", "y1"):
        if edge == "x0" and x1 != x0:
            t = (0 - x0) / (x1 - x0)
        elif edge == "x1" and x1 != x0:
            t = (W - x0) / (x1 - x0)
        elif edge == "y0" and y1 != y0:
            t = (0 - y0) / (y1 - y0)
        elif edge == "y1" and y1 != y0:
            t = (H - y0) / (y1 - y0)
        else:
            continue
        if 0 <= t <= 1:
            xx = x0 + t * (x1 - x0)
            yy = y0 + t * (y1 - y0)
            if -1 <= xx <= W + 1 and -1 <= yy <= H + 1:
                best_t = max(best_t, t)
    return (x0 + best_t * (x1 - x0), y0 + best_t * (y1 - y0))


def build(lang):
    L = LABELS[lang]
    with open(BASE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<image href="data:image/png;base64,{b64}" x="0" y="0" '
        f'width="{W}" height="{H}"/>',
    ]

    P = {k: px(*v) for k, v in COORD.items()}
    # Caussade is off-map; find where its leg enters the canvas
    entry = clip_to_canvas(P["caussade"], P["stettin"])

    # --- draw route legs (halo underlay first, then ink) ------------------
    def leg_path(a, b, side, frac):
        c = control(a, b, side, frac)
        return f'M {a[0]:.1f} {a[1]:.1f} Q {c[0]:.1f} {c[1]:.1f} {b[0]:.1f} {b[1]:.1f}', c

    legs = []
    for i in range(len(ROUTE) - 1):
        a_name, b_name = ROUTE[i], ROUTE[i + 1]
        a = entry if a_name == "caussade" else P[a_name]
        b = P[b_name]
        side, frac = CURVES.get(i, ("up", 0.10))
        d, c = leg_path(a, b, side, frac)
        legs.append((d, a, c, b))

    # solid, haloed route line (distinct from the map's red-dashed HRE border)
    for d, *_ in legs:
        parts.append(f'<path d="{d}" fill="none" stroke="{HALO}" '
                     f'stroke-width="13" stroke-linecap="round"/>')
    for d, *_ in legs:
        parts.append(f'<path d="{d}" fill="none" stroke="{ROUTE_COL}" '
                     f'stroke-width="6.5" stroke-linecap="round" '
                     f'stroke-linejoin="round"/>')

    # arrowheads at the end of each leg (tangent from bezier)
    for d, a, c, b in legs:
        p_near = quad(a, c, b, 0.94)
        ang = math.atan2(b[1] - p_near[1], b[0] - p_near[0])
        s = 22
        x1 = b[0] - s * math.cos(ang - 0.42)
        y1 = b[1] - s * math.sin(ang - 0.42)
        x2 = b[0] - s * math.cos(ang + 0.42)
        y2 = b[1] - s * math.sin(ang + 0.42)
        parts.append(f'<polygon points="{b[0]:.1f},{b[1]:.1f} {x1:.1f},{y1:.1f} '
                     f'{x2:.1f},{y2:.1f}" fill="{ROUTE_COL}" '
                     f'stroke="{HALO}" stroke-width="2.5" stroke-linejoin="round"/>')

    # --- station dots + labels -------------------------------------------
    def dot(p, r=11):
        parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r+3}" '
                     f'fill="{HALO}"/>')
        parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" '
                     f'fill="{DOT_COL}"/>')
        parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r-5}" '
                     f'fill="{HALO}"/>')

    for name in ("stettin", "isenburg", "rotterdam", "berlin"):
        dot(P[name])
    dot(P["halle"], r=8)

    for name in ("stettin", "isenburg", "rotterdam", "berlin", "halle"):
        dx, dy, anchor, title, sub = L[name]
        x, y = P[name]
        parts.append(halo_text(x + dx, y + dy, title, 34, anchor=anchor,
                               weight="700"))
        parts.append(halo_text(x + dx, y + dy + 30, sub, 24, anchor=anchor,
                               weight="600", italic=True))

    # --- Caussade entry marker at the bottom edge -------------------------
    ex, ey = entry
    # small inward arrow already drawn as leg; add an origin dot on the edge
    parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="12" fill="{HALO}"/>')
    parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="9" fill="{DOT_COL}"/>')
    parts.append(halo_text(ex + 20, ey - 26, L["caussade_corner"], 30,
                           anchor="start", weight="700"))

    # --- title plate (bottom-left, over Switzerland/France, area is empty) -
    tx, ty = 70, 1760
    parts.append(halo_text(tx, ty, L["title"], 40, anchor="start",
                           weight="700", halo_w=6))

    parts.append("</svg>")
    return "".join(parts)


def main():
    for lang, out in (("de", "docs/images/karte-1789-weg.png"),
                      ("en", "docs/images/karte-1789-weg-en.png")):
        svg = build(lang)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=out,
                         output_width=W)
        print("wrote", out)


if __name__ == "__main__":
    main()
