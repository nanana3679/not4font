"""Draws the three concepts of round v25 as black SVG wordmarks (logo-design skill, phase 4: black first, no finish).
The brief: heavy, mechanical, interlocking, cybernetic, combative; a large title only (the icon does the small
sizes); its lettering may later seed the in-game typeface, so every concept is a rule that other letters can follow.
Kept from before: red only on the diagonal of the N, sticking out past both ends; the channel between the T and the
4 in which the lit slash stands; a plain 4 that never reads as A; a plain K; no outline and no plate.

  A billet   NOT4K milled out of one heavy block: weight 30, the letters parted only by narrow channels of one width
  B joints   every stroke a rigid segment and every junction an octagonal pin joint, like an articulated arm
  C keys     each letter locks into the next by an arrow-headed key at half height; only the T and the 4 stay apart,
             parted by the channel of the lit slash

Units: the cap height is 100, the baseline is y = 0, y grows upwards. Needs shapely (PYTHONPATH to a folder that
has it). Usage: concepts-v25.py <out folder>"""
import importlib.util
import json
import math
import sys
from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

spec = importlib.util.spec_from_file_location('glyphs', Path(__file__).parent / 'glyphs-v23.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
rect, blade, keep, box, offset = G.rect, G.blade, G.keep, G.box, G.offset

TAN = 100 / 78                      # every diagonal lies at the angle of the red diagonal of the N
SIN, COS = TAN / math.hypot(1, TAN), 1 / math.hypot(1, TAN)
RUN = 1 / TAN
UP, DOWN = (COS, SIN), (COS, -SIN)
UPPER_LEFT, LOWER_RIGHT = (-SIN, COS), (SIN, -COS)
SLASH_WEIGHT, SLASH_ROOM = 10, 6
CHANNEL = SLASH_ROOM * 2 + SLASH_WEIGHT
INK, RED = '#111111', '#ff3d48'


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def P(points):
    return Polygon(points).buffer(0)


def octagon_at(centre, radius):
    return P([(centre[0] + radius * math.cos(math.radians(22.5 + 45 * i)), centre[1] + radius * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)])


def red_crystal(axis, width, out=G.N_OUT + 12, tip=40):
    return P(blade(*axis, width, tip, tip, before=out, after=out))


def channel(x4, bar_bottom):
    """the channel of the lit slash: the outer edge of the diagonal of the 4 runs up to the right from (x4, bar_bottom);
    returns the middle line of the slash and a point on the far wall"""
    foot = (x4, bar_bottom)
    return add(foot, UPPER_LEFT, SLASH_ROOM + SLASH_WEIGHT / 2), add(foot, UPPER_LEFT, CHANNEL)


def wall_side(poly_points, wall, inside):
    return keep(poly_points, wall, add(wall, UP, 100), inside)


def at_height(point, direction, y):
    return add(point, direction, (y - point[1]) / direction[1])


def four(x4, bar, weight, stem_w, arm, flat_foot=True):
    """a plain 4 whose diagonal leaves (x4, bar[0]) at the angle of the red diagonal; bar = (bottom, top)"""
    stem_x = x4 + (100 - bar[0]) * RUN
    axis_start = add((x4, bar[0]), LOWER_RIGHT, weight / 2)
    diagonal = box(blade(axis_start, add(axis_start, UP, 160), weight, before=40), y0=bar[0], y1=100, x1=stem_x + stem_w)
    crossbar = keep(rect(x4 - 40, bar[0], stem_x + stem_w + arm, bar[1]), (x4, bar[0]), (stem_x, 100), (stem_x, bar[0] + 5))
    stem = rect(stem_x, 0, stem_x + stem_w, 100)
    return [P(diagonal), P(crossbar), P(stem)], stem_x


def t_letter(stem_x, stem_w, bar, wall, left_cut):
    inside = (stem_x + stem_w / 2, (bar[0] + bar[1]) / 2)
    crossbar = wall_side(rect(stem_x - 120, bar[0], stem_x + 160, bar[1]), wall, inside)
    if left_cut:
        crossbar = keep(crossbar, left_cut[0], left_cut[1], inside)
    stem = wall_side(rect(stem_x, 0, stem_x + stem_w, bar[0] + 1), wall, (stem_x + 3, bar[0] - 5))
    return [P(crossbar), P(stem)]


def k_kors(x, weight, gap):
    """the K of the shared logo: the top of the stem cut along \\ into a V with the arm; the leg leaves from under the
    arm behind a narrow gap"""
    stem = keep(rect(x, 0, x + weight, 100), (x, 100), (x + weight, 100 - weight * TAN), (x + weight / 2, 30))
    vertex = (x + weight, 40)
    arm_axis = add(vertex, UPPER_LEFT, weight / 2)
    arm = box(blade(arm_axis, add(arm_axis, UP, 120), weight, before=40), x0=x, y1=100)
    gap_at = add(vertex, LOWER_RIGHT, gap)
    leg_axis = (x + weight + 24, 42)
    leg = box(blade(add(leg_axis, DOWN, -60), add(leg_axis, DOWN, 120), weight), y0=0)
    leg = keep(leg, gap_at, add(gap_at, UP, 50), (x + weight + 60, 5))
    return [P(stem), P(arm), P(leg)]


# ---- A billet --------------------------------------------------------------------------------------------------
def concept_a(k_builder=None, four_arm=16, o_width=120, bar4=(10, 34), arm_mode='out', seam=4, red_width=33, nest_n=False, n_foot=False, n_top=False, n_top_sweep=False, n_triangle=False, o_shift=0, o_cut_for_sweep=False, o_corners=None, nest_ox=None, o_height=100, o_cut_square=False):
    """arm_mode says what the crossbar of the 4 does on its right (round v29):
      out    it sticks out `four_arm` past the stem of the 4 (rounds v25 to v28)
      over   it runs on across the stem of the K and lies in front of it, a dark seam of `seam` above and below
      stand  as over, but the stem of the K stops above it: the K stands on the crossbar of the 4
      merge  it runs on into the stem of the K, joined to it"""
    S, B, GAP = 30, 26, 6
    ink = []
    # N: two stems; the red crystal from above its top left corner to below its bottom right corner
    n_width = 120
    ox, ow, cut = n_width + GAP + o_shift, o_width, 26
    # o_corners (round v36): how far each corner of the O runs along the baseline or the cap line, as (bottom left,
    # bottom right, top right, top left); every corner is `cut` tall. By default each runs cut * RUN, so that it lies
    # at the angle of the red diagonal; a run of `cut` lays it at 45 degrees
    run_bl, run_br, run_tr, run_tl = o_corners or (cut * RUN,) * 4
    # o_height (round v38): how tall the O is; it stands on the baseline and its corners stay `cut` tall
    oh = o_height
    tl_a, tl_b = (ox, oh - cut), (ox + run_tl, oh)
    tl_long = math.hypot(run_tl, cut)
    tl_along, tl_out = (run_tl / tl_long, cut / tl_long), (-cut / tl_long, run_tl / tl_long)
    n_right = rect(n_width - S, 0, n_width, 100)
    if nest_n:
        # nest_n (round v31). Meant to cut the top right corner of the right stem of the N parallel to the top left
        # corner of the O; in fact the line, GAP from that corner, crosses the stem from (90, 37.6) to (120, 76.1) and
        # the side kept is the one above it, so only the top of the stem is left, its foot cut along that line. The
        # user liked the stem cut this way (turned, the N reads like a 4) and it was kept (round v32).
        # nest_ox (round v36): where the O stood when the cut was made, so that the stem no longer follows the O
        # the cut is laid against the corner of an O of full height, so that it does not follow the height either
        nest_x = ox if nest_ox is None else nest_ox
        nest_a, nest_b = (nest_x, 100 - cut), (nest_x + run_tl, 100)
        n_right = keep(n_right, add(nest_a, tl_out, GAP), add(nest_b, tl_out, GAP), (n_width - S + 5, 50))
    ink += [P(rect(0, 0, S, 100)), P(n_right)]
    if n_foot:
        # n_foot (round v32): the foot of the left stem of the N sweeps left along the baseline, the mirror of the
        # sweep of the leg of the K at the other end of the word: from 20 up its outer edge, 30 degrees down to a point
        ink.append(P([(0, 20), (-20 / math.tan(math.radians(30)), 0), (10, 0), (10, 20)]))
    if n_top:
        # n_top (round v32): a pointed ornament on the top of the right stem of the N, rising up and to the right above
        # the cap line (to the right along the cap line it would run into the O)
        ink.append(P([(n_width - S + 12, 100), (n_width, 100), (n_width + 12, 128)]))
    if n_top_sweep:
        # n_top_sweep (round v33): the sweep of the foot turned half a turn about the middle of the N, so that the top
        # right of the N is its mirror: from 80 down its outer edge, 30 degrees up to a point on the cap line
        ink.append(P([(n_width, 80), (n_width + 20 / math.tan(math.radians(30)), 100), (n_width - 10, 100), (n_width - 10, 80)]))
    if n_triangle:
        # n_triangle (round v33): the right stem of the N fills the cut top left corner of the O: its outer edge runs
        # GAP from that corner, parallel to it, from where it leaves the inner edge of the stem up to the cap line, so
        # that the stem becomes a triangle
        edge = add(tl_a, tl_out, GAP)
        inner_x = n_width - S
        low = add(edge, tl_along, (inner_x - edge[0]) / tl_along[0])
        high = add(edge, tl_along, (oh - edge[1]) / tl_along[1])
        ink[1] = P([low, high, (inner_x, 100)])
    red = red_crystal(((21, 100), (99, 0)), red_width)
    # O: an octagon with upright sides, its corners cut at the angle of the red diagonal
    outer = [(ox + run_bl, 0), (ox + ow - run_br, 0), (ox + ow, cut), (ox + ow, oh - cut), (ox + ow - run_tr, oh), (ox + run_tl, oh), (ox, oh - cut), (ox, cut)]
    corner = S * 0.93
    inner = offset(outer, [-B, -corner, -S, -corner, -B, -corner, -S, -corner])
    if o_cut_square:
        # o_cut_square (round v40): before the top left of the O is cut under the sweep, that corner is made square,
        # so that the left side runs straight up to the cut and the channel turns once, keeping its width of GAP
        # (otherwise a little of the corner stays and the channel is wider where the stem meets the sweep)
        squared = outer[:5] + [(ox, oh)] + outer[7:]
        o_ring = P(squared).difference(P(inner))
    else:
        o_ring = P(outer).difference(P(inner))
    if o_cut_for_sweep:
        # o_cut_for_sweep (round v34): the top left of the O is cut GAP below the lower edge of the sweep at the top
        # right of the N (30 degrees from (n_width, 80)), so that the sweep lies over the O with one channel between
        start = add((n_width, 80), (math.sin(math.radians(30)), -math.cos(math.radians(30))), GAP)
        along = (math.cos(math.radians(30)), math.sin(math.radians(30)))
        far = add(start, along, 400)
        above = P([add(start, along, -100), far, (far[0], 300), (start[0] - 200, 300)])
        o_ring = o_ring.difference(above)
    ink.append(o_ring)
    # T: the left end of its crossbar cut parallel to the top right corner of the O; its stem GAP past the O
    stem_x = ox + ow + GAP
    corner_a, corner_b = (ox + ow, oh - cut), (ox + ow - run_tr, oh)
    tr_long = math.hypot(run_tr, cut)
    normal = (cut / tr_long, run_tr / tr_long)
    left_cut = (add(corner_a, normal, GAP), add(corner_b, normal, GAP))
    # the wall of the channel passes through the bottom left corner of the T, which fixes where the 4 stands
    x4 = stem_x + (CHANNEL * SIN) + (bar4[0] + CHANNEL * COS) * RUN
    middle, wall = channel(x4, bar4[0])
    ink += t_letter(stem_x, S, (100 - B, 100), wall, left_cut)
    crossing_k = arm_mode in ('over', 'stand', 'merge')
    arm = (GAP + S) if crossing_k else four_arm
    pieces, stem4 = four(x4, bar4, 26, S, arm)
    kx = stem4 + S + (0 if crossing_k else four_arm) + GAP
    k_pieces = (k_builder or k_kors)(kx, S, GAP)
    if arm_mode in ('over', 'stand'):
        crossing = P(rect(stem4 + S, bar4[0], kx + S, bar4[1])).buffer(seam, join_style='mitre')
        if arm_mode == 'stand':
            crossing = unary_union([crossing, P(rect(kx, -10, kx + S, bar4[1] + seam))])
        crossing = crossing.intersection(P(rect(kx, -10, kx + S, 110)))
        k_pieces = [piece.difference(crossing) for piece in k_pieces]
    ink += pieces + k_pieces
    return finish(ink, red, middle, 'A')


# ---- B joints --------------------------------------------------------------------------------------------------
def concept_b():
    S, B, GAP, HUB, PIN = 22, 20, 10, 16, 5
    ink, hubs = [], []
    # N: stems 78 apart so that the red limb between the joints at their ends lies at the angle of the family
    ink += [P(rect(0, 0, S, 100)), P(rect(78, 0, 100, 100))]
    hub1, hub2 = (11, 100), (89, 0)
    red = red_crystal((hub1, hub2), 24, out=57, tip=30)
    hubs += [hub1, hub2]
    # O: the six-sided ring with its four flanks at the angle, joints at its two side points
    ox, ow = 100 + GAP + 6, 128
    run = 50 * RUN
    outer = [(ox, 50), (ox + run, 0), (ox + ow - run, 0), (ox + ow, 50), (ox + ow - run, 100), (ox + run, 100)]
    inner = offset(outer, [-S, -B, -S, -S, -B, -S])
    ink.append(P(outer).difference(P(inner)))
    hubs += [(ox + 13, 50), (ox + ow - 13, 50)]
    # T: a joint where the stem meets the crossbar; the crossbar cut parallel to the upper right flank of the O
    stem_x = ox + ow + 18
    flank_a, flank_b = (ox + ow, 50), (ox + ow - run, 100)
    normal = (SIN, COS)
    left_cut = (add(flank_a, normal, GAP), add(flank_b, normal, GAP))
    bar4 = (18, 38)
    x4 = stem_x + CHANNEL * SIN + (bar4[0] + CHANNEL * COS) * RUN
    middle, wall = channel(x4, bar4[0])
    ink += t_letter(stem_x, S, (80, 100), wall, left_cut)
    hubs.append((stem_x + S / 2, 90))
    pieces, stem4 = four(x4, bar4, S, S, 18)
    ink += pieces
    hubs.append((stem4 + S / 2, 100))
    # K: arm and leg leave a joint on the right edge of the stem
    kx = stem4 + S + 18 + GAP
    ink.append(P(rect(kx, 0, kx + S, 100)))
    vertex = (kx + S / 2, 50)
    arm = box(blade(vertex, add(vertex, UP, 120), S), y1=100, x0=kx)
    leg = box(blade(vertex, add(vertex, DOWN, 120), S + 2), y0=0, x0=kx)
    ink += [P(arm), P(leg)]
    hubs.append((kx + S, 50))
    hub_shapes = [octagon_at(c, HUB) for c in hubs]
    pins = [octagon_at(c, PIN) for c in hubs]
    return finish(ink, red, middle, 'B', front=hub_shapes, holes=pins)


# ---- C keys ----------------------------------------------------------------------------------------------------
def key_shape(x_edge):
    """a dovetail key that leaves an upright edge at x_edge, at half height: narrow where it leaves its letter and
    wider at its square end, so that it cannot be pulled out of the slot of the next letter (the joint of a dovetail
    slide, as on a machine tool). An arrowhead read as an arrow sign."""
    root, length = 7, 22
    end = root + (length + 2) * math.tan(math.radians(15))   # its sides, from 2 inside its letter, at exactly 15 degrees
    return P([(x_edge - 2, 50 - root), (x_edge + length, 50 - end), (x_edge + length, 50 + end), (x_edge - 2, 50 + root)])


def concept_c():
    S, B, GAP, CLEAR = 22, 20, 7, 3.5
    ink, keys = [], []
    n_width = 108
    ink += [P(rect(0, 0, S, 100)), P(rect(n_width - S, 0, n_width, 100))]
    red = red_crystal(G.N_AXIS, 33)
    keys.append(key_shape(n_width))
    ox, ow, cut = n_width + GAP, 116, 20
    outer = [(ox + cut * RUN, 0), (ox + ow - cut * RUN, 0), (ox + ow, cut), (ox + ow, 100 - cut), (ox + ow - cut * RUN, 100), (ox + cut * RUN, 100), (ox, 100 - cut), (ox, cut)]
    inner = offset(outer, [-B, -S * 0.93, -S, -S * 0.93, -B, -S * 0.93, -S, -S * 0.93])
    ink.append(P(outer).difference(P(inner)))
    keys.append(key_shape(ox + ow))
    stem_x = ox + ow + GAP
    corner_a, corner_b = (ox + ow, 100 - cut), (ox + ow - cut * RUN, 100)
    normal = (SIN, COS)
    left_cut = (add(corner_a, normal, GAP), add(corner_b, normal, GAP))
    bar4 = (18, 38)
    x4 = stem_x + CHANNEL * SIN + (bar4[0] + CHANNEL * COS) * RUN
    middle, wall = channel(x4, bar4[0])
    ink += t_letter(stem_x, S, (80, 100), wall, left_cut)
    pieces, stem4 = four(x4, bar4, S, S, 0)
    ink += pieces
    keys.append(key_shape(stem4 + S))
    kx = stem4 + S + GAP
    ink.append(P(rect(kx, 0, kx + S, 100)))
    vertex = (kx + S, 50)
    arm_axis = add(vertex, UPPER_LEFT, S / 2)
    arm = box(blade(arm_axis, add(arm_axis, UP, 120), S, before=30), y1=100, x0=kx)
    leg_axis = add(vertex, (-SIN, -COS), S / 2)
    leg = box(blade(leg_axis, add(leg_axis, DOWN, 120), S + 2, before=30), y0=0, x0=kx)
    ink += [P(arm), P(leg)]
    # every key cuts its slot, with a little room, out of the letter it enters, then lies in it
    slots = [k.buffer(CLEAR, join_style='mitre') for k in keys]
    return finish(ink, red, middle, 'C', cut_first=slots, front=keys)


def finish(ink, red, middle, name, front=(), holes=(), cut_first=()):
    body = unary_union(ink)
    for slot in cut_first:
        body = body.difference(slot)
    body = body.difference(red.buffer(4.5, join_style='mitre'))
    red_shape = red
    for piece in front:
        body = body.difference(piece.buffer(3.5, join_style='mitre'))
        red_shape = red_shape.difference(piece.buffer(3.5, join_style='mitre'))
    body = unary_union([body] + list(front))
    for hole in holes:
        body = body.difference(hole)
        red_shape = red_shape.difference(hole)
    slash = [at_height(middle, UP, -30), at_height(middle, UP, 130)]
    return {'name': name, 'ink': body, 'red': red_shape, 'slash': slash}


def path_of(geometry, to_svg):
    polys = list(geometry.geoms) if isinstance(geometry, MultiPolygon) else [geometry]
    parts = []
    for poly in polys:
        for ring in [poly.exterior] + list(poly.interiors):
            points = [to_svg(x, y) for x, y in list(ring.coords)[:-1]]
            parts.append('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in points) + ' Z')
    return ' '.join(parts)


def write(concept, folder, colour=True, slash=False):
    ink, red = concept['ink'], concept['red']
    x0, y0, x1, y1 = unary_union([ink, red]).bounds
    pad = 12
    width, height = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad

    def to_svg(x, y):
        return x - x0 + pad, y1 - y + pad

    red_fill = RED if colour else '#7d828c'
    extra = ''
    if slash:
        (fx, fy), (hx, hy) = concept['slash']
        a, b = to_svg(fx, fy), to_svg(hx, hy)
        extra = f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="#9fe9ff" stroke-width="{SLASH_WEIGHT}" stroke-linecap="butt"/>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" width="{width:.0f}" height="{height:.0f}">'
           f'<title>NOT4K concept {concept["name"]}</title>'
           f'<path fill="{INK}" fill-rule="evenodd" d="{path_of(ink, to_svg)}"/>'
           f'<path fill="{red_fill}" fill-rule="evenodd" d="{path_of(red, to_svg)}"/>{extra}</svg>\n')
    suffix = ('' if colour else '-grey') + ('-slash' if slash else '')
    out = folder / f'concept-{concept["name"].lower()}{suffix}.svg'
    out.write_text(svg)
    return out, (width, height), (x0, y1, pad)


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    record = []
    for build in (concept_a, concept_b, concept_c):
        concept = build()
        out, size, frame = write(concept, folder)
        write(concept, folder, colour=False)
        write(concept, folder, slash=True)
        record.append({'name': concept['name'], 'svg': out.name, 'size': size, 'slash': concept['slash'], 'frame': frame})
        print(concept['name'], out.name, [round(v) for v in size], 'pieces', len(concept['ink'].geoms) if isinstance(concept['ink'], MultiPolygon) else 1)
    (folder / 'concepts.json').write_text(json.dumps(record, indent=1) + '\n')


if __name__ == '__main__':
    main()
