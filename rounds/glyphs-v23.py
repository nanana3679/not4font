"""Draws the five characters of NOT4K one at a time (round v23): four designs for each character, each taking one move
of one letter of the two reference logos (studied letter by letter on the private board) or one idea of our own.
The drawings are flat: silver-grey metal, red lacquer only for the diagonal of the N, a near-black background.
They are given to the generator as the shape to keep (it renders them in chrome), and the page shows them as they
are ("도면").

Units: the cap height is 100, the baseline is y = 0 and y grows upwards. Every design has the same cap height and
the same stroke weights, so that any N can stand next to any O.

Usage: glyphs-v23.py <generation folder> <gallery logo folder>
Writes <generation folder>/w23-<id>-shape.png (1672x941, the reference for the generator), <gallery logo
folder>/gen/w23-<id>-draw.webp (the drawing for the page, transparent around the letter), and
<generation folder>/w23-glyphs.json (where the cap line and the baseline lie in both pictures)."""
import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw

S = 22      # weight of an upright stroke
B = 20      # weight of a crossbar
GAP = 5     # a stencil gap
LINE = 3.5  # the dark line around a piece that lies in front

GROUND = (7, 11, 20)
METAL = (204, 211, 222)
RED = (255, 61, 72)
FACET = (196, 36, 50)
SHADE = (150, 160, 176)


# ---- shapes ---------------------------------------------------------------------------------------------------
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def unit(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def blade(p, q, width, tip_start=0.0, tip_end=0.0, before=0.0, after=0.0):
    """a stroke along p->q, `width` across, its ends square or drawn to a point over `tip_*` units"""
    ux, uy = unit(p, q)
    p = (p[0] - ux * before, p[1] - uy * before)
    q = (q[0] + ux * after, q[1] + uy * after)
    nx, ny = -uy * width / 2, ux * width / 2

    def at(point, along, side):
        return (point[0] + ux * along + nx * side, point[1] + uy * along + ny * side)

    out = [at(p, tip_start, -1), at(q, -tip_end, -1)]
    if tip_end:
        out.append(q)
    out += [at(q, -tip_end, 1), at(p, tip_start, 1)]
    if tip_start:
        out.append(p)
    return out


def clip(poly, a, b, c):
    """keeps the part of a convex polygon where a*x + b*y + c >= 0"""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def keep(poly, p, q, inside):
    """keeps the side of the line through p and q on which the point `inside` lies"""
    a, b = -(q[1] - p[1]), q[0] - p[0]
    c = -(a * p[0] + b * p[1])
    if a * inside[0] + b * inside[1] + c < 0:
        a, b, c = -a, -b, -c
    return clip(poly, a, b, c)


def box(poly, x0=-1e9, y0=-1e9, x1=1e9, y1=1e9):
    for a, b, c in ((1, 0, -x0), (0, 1, -y0), (-1, 0, x1), (0, -1, y1)):
        poly = clip(poly, a, b, c)
    return poly


def offset(poly, distance):
    """moves every edge of a convex polygon outwards by `distance` (a number, or one number per edge)"""
    area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))
    turn = 1 if area > 0 else -1
    count = len(poly)
    ds = distance if isinstance(distance, (list, tuple)) else [distance] * count
    lines = []
    for i in range(count):
        p, q = poly[i], poly[(i + 1) % count]
        ux, uy = unit(p, q)
        nx, ny = uy * turn, -ux * turn  # outwards
        lines.append(((p[0] + nx * ds[i], p[1] + ny * ds[i]), (ux, uy)))
    out = []
    for i in range(count):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def chamfered(x0, y0, x1, y1, corners):
    """a rectangle with some corners cut at 45 degrees: corners maps 'bl', 'br', 'tr', 'tl' to the size of the cut"""
    poly = rect(x0, y0, x1, y1)
    for corner, size in corners.items():
        cx = x0 if corner[1] == 'l' else x1
        cy = y0 if corner[0] == 'b' else y1
        sx = size if corner[1] == 'l' else -size
        sy = size if corner[0] == 'b' else -size
        poly = keep(poly, (cx + sx, cy), (cx, cy + sy), ((x0 + x1) / 2, (y0 + y1) / 2))
    return poly


def octagon(x0, y0, x1, y1, size):
    return chamfered(x0, y0, x1, y1, {'bl': size, 'br': size, 'tr': size, 'tl': size})


# ---- the red diagonal of the N ---------------------------------------------------------------------------------
# Every N has the same two stems and the same line for its diagonal, so that the red always lies at the same angle:
# from above the top left corner of the N to below its bottom right corner.
N_WIDTH = 108
N_SLANT = 30  # how far the diagonal reaches across, measured flat
N_AXIS = ((N_SLANT / 2, 100), (N_WIDTH - N_SLANT / 2, 0))
N_ACROSS = N_SLANT * 100 / math.hypot(N_WIDTH - N_SLANT, 100)  # its weight, measured square to it
N_OUT = 45 * math.hypot(N_WIDTH - N_SLANT, 100) / 100  # along the line, for 45 units of height past each end


def red_blade(width=N_ACROSS, out=N_OUT, tip=30.0):
    return blade(*N_AXIS, width, tip, tip, before=out, after=out)


# ---- the designs -----------------------------------------------------------------------------------------------
# Each design is a list of (layer, polygon). Layers are drawn in this order: metal, hole (cut out of the metal: the
# inside of a letter and the stencil gaps), line (the dark line around a piece in front), red, facet (lines on a
# crystal), shade (a darker line on the metal).
def taper(p, q, w0, w1):
    """a stroke along p->q that is w0 across at p and w1 across at q (0 draws it to a point)"""
    ux, uy = unit(p, q)
    nx, ny = -uy, ux
    out = [(p[0] - nx * w0 / 2, p[1] - ny * w0 / 2), (q[0] - nx * w1 / 2, q[1] - ny * w1 / 2)]
    if w1:
        out.append((q[0] + nx * w1 / 2, q[1] + ny * w1 / 2))
    out.append((p[0] + nx * w0 / 2, p[1] + ny * w0 / 2))
    if w0 == 0:
        out = out[1:]
    return out


# 1 = the spikes of the first reference (its N and T: ends cut along the diagonal, some running past the guide lines;
#     round parts made of chevrons, like its R, D and E)
# 2 = the gaps of the second reference (strokes of one weight, corners cut at 45 degrees, one gap across the middle
#     height of the word, middle parts left floating, like its E, O and S)
# 3 = one move that belongs to that letter only
# 4 = blade ends: every free end of a stroke drawn out to a point, the strokes heaviest where they meet
def n_spike():
    left = keep(rect(0, 0, S, 100), (0, 26), (S, 0), (11, 60))
    right = keep(rect(N_WIDTH - S, 0, N_WIDTH, 130), (N_WIDTH - S, 116), (N_WIDTH, 100), (97, 50))
    return [('metal', left), ('metal', right), ('red', red_blade())]


def n_gap():
    left = chamfered(0, 0, S, 100, {'bl': 14})
    right = chamfered(N_WIDTH - S, 0, N_WIDTH, 100, {'tr': 14})
    red = box(blade(*N_AXIS, N_ACROSS, before=N_OUT + 20, after=N_OUT + 20), y0=-45, y1=145)
    return [('metal', left), ('metal', right), ('hole', rect(-5, 47.5, N_WIDTH + 5, 52.5)),
            ('line', offset(red, GAP)), ('red', red)]


def n_crystal():
    left = chamfered(0, 0, S, 100, {'bl': 6, 'tl': 6})
    right = chamfered(N_WIDTH - S, 0, N_WIDTH, 100, {'tr': 6, 'br': 6})
    out = N_OUT + 12
    shard = blade(*N_AXIS, 33, 40, 40, before=out, after=out)
    p, q = N_AXIS
    ux, uy = unit(p, q)
    ridge = blade((p[0] - ux * out, p[1] - uy * out), (q[0] + ux * out, q[1] + uy * out), 2.4, 6, 6)
    return [('metal', left), ('metal', right), ('line', offset(shard, LINE + 0.5)), ('red', shard), ('facet', ridge)]


def n_blade():
    # the free end of each stem is cut to a long blade point past the guide line: the foot of the left stem down at
    # its outer edge, the top of the right stem up at its outer edge
    left = [(0, 100), (S, 100), (S, 30), (0, -18)]
    right = [(N_WIDTH, 0), (N_WIDTH - S, 0), (N_WIDTH - S, 70), (N_WIDTH, 118)]
    return [('metal', left), ('metal', right), ('red', red_blade(tip=42))]


O_WIDTH = 112


def o_chevron():
    outer = [(0, 50), (24, 0), (O_WIDTH - 24, 0), (O_WIDTH, 50), (O_WIDTH - 24, 100), (24, 100)]
    inner = offset(outer, [-S, -B, -S, -S, -B, -S])
    return [('metal', outer), ('hole', inner)]


def o_ring():
    outer = octagon(0, 0, O_WIDTH, 100, 26)
    # edges from the bottom left corner cut: bottom, bottom right cut, right, top right cut, top, top left cut, left, bottom left cut
    inner = offset(outer, [-B, -21, -S, -21, -B, -21, -S, -21])
    return outer, inner


def o_gap():
    outer, inner = o_ring()
    return [('metal', outer), ('hole', inner), ('hole', rect(-5, 47.5, O_WIDTH + 5, 52.5))]


def o_slashed():
    outer, inner = o_ring()
    ux, uy = unit(*N_AXIS)
    middle = (O_WIDTH / 2, 50)
    cut = blade((middle[0] - ux * 90, middle[1] - uy * 90), (middle[0] + ux * 90, middle[1] + uy * 90), GAP + 1)
    return [('metal', outer), ('hole', inner), ('hole', cut)]


def o_blade():
    half = O_WIDTH / 2 - 2.5
    left = [(half, 100), (24, 100), (0, 50), (24, 0), (half, 0), (34, 19), (23, 50), (34, 81)]
    right = [(O_WIDTH - x, y) for x, y in left]
    return [('metal', left), ('metal', right)]


T_WIDTH = 120


def t_spike():
    bar = [(0, 100), (14, 80), (T_WIDTH + 8, 80), (T_WIDTH - 20, 100)]
    stem = [(49, 80), (49, 4), (71, -14), (71, 80)]
    return [('metal', bar), ('metal', stem)]


def t_gap():
    bar = chamfered(0, 80, 116, 100, {'tl': 14, 'tr': 14})
    stem = chamfered(47, 0, 69, 80, {'bl': 6, 'br': 6})
    return [('metal', bar), ('metal', stem), ('hole', rect(40, 47.5, 76, 52.5))]


def t_float():
    bar = octagon(0, 80, 116, 100, 7)
    stem = keep(keep(rect(47, 0, 69, 74), (47, 63), (58, 74), (58, 30)), (58, 74), (69, 63), (58, 30))
    return [('metal', bar), ('metal', stem)]


def t_blade():
    bar = [(0, 100), (126, 100), (96, 80), (30, 80)]
    stem = [(52, 81), (74, 81), (74, 26), (63, -18), (52, 26)]
    return [('metal', bar), ('metal', stem)]


def four_diagonal(stem_x=72, bar_bottom=18, weight=S):
    """the diagonal of a plain 4, from the left end of the crossbar to the top of the stem"""
    outer_from, outer_to = (0, bar_bottom), (stem_x, 100)
    ux, uy = unit(outer_from, outer_to)
    nx, ny = uy, -ux  # towards the inside of the 4
    axis = ((outer_from[0] + nx * weight / 2, outer_from[1] + ny * weight / 2), (outer_to[0] + nx * weight / 2, outer_to[1] + ny * weight / 2))
    return blade(*axis, weight, before=40, after=40)


def four_spike():
    diagonal = box(four_diagonal(), x0=0, y0=18, x1=94)
    # the top is cut along the diagonal of the N, so that it runs to a point a little above the cap line
    diagonal = keep(diagonal, (80, 110), (94, 99), (60, 60))
    bar = [(0, 18), (114, 18), (100, 38), (0, 38)]
    stem = keep([(72, 100), (72, 4), (94, -14), (94, 120)], (80, 110), (94, 99), (83, 50))
    return [('metal', diagonal), ('metal', bar), ('metal', stem)]


def four_gap():
    chamfer = ((0, 30), (12, 18))
    diagonal = keep(box(four_diagonal(), x0=0, y0=18, x1=72 - GAP, y1=100), *chamfer, (40, 40))
    bar = chamfered(0, 18, 72 - GAP, 38, {'bl': 12})
    # no stub of the crossbar right of the stem: standing apart, it read as a full stop between the 4 and the K
    stem = chamfered(72, 0, 94, 100, {'tr': 12})
    return [('metal', diagonal), ('metal', bar), ('metal', stem), ('hole', rect(68, 47.5, 98, 52.5))]


def four_square():
    upright = chamfered(0, 26, S, 100, {'tl': 8})
    bar = chamfered(0, 26, 106, 46, {'bl': 8})
    stem = chamfered(66, 0, 88, 100, {'tr': 8})
    return [('metal', upright), ('metal', bar), ('metal', stem)]


def four_blade():
    diagonal = box(four_diagonal(), x0=0, y0=18, x1=94, y1=100)
    bar = [(0, 18), (126, 18), (98, 38), (0, 38)]
    stem = [(72, 100), (94, 100), (94, 26), (83, -18), (72, 26)]
    return [('metal', diagonal), ('metal', bar), ('metal', stem)]


K_WIDTH = 104


def k_arms(vertex, width=K_WIDTH, weight=S):
    arm = box(blade(vertex, (width + 6, 104), weight, before=8, after=10), x0=0, x1=width, y1=100)
    leg = box(blade(vertex, (width + 6, -4), weight + 2, before=8, after=10), x0=0, x1=width, y0=0)
    return arm, leg


def k_spike():
    stem = keep(rect(0, -16, S, 100), (S, 6), (0, -16), (11, 50))
    arm, leg = k_arms((12, 50))
    return [('metal', stem), ('metal', arm), ('metal', leg)]


def k_gap():
    stem = chamfered(0, 0, S, 100, {'tl': 12, 'bl': 12})
    arm, leg = k_arms((24, 50))
    arm = box(arm, x0=S + GAP, y0=52.5)
    leg = box(leg, x0=S + GAP, y1=47.5)
    return [('metal', stem), ('hole', rect(-5, 47.5, S + 5, 52.5)), ('metal', arm), ('metal', leg)]


def k_apart():
    stem = chamfered(0, 0, S, 100, {'tl': 6, 'bl': 6})
    tip = (S + 6, 50)
    weight = 20
    top, bottom = (K_WIDTH - 12, 100), (K_WIDTH - 12, 0)
    au, bu = unit(tip, top), unit(tip, bottom)
    inner_x = tip[0] + weight / abs(au[1])
    arm = box([tip, top, (top[0] + weight / abs(au[1]), 100), (inner_x, 50)], x1=K_WIDTH)
    leg = box([tip, (inner_x, 50), (bottom[0] + weight / abs(bu[1]), 0), bottom], x1=K_WIDTH)
    return [('metal', stem), ('metal', arm), ('metal', leg)]


def k_blade():
    stem = [(0, 100), (S, 100), (S, 26), (S / 2, -18), (0, 26)]
    arm = box(blade((12, 50), (K_WIDTH + 14, 112), S, 0, 34, before=8), x0=0, x1=K_WIDTH + 20)
    leg = box(blade((12, 50), (K_WIDTH + 24, -28), S + 2, 0, 40, before=8), x0=0)
    return [('metal', stem), ('metal', arm), ('metal', leg)]


# label, id, the character, the design
DESIGNS = [
    ('N-1', 'n1', 'N', n_spike), ('N-2', 'n2', 'N', n_gap), ('N-3', 'n3', 'N', n_crystal), ('N-4', 'n4', 'N', n_blade),
    ('O-1', 'o1', 'O', o_chevron), ('O-2', 'o2', 'O', o_gap), ('O-3', 'o3', 'O', o_slashed), ('O-4', 'o4', 'O', o_blade),
    ('T-1', 't1', 'T', t_spike), ('T-2', 't2', 'T', t_gap), ('T-3', 't3', 'T', t_float), ('T-4', 't4', 'T', t_blade),
    ('4-1', 'f1', '4', four_spike), ('4-2', 'f2', '4', four_gap), ('4-3', 'f3', '4', four_square), ('4-4', 'f4', '4', four_blade),
    ('K-1', 'k1', 'K', k_spike), ('K-2', 'k2', 'K', k_gap), ('K-3', 'k3', 'K', k_apart), ('K-4', 'k4', 'K', k_blade),
]

ORDER = ['metal', 'hole', 'line', 'red', 'facet', 'shade']


def extent(parts):
    xs = [p[0] for _, poly in parts for p in poly]
    ys = [p[1] for _, poly in parts for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def body_width(parts):
    xs = [p[0] for layer, poly in parts if layer in ('metal', 'red') for p in poly if -1 <= p[1] <= 101]
    return min(xs), max(xs)


def render(parts, size, scale, origin, transparent, supersample=4):
    """origin: where (0, 0) of the drawing lands, in pixels of the picture"""
    w, h = size[0] * supersample, size[1] * supersample
    k = scale * supersample

    def px(poly):
        return [(origin[0] * supersample + x * k, origin[1] * supersample - y * k) for x, y in poly]

    colour = Image.new('RGB', (w, h), METAL if transparent else GROUND)
    ink = Image.new('L', (w, h), 0)
    paint, mask = ImageDraw.Draw(colour), ImageDraw.Draw(ink)
    for layer in ORDER:
        for name, poly in parts:
            if name != layer or len(poly) < 3:
                continue
            if layer == 'metal':
                paint.polygon(px(poly), fill=METAL)
                mask.polygon(px(poly), fill=255)
            elif layer in ('hole', 'line'):
                paint.polygon(px(poly), fill=METAL if transparent else GROUND)
                mask.polygon(px(poly), fill=0)
            elif layer == 'red':
                paint.polygon(px(poly), fill=RED)
                mask.polygon(px(poly), fill=255)
            elif layer == 'facet':
                paint.polygon(px(poly), fill=FACET)
            elif layer == 'shade':
                paint.polygon(px(poly), fill=SHADE)
    colour = colour.resize(size, Image.LANCZOS)
    ink = ink.resize(size, Image.LANCZOS)
    if not transparent:
        return colour
    picture = colour.convert('RGBA')
    picture.putalpha(ink)
    return picture


def main():
    proto, logo = Path(sys.argv[1]), Path(sys.argv[2])
    (logo / 'gen').mkdir(parents=True, exist_ok=True)
    SHAPE_SIZE, SHAPE_SCALE = (1672, 941), 3.9
    DRAW_SCALE, MARGIN = 1.7, 14
    records = []
    for label, ident, character, design in DESIGNS:
        parts = design()
        x0, y0, x1, y1 = extent(parts)
        left, right = body_width(parts)
        # the reference for the generator: every letter at the same size, the middle of its body in the middle
        origin = (SHAPE_SIZE[0] / 2 - (left + right) / 2 * SHAPE_SCALE, SHAPE_SIZE[1] / 2 + 50 * SHAPE_SCALE)
        render(parts, SHAPE_SIZE, SHAPE_SCALE, origin, False).save(proto / f'w23-{ident}-shape.png')
        # the drawing for the page: only as large as the letter with a margin, transparent around it
        size = (round((x1 - x0) * DRAW_SCALE + 2 * MARGIN), round((y1 - y0) * DRAW_SCALE + 2 * MARGIN))
        draw_origin = (MARGIN - x0 * DRAW_SCALE, MARGIN + y1 * DRAW_SCALE)
        render(parts, size, DRAW_SCALE, draw_origin, True).save(logo / 'gen' / f'w23-{ident}-draw.webp', lossless=True)
        records.append({
            'label': label, 'id': ident, 'character': character,
            'shape': {'size': SHAPE_SIZE, 'cap': origin[1] - 100 * SHAPE_SCALE, 'base': origin[1],
                      'box': [origin[0] + x0 * SHAPE_SCALE, origin[1] - y1 * SHAPE_SCALE, origin[0] + x1 * SHAPE_SCALE, origin[1] - y0 * SHAPE_SCALE]},
            'draw': {'size': size, 'cap': draw_origin[1] - 100 * DRAW_SCALE, 'base': draw_origin[1]},
        })
    (proto / 'w23-glyphs.json').write_text(json.dumps(records, indent=1) + '\n')
    print(len(records), 'designs')


if __name__ == '__main__':
    main()
