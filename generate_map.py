#!/usr/bin/env python3
"""Generate the life-journey map of Etienne Cabos (1737-1808) as a PNG.

Builds a clean, self-contained SVG (equirectangular projection with a
cos-latitude correction) showing the main residences as a numbered route
plus the shorter journeys (military campaign, business trips) as dashed
side-trips, then rasterises it to a high-resolution PNG with cairosvg.

Produces two language variants:
  docs/images/karte-stationen.png     (German, also used in the PDF)
  docs/images/karte-stationen-en.png  (English)
"""

import math
import os

import cairosvg

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

# --- Palette (antique styling, matches the book's brown/amber theme) ---
PARCHMENT = "#f4ecd9"      # page background
PARCHMENT2 = "#efe4cb"     # panels / legend
FRAME = "#b9a37e"
SEA = "#c2d2d0"            # muted blue-grey water
LAND = "#e9dcbb"          # aged parchment land
COAST = "#7d6a49"         # sepia coastline
GRID = "#a8987a"          # graticule (sepia, low opacity applied inline)
LAND_LABEL = "#9c8a63"    # region names over land
SEA_LABEL = "#8fa3a2"     # sea names
ROUTE = "#5d4037"         # dark brown main route
ROUTE_HALO = "#f7f1e2"
EXCURSION = "#c9781f"     # amber side-trips
PIN = "#7a4a2b"
PIN_EDGE = "#4e3120"
EXC_PIN = "#d98a2b"
INK = "#3a2c1e"
INK_SOFT = "#6f5c46"

# --- Geographic bounds (lon/lat) ---
LON_MIN, LON_MAX = -3.2, 16.6
LAT_MIN, LAT_MAX = 43.0, 54.75
MEAN_LAT = (LAT_MIN + LAT_MAX) / 2
K = math.cos(math.radians(MEAN_LAT))  # horizontal compression

# --- Canvas / layout ---
W, H = 1240, 862
MAP_X0, MAP_X1 = 58, 792   # map drawing band (with inner margin applied below)
MAP_Y0, MAP_Y1 = 108, 792
INNER = 34

_ax0 = MAP_X0 + INNER
_ax1 = MAP_X1 - INNER
_ay0 = MAP_Y0 + INNER
_ay1 = MAP_Y1 - INNER
_eff_w = (LON_MAX - LON_MIN) * K
_eff_h = (LAT_MAX - LAT_MIN)
SCALE = min((_ax1 - _ax0) / _eff_w, (_ay1 - _ay0) / _eff_h)
_used_w = _eff_w * SCALE
_used_h = _eff_h * SCALE
_off_x = _ax0 + ((_ax1 - _ax0) - _used_w) / 2
_off_y = _ay0 + ((_ay1 - _ay0) - _used_h) / 2


def px(lon, lat):
    x = _off_x + (lon - LON_MIN) * K * SCALE
    y = _off_y + (LAT_MAX - lat) * SCALE
    return x, y


def _ring_to_path(coords):
    parts = []
    for i, (lon, lat) in enumerate(coords):
        x, y = px(lon, lat)
        parts.append(("M " if i == 0 else "L ") + f"{x:.1f} {y:.1f}")
    return " ".join(parts) + " Z"


def build_land_path():
    """Return one SVG path 'd' for all land within the map bounds, using real
    coastline geometry (Natural Earth 110m via geopandas, offline). Country
    borders are dissolved away so only coastlines remain - period-appropriate,
    since 18th-century political borders differed from today's. Falls back to
    an empty string if geopandas is unavailable (pre-generated PNGs ship in the
    repo, so the deploy build never needs this)."""
    try:
        import warnings
        warnings.filterwarnings("ignore")
        import geopandas as gpd
        from shapely.geometry import box
        from shapely.ops import unary_union

        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        land = unary_union(list(world.geometry))
        clip = box(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)
        land = land.intersection(clip)
    except Exception as exc:  # pragma: no cover
        print(f"  [land layer skipped: {exc}]")
        return ""

    polys = []
    if land.geom_type == "Polygon":
        polys = [land]
    elif land.geom_type in ("MultiPolygon", "GeometryCollection"):
        polys = [g for g in land.geoms if g.geom_type == "Polygon"]

    d = []
    for poly in polys:
        d.append(_ring_to_path(list(poly.exterior.coords)))
        for hole in poly.interiors:
            d.append(_ring_to_path(list(hole.coords)))
    return " ".join(d)


LAND_PATH = build_land_path()


# lon, lat of every place
COORD = {
    "caussade": (1.53, 44.16),
    "stettin": (14.55, 53.43),
    "isenburg": (8.70, 50.05),
    "rotterdam": (4.48, 51.92),
    "berlin": (13.37, 52.52),
    "bohemia": (14.30, 50.55),
    "lehavre": (0.11, 49.49),
    "halle": (11.97, 51.48),
}

MAIN_ROUTE = ["caussade", "stettin", "isenburg", "rotterdam", "berlin"]
EXCURSIONS = [("stettin", "bohemia"), ("rotterdam", "lehavre"), ("berlin", "halle")]

# Region context labels over land: (lon, lat, rotation)
REGIONS_BASE = [
    (1.9, 47.2, 0),    # France
    (5.6, 52.85, 0),   # Netherlands
    (11.6, 54.0, 0),   # Prussia
    (14.9, 49.5, 0),   # Bohemia
]
# Sea labels: (lon, lat, rotation)
SEAS_BASE = [
    (3.1, 54.4, 0),    # North Sea
    (-2.4, 46.0, 0),   # Atlantic
]

TEXT = {
    "de": {
        "title": "Etiennes Lebensweg 1737–1808",
        "subtitle": "Von Caussade in Südfrankreich über Stettin, Isenburg und Rotterdam nach Berlin",
        "regions": ["FRANKREICH", "NIEDER-\nLANDE", "PREUSSEN", "BÖHMEN"],
        "seas": ["NORDSEE", "ATLANTIK"],
        "legend_head": "Stationen",
        "pins": {
            "caussade": "Caussade",
            "stettin": "Stettin",
            "isenburg": "Isenburg",
            "rotterdam": "Rotterdam",
            "berlin": "Berlin",
        },
        "exc": {
            "bohemia": "Böhmen 1778/79",
            "lehavre": "Le Havre 1783",
            "halle": "Halle 1794/98",
        },
        "legend": [
            ("1", "Caussade", "Quercy, Frankreich · 1737",
             "Geburt & Taufe; Kindheit und Jugend im hugenottischen Süden."),
            ("2", "Stettin", "Preußen · 1772–1780",
             "Heirat mit Maria Justine Siercken (1772); Soldat im "
             "Infanterieregiment Nr. 8; fünf Kinder geboren."),
            ("↳", "Böhmen", "1778/79",
             "Kartoffelkrieg – Teilnahme am Feldzug (Nebenreise)."),
            ("3", "Isenburg", "bei Frankfurt · 1780",
             "Zwischenstation; kirchlicher Reisepass nach Holland (10. April 1780)."),
            ("4", "Rotterdam", "Niederlande · 1780–1792",
             "Bürgerrecht; Galanteriewarengeschäft am Vissersdijk; drei Kinder; "
             "wachsende Not, Unterhaltsvertrag 1792."),
            ("↳", "Le Havre", "1783",
             "Sohn Etienne unterwegs auf der Rückreise geboren (Nebenreise)."),
            ("5", "Berlin & Charlottenburg", "Preußen · 1792–1808",
             "Neuanfang als Zahnarzt („Dentiste“); Sohn Charles Emmanuel (1793); "
             "Tochter Elisabeth heiratet (1807); Tod am 14. September 1808."),
            ("↳", "Halle (Saale)", "1794 & 1798",
             "Als reisender Zahnarzt (Nebenreisen)."),
        ],
        "caption": "Karte im historischen Stil (Küstenlinien nach geografischen Daten) – "
                   "Hauptstationen nummeriert, Nebenreisen gestrichelt.",
        "scalebar": "200 km",
        "north": "N",
    },
    "en": {
        "title": "Etienne's Life Journey 1737–1808",
        "subtitle": "From Caussade in southern France via Stettin, Isenburg and Rotterdam to Berlin",
        "regions": ["FRANCE", "NETHER-\nLANDS", "PRUSSIA", "BOHEMIA"],
        "seas": ["NORTH SEA", "ATLANTIC"],
        "legend_head": "Stations",
        "pins": {
            "caussade": "Caussade",
            "stettin": "Stettin",
            "isenburg": "Isenburg",
            "rotterdam": "Rotterdam",
            "berlin": "Berlin",
        },
        "exc": {
            "bohemia": "Bohemia 1778/79",
            "lehavre": "Le Havre 1783",
            "halle": "Halle 1794/98",
        },
        "legend": [
            ("1", "Caussade", "Quercy, France · 1737",
             "Birth & baptism; childhood and youth in the Huguenot south."),
            ("2", "Stettin", "Prussia · 1772–1780",
             "Marriage to Maria Justine Siercken (1772); soldier in Infantry "
             "Regiment No. 8; five children born."),
            ("↳", "Bohemia", "1778/79",
             "Potato War – took part in the campaign (side-trip)."),
            ("3", "Isenburg", "near Frankfurt · 1780",
             "Waypoint; church travel pass to Holland (10 April 1780)."),
            ("4", "Rotterdam", "Netherlands · 1780–1792",
             "Citizenship; fancy-goods shop on the Vissersdijk; three children; "
             "growing hardship, maintenance contract 1792."),
            ("↳", "Le Havre", "1783",
             "Son Etienne born en route on the return journey (side-trip)."),
            ("5", "Berlin & Charlottenburg", "Prussia · 1792–1808",
             "New start as a dentist (“Dentiste”); son Charles Emmanuel (1793); "
             "daughter Elisabeth marries (1807); death on 14 September 1808."),
            ("↳", "Halle (Saale)", "1794 & 1798",
             "As a travelling dentist (side-trips)."),
        ],
        "caption": "Map in a historical style (coastlines from geographic data) – "
                   "main stations numbered, side-trips dashed.",
        "scalebar": "200 km",
        "north": "N",
    },
}

FONT = "Liberation Serif, DejaVu Serif, Georgia, serif"
SANS = "Liberation Sans, DejaVu Sans, Helvetica, sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def arrowhead(x0, y0, x1, y1, t=0.60, size=11, color=ROUTE):
    """Triangle arrowhead at fraction t along segment, pointing to (x1,y1)."""
    ax = x0 + (x1 - x0) * t
    ay = y0 + (y1 - y0) * t
    ang = math.atan2(y1 - y0, x1 - x0)
    p1 = (ax + size * math.cos(ang), ay + size * math.sin(ang))
    p2 = (ax + size * math.cos(ang + 2.5), ay + size * math.sin(ang + 2.5))
    p3 = (ax + size * math.cos(ang - 2.5), ay + size * math.sin(ang - 2.5))
    return (f'<polygon points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} '
            f'{p3[0]:.1f},{p3[1]:.1f}" fill="{color}"/>')


def halo_text(x, y, text, size, fill, anchor="start", family=SANS,
              weight=None, italic=False, ls=None, halo=PARCHMENT2, halo_w=3.0):
    """Halo'd text drawn as two elements (halo underneath, fill on top).

    cairosvg does not honour SVG `paint-order`, so a single element with a
    thick light stroke would paint the halo over the dark fill and wash the
    text out. Emitting the halo copy first and the fill copy second is robust."""
    a = f'font-family="{family}" font-size="{size}"'
    if weight:
        a += f' font-weight="{weight}"'
    if italic:
        a += ' font-style="italic"'
    if ls:
        a += f' letter-spacing="{ls}"'
    common = f'x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" {a}'
    return (f'<text {common} fill="{halo}" stroke="{halo}" stroke-width="{halo_w}" '
            f'stroke-linejoin="round">{esc(text)}</text>'
            f'<text {common} fill="{fill}">{esc(text)}</text>')


def build_svg(lang):
    t = TEXT[lang]
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}">')

    # background
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PARCHMENT}"/>')

    # map plate
    s.append(f'<rect x="{MAP_X0}" y="{MAP_Y0}" width="{MAP_X1-MAP_X0}" '
             f'height="{MAP_Y1-MAP_Y0}" fill="{PARCHMENT2}" stroke="{FRAME}" '
             f'stroke-width="2" rx="6"/>')

    # clip for map interior
    s.append(f'<clipPath id="mapclip"><rect x="{MAP_X0+2}" y="{MAP_Y0+2}" '
             f'width="{MAP_X1-MAP_X0-4}" height="{MAP_Y1-MAP_Y0-4}" rx="5"/></clipPath>')
    s.append(f'<g clip-path="url(#mapclip)">')

    # sea background
    s.append(f'<rect x="{MAP_X0+2}" y="{MAP_Y0+2}" width="{MAP_X1-MAP_X0-4}" '
             f'height="{MAP_Y1-MAP_Y0-4}" fill="{SEA}"/>')

    # land masses (real coastline, historical style: parchment fill, sepia coast)
    if LAND_PATH:
        s.append(f'<path d="{LAND_PATH}" fill="{LAND}" fill-rule="evenodd" '
                 f'stroke="none"/>')
        # soft coastal shading just inside the coast
        s.append(f'<path d="{LAND_PATH}" fill="none" stroke="#d8c9a0" '
                 f'stroke-width="6" fill-rule="evenodd" opacity="0.55"/>')
        s.append(f'<path d="{LAND_PATH}" fill="none" stroke="{COAST}" '
                 f'stroke-width="1.4" fill-rule="evenodd"/>')

    # graticule (faint, over land + sea)
    lon = math.ceil(LON_MIN / 2) * 2
    while lon <= LON_MAX:
        x, _ = px(lon, LAT_MAX)
        s.append(f'<line x1="{x:.1f}" y1="{MAP_Y0+2}" x2="{x:.1f}" y2="{MAP_Y1-2}" '
                 f'stroke="{GRID}" stroke-width="0.8" opacity="0.4"/>')
        s.append(halo_text(x, MAP_Y1 - 8, f"{lon}°E", 11, INK_SOFT,
                           anchor="middle", halo="#eae1c9", halo_w=2.6))
        lon += 2
    lat = math.ceil(LAT_MIN / 2) * 2
    while lat <= LAT_MAX:
        _, y = px(LON_MIN, lat)
        s.append(f'<line x1="{MAP_X0+2}" y1="{y:.1f}" x2="{MAP_X1-2}" y2="{y:.1f}" '
                 f'stroke="{GRID}" stroke-width="0.8" opacity="0.4"/>')
        s.append(halo_text(MAP_X0 + 6, y - 4, f"{lat}°N", 11, INK_SOFT,
                           anchor="start", halo="#eae1c9", halo_w=2.6))
        lat += 2

    # sea labels
    for (lon_r, lat_r, rot), txt in zip(SEAS_BASE, t["seas"]):
        x, y = px(lon_r, lat_r)
        s.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" '
                 f'font-size="15" letter-spacing="4" fill="{SEA_LABEL}" '
                 f'text-anchor="middle" font-style="italic">{esc(txt)}</text>')

    # region context labels
    for (lon_r, lat_r, rot), txt in zip(REGIONS_BASE, t["regions"]):
        x, y = px(lon_r, lat_r)
        lines = txt.split("\n")
        for i, ln in enumerate(lines):
            s.append(halo_text(x, y + i * 20, ln, 16, LAND_LABEL, anchor="middle",
                               family=SANS, weight="700", ls=3, halo=LAND, halo_w=3.0))

    # excursion connectors (dashed) - under main route
    for a, b in EXCURSIONS:
        xa, ya = px(*COORD[a])
        xb, yb = px(*COORD[b])
        s.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" '
                 f'stroke="{EXCURSION}" stroke-width="3" stroke-dasharray="2 7" '
                 f'stroke-linecap="round" opacity="0.9"/>')

    # main route: halo then line then arrowheads
    pts = [px(*COORD[k]) for k in MAIN_ROUTE]
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    s.append(f'<path d="{d}" fill="none" stroke="{ROUTE_HALO}" stroke-width="8" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{ROUTE}" stroke-width="3.4" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        s.append(arrowhead(x0, y0, x1, y1))

    # excursion end markers (small diamonds) + labels
    exc_label_pos = {
        "bohemia": ("mid", 22),
        "lehavre": ("start", 20),
        "halle": ("end", -12),
    }
    for a, b in EXCURSIONS:
        xb, yb = px(*COORD[b])
        r = 6
        s.append(f'<rect x="{xb-r:.1f}" y="{yb-r:.1f}" width="{2*r}" height="{2*r}" '
                 f'transform="rotate(45 {xb:.1f} {yb:.1f})" fill="{EXC_PIN}" '
                 f'stroke="#fff" stroke-width="1.5"/>')
    # excursion labels
    xb, yb = px(*COORD["bohemia"])
    s.append(halo_text(xb, yb + 24, t["exc"]["bohemia"], 13, EXCURSION,
                       anchor="middle", family=SANS, italic=True, halo=LAND, halo_w=3.0))
    xb, yb = px(*COORD["lehavre"])
    s.append(halo_text(xb - 12, yb + 4, t["exc"]["lehavre"], 13, EXCURSION,
                       anchor="end", family=SANS, italic=True, halo=LAND, halo_w=3.0))
    # (Halle sits in the congested centre where several routes cross; its
    # on-map label is omitted - the legend lists it clearly instead.)

    # main pins + labels
    label_off = {
        "caussade": (17, 6, "start"),
        "stettin": (17, 5, "start"),
        "isenburg": (16, 6, "start"),
        "rotterdam": (-16, 6, "end"),
        "berlin": (17, 22, "start"),
    }
    for i, key in enumerate(MAIN_ROUTE, start=1):
        x, y = px(*COORD[key])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="{PIN}" '
                 f'stroke="#fff" stroke-width="2.5"/>')
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="none" '
                 f'stroke="{PIN_EDGE}" stroke-width="1" opacity="0.4"/>')
        s.append(f'<text x="{x:.1f}" y="{y+5.5:.1f}" font-family="{SANS}" '
                 f'font-size="16" font-weight="700" fill="#fff" '
                 f'text-anchor="middle">{i}</text>')
        dx, dy, anch = label_off[key]
        s.append(halo_text(x + dx, y + dy, t["pins"][key], 18, INK, anchor=anch,
                           family=FONT, weight="700", halo="#f6efdd", halo_w=3.6))

    s.append('</g>')  # end map clip

    # north arrow
    nx, ny = MAP_X1 - 34, MAP_Y0 + 30
    s.append(f'<polygon points="{nx},{ny-16} {nx-7},{ny+6} {nx},{ny} {nx+7},{ny+6}" '
             f'fill="{ROUTE}"/>')
    s.append(f'<text x="{nx}" y="{ny+22}" font-family="{SANS}" font-size="13" '
             f'font-weight="700" fill="{ROUTE}" text-anchor="middle">{t["north"]}</text>')

    # scale bar (200 km)
    bar_px = 200.0 / 111.0 * SCALE
    bx0 = MAP_X0 + 24
    by = MAP_Y1 - 26
    s.append(f'<line x1="{bx0:.1f}" y1="{by}" x2="{bx0+bar_px:.1f}" y2="{by}" '
             f'stroke="{INK}" stroke-width="3"/>')
    for xx in (bx0, bx0 + bar_px):
        s.append(f'<line x1="{xx:.1f}" y1="{by-5}" x2="{xx:.1f}" y2="{by+5}" '
                 f'stroke="{INK}" stroke-width="3"/>')
    s.append(f'<text x="{bx0+bar_px/2:.1f}" y="{by-9:.1f}" font-family="{SANS}" '
             f'font-size="12" fill="{INK}" text-anchor="middle">{t["scalebar"]}</text>')

    # title + subtitle
    s.append(f'<text x="{MAP_X0}" y="46" font-family="{FONT}" font-size="34" '
             f'font-weight="700" fill="{INK}">{esc(t["title"])}</text>')
    s.append(f'<text x="{MAP_X0}" y="72" font-family="{FONT}" font-size="16" '
             f'font-style="italic" fill="{INK_SOFT}">{esc(t["subtitle"])}</text>')

    # legend panel
    lx0 = 812
    s.append(f'<rect x="{lx0}" y="{MAP_Y0}" width="{W-lx0-24}" height="{MAP_Y1-MAP_Y0}" '
             f'fill="{PARCHMENT2}" stroke="{FRAME}" stroke-width="1.5" rx="6"/>')
    tx = lx0 + 20
    y = MAP_Y0 + 34
    s.append(f'<text x="{tx}" y="{y}" font-family="{FONT}" font-size="21" '
             f'font-weight="700" fill="{INK}">{esc(t["legend_head"])}</text>')
    y += 12
    s.append(f'<line x1="{tx}" y1="{y}" x2="{W-40}" y2="{y}" stroke="{FRAME}" '
             f'stroke-width="1"/>')
    y += 24
    import textwrap
    for num, name, meta, desc in t["legend"]:
        is_exc = num == "↳"
        indent = 22 if is_exc else 0
        badge_fill = EXC_PIN if is_exc else PIN
        cx = tx + 12 + indent
        if is_exc:
            r = 6
            s.append(f'<rect x="{cx-r:.1f}" y="{y-6-r:.1f}" width="{2*r}" '
                     f'height="{2*r}" transform="rotate(45 {cx:.1f} {y-6:.1f})" '
                     f'fill="{badge_fill}" stroke="#fff" stroke-width="1.3"/>')
        else:
            s.append(f'<circle cx="{cx:.1f}" cy="{y-6:.1f}" r="12" fill="{badge_fill}" '
                     f'stroke="#fff" stroke-width="2"/>')
            s.append(f'<text x="{cx:.1f}" y="{y-1:.1f}" font-family="{SANS}" '
                     f'font-size="14" font-weight="700" fill="#fff" '
                     f'text-anchor="middle">{num}</text>')
        namecol = INK if not is_exc else "#9a5a12"
        nsize = 17 if not is_exc else 15
        s.append(f'<text x="{tx+34+indent}" y="{y-2:.1f}" font-family="{FONT}" '
                 f'font-size="{nsize}" font-weight="700" fill="{namecol}">'
                 f'{esc(name)}</text>')
        s.append(f'<text x="{W-40}" y="{y-2:.1f}" font-family="{SANS}" font-size="12" '
                 f'fill="{INK_SOFT}" text-anchor="end">{esc(meta)}</text>')
        y += 18
        wrapped = textwrap.wrap(desc, width=54 if is_exc else 58)
        for ln in wrapped:
            s.append(f'<text x="{tx+34+indent}" y="{y:.1f}" font-family="{SANS}" '
                     f'font-size="13" fill="{INK_SOFT}">{esc(ln)}</text>')
            y += 17
        y += 12

    # caption
    s.append(f'<text x="{MAP_X0}" y="{H-16}" font-family="{FONT}" font-size="13.5" '
             f'font-style="italic" fill="{INK_SOFT}">{esc(t["caption"])}</text>')

    s.append('</svg>')
    return "\n".join(s)


def main():
    targets = {"de": "karte-stationen.png", "en": "karte-stationen-en.png"}
    for lang, fname in targets.items():
        svg = build_svg(lang)
        out = os.path.join(DOCS, "images", fname)
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=out,
                         output_width=W * 2, output_height=H * 2)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
