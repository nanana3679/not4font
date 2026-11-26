"""Round v57: the whole set drawn from one set of weights, so that the font can have a Regular beside the Bold. The
user: the logo keeps its red at 30 ("로고는 지금이나은듯"), and "안굵은버전도" (a version that is not bold).
Every letter follows the rules of the Bold; only these numbers change with the weight:
  s   stems                         Bold 30
  h   horizontals that stack         Bold 24 (E, F, S, B, 2, 3, 5, 6, 8, 9, bowls below, crossbars, arms)
  ho  horizontals of the O family    Bold 26 (O, C, G, D, Q, U, J, 0, T, the top of bowls)
  d   diagonals, across              Bold 26
  g   gaps of stencils               Bold 6
  sp  space between letters          Bold 6 (the least distance between neighbours); the arm of the 4 runs on by it
Corners stay cut 26 tall at 52 degrees in every weight, so the outlines keep their shape; widths that hold the
angle of 52 degrees (N, M, V, X, Y, Z, A) follow from the stems.
With the Bold numbers this redraws the Bold of round v56 (checked letter by letter). Writes three Regular weights
to choose from (stems 14, 16, 18), each as the set, the judgment words and a few words of the interface.
Needs shapely (PYTHONPATH). Usage: font-v57.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import rotate, scale, translate
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load('c25', 'concepts-v25.py')
B42 = load('b42', 'base-v42.py')
B44 = load('b44', 'base-v44.py')
P, rect, offset, blade, box, keep, add = C.P, C.rect, C.offset, C.blade, C.box, C.keep, C.add
RUN, SIN = C.RUN, C.SIN
CUT = 26
R = CUT * RUN


class Weight:
    def __init__(self, name, s, h, ho, d, g, sp):
        self.name, self.s, self.h, self.ho, self.d, self.g, self.sp = name, s, h, ho, d, g, sp
        self.corner = s * 0.93
        self.ac = d / SIN                                 # a diagonal measured along a horizontal
        self.m0, self.m1 = 50 - h / 2, 50 + h / 2         # the middle bar
        self.bowl0 = 50 - h / 2 - 4                       # where the bowl of P and R begins


BOLD = Weight('bold', 30, 24, 26, 26, 6, 6)
REGULARS = [Weight('r14', 14, 12, 13, 12, 4, 12), Weight('r16', 16, 14, 15, 14, 4, 12), Weight('r18', 18, 16, 17, 16, 5, 12)]


def ring(w, width, y0, y1, top, bottom):
    outer = [(R, y0), (width - R, y0), (width, y0 + CUT), (width, y1 - CUT), (width - R, y1), (R, y1), (0, y1 - CUT), (0, y0 + CUT)]
    inner = offset(outer, [-bottom, -w.corner, -w.s, -w.corner, -top, -w.corner, -w.s, -w.corner])
    return P(outer).difference(P(inner))


def bowl(w, width, y0, y1, bottom, top):
    outer = [(0, y0), (width - R, y0), (width, y0 + CUT), (width, y1 - CUT), (width - R, y1), (0, y1)]
    inner = offset(outer, [-bottom, -w.corner, -w.s, -w.corner, -top, -w.s])
    return P(outer).difference(P(inner))


def u_ring(w, width):
    outer = [(0, 100), (0, CUT), (R, 0), (width - R, 0), (width, CUT), (width, 100)]
    inner = offset(outer, [-w.s, -w.corner, -w.ho, -w.corner, -w.s, 10])
    return P(outer).difference(P(inner))


def arm(x_end, y0, y1):
    return P([(0, y0), (0, y1), (x_end, y1), (x_end - (y1 - y0) * RUN, y0)])


def band(bottom, top):
    (b0, b1, yb), (t0, t1, yt) = bottom, top
    return P([(b0, yb), (b1, yb), (t1, yt), (t0, yt)])


def stem(w, x=0):
    return P(rect(x, 0, x + w.s, 100))


def g_a(w):
    run = 100 * RUN
    axis = add((0, 0), C.LOWER_RIGHT, w.d / 2)
    diagonal = P(box(blade(axis, add(axis, C.UP, 160), w.d, before=40), y0=0, y1=100, x1=run + w.s))
    b0, b1 = 25 - w.h / 2, 25 + w.h / 2
    crossbar = P(keep(rect(-40, b0, run + w.s, b1), (0, 0), (run, 100), (run, 5)))
    return unary_union([diagonal, crossbar, stem(w, run)])


def g_b(w, width=96):
    return unary_union([bowl(w, width, w.m0, 100, w.h, w.h), bowl(w, width, 0, w.m1, w.h, w.h), stem(w)])


def g_c(w, width=96):
    return ring(w, width, 0, 100, w.ho, w.ho).difference(P(rect(width / 2, w.ho, width + 1, 100 - w.ho)))


def g_d(w, width=100):
    outer = [(0, 0), (width - R, 0), (width, CUT), (width, 100 - CUT), (width - R, 100), (0, 100)]
    inner = offset(outer, [-w.ho, -w.corner, -w.s, -w.corner, -w.ho, -w.s])
    return P(outer).difference(P(inner))


def g_e(w, width=84):
    return unary_union([stem(w), arm(width, 100 - w.h, 100), arm(width - 8, w.m0, w.m1), arm(width, 0, w.h)])


def g_f(w, width=82):
    return unary_union([stem(w), arm(width, 100 - w.h, 100), arm(width - 8, w.m0, w.m1)])


def g_g(w, width=104):
    body = ring(w, width, 0, 100, w.ho, w.ho).difference(P(rect(width / 2, w.m1, width + 1, 100 - w.ho)))
    return unary_union([body, P(rect(width - w.s - 22, w.m0, width - w.s + 1, w.m1))])


def g_h(w, width=100):
    return unary_union([stem(w), stem(w, width - w.s), P(rect(w.s - 1, w.m0, width - w.s + 1, w.m1))])


def g_i(w):
    return stem(w)


def g_j(w, width=88):
    return u_ring(w, width).difference(P(rect(-1, 40, width / 2, 101)))


def g_k(w):
    vertex = (w.s, 38)
    arm_axis = add(vertex, C.UPPER_LEFT, w.s / 2)
    upper = box(blade(arm_axis, add(arm_axis, C.UP, 120), w.d, before=40), x0=0, y1=100)
    gap_at = add(vertex, C.LOWER_RIGHT, w.g)
    leg_axis = (w.s + 24, 40)
    leg = box(blade(add(leg_axis, C.DOWN, -60), add(leg_axis, C.DOWN, 120), w.d), y0=0)
    leg = keep(leg, gap_at, add(gap_at, C.UP, 50), (w.s + 60, 5))
    return unary_union([stem(w), P(upper), P(leg)])


def g_l(w, width=80):
    return unary_union([stem(w), arm(width, 0, w.h)])


def g_m(w):
    width = 1.4 * w.s + 94

    def arm_of(start, direction):
        far = (start[0] + direction[0] * 200, start[1] + direction[1] * 200)
        return P(box(blade(start, far, w.d, before=40), y1=100))
    left = arm_of((0.7 * w.s, 100), (C.COS, -C.SIN)).intersection(P(rect(-100, -100, width / 2, 200)))
    right = arm_of((width - 0.7 * w.s, 100), (-C.COS, -C.SIN)).intersection(P(rect(width / 2, -100, width + 100, 200)))
    v = unary_union([left, right]).intersection(P(rect(0, 0, width, 100)))
    room = v.buffer(w.g, join_style='mitre')
    return unary_union([stem(w).difference(room), stem(w, width - w.s).difference(room), v])


def g_n(w):
    width = 78 + 1.4 * w.s
    diagonal = P(box(blade((0.7 * w.s, 100), (width - 0.7 * w.s, 0), w.d, before=60, after=60), y0=0, y1=100))
    room = diagonal.buffer(w.g, join_style='mitre')
    return unary_union([stem(w).difference(room), stem(w, width - w.s).difference(room), diagonal])


def g_o(w, width=104):
    return ring(w, width, 0, 100, w.ho, w.ho)


def g_p(w, width=96):
    return unary_union([stem(w), bowl(w, width, w.bowl0, 100, w.h, w.ho)])


def g_q(w, width=104, top=40):
    body = ring(w, width, 0, 100, w.ho, w.ho)
    across = w.h / SIN
    foot = (width - 20.6, width - 20.6 + across, 0)
    tail = band(foot, (foot[0] - top * RUN, foot[1] - top * RUN, top))
    return unary_union([body.difference(tail.buffer(w.g, join_style='mitre')), tail])


def g_r(w, width=100):
    top = w.bowl0 - w.g
    leg = P([(width - w.ac, 0), (width, 0), (width - top * RUN, top), (width - w.ac - top * RUN, top)])
    return unary_union([stem(w), bowl(w, width, w.bowl0, 100, w.h, w.ho), leg])


def g_s(w, width=96):
    upper = ring(w, width, w.m0, 100, w.h, w.h).difference(P(rect(width / 2, w.m0 - 1, width + 1, 100 - w.h)))
    lower = ring(w, width, 0, w.m1, w.h, w.h).difference(P(rect(-1, w.h, width / 2, w.m1 + 1)))
    return unary_union([upper, lower])


def g_t(w, width=97):
    bar = P([(0, 100), (width, 100), (width - w.ho * RUN, 100 - w.ho), (w.ho * RUN, 100 - w.ho)])
    left = (width - w.s) / 2
    return unary_union([bar, P(rect(left, 0, left + w.s, 100 - w.ho + 1))])


def g_u(w, width=100):
    return u_ring(w, width)


def g_v(w):
    run = 100 * RUN
    diagonal = band((run, run + w.ac, 0), (0, w.ac, 100))
    return unary_union([diagonal, stem(w, run)]).intersection(P(rect(0, 0, run + w.s, 100)))


def g_w(w):
    return scale(g_m(w), yfact=-1, origin=((1.4 * w.s + 94) / 2, 50))


def g_x(w):
    width = 78 + w.ac
    falling = band((width - w.ac, width, 0), (0, w.ac, 100))
    rising = band((0, w.ac, 0), (width - w.ac, width, 100))
    return unary_union([falling, rising.difference(falling.buffer(w.g, join_style='mitre'))])


def g_y(w):
    width = 78 + w.ac
    middle = width / 2
    left = band((middle - w.ac / 2, middle + w.ac / 2, 50), (0, w.ac, 100)).intersection(P(rect(-1, 0, middle, 101)))
    right = band((middle - w.ac / 2, middle + w.ac / 2, 50), (width - w.ac, width, 100)).intersection(P(rect(middle, 0, width + 1, 101)))
    arms = unary_union([left, right])
    return unary_union([arms, P(rect(middle - w.s / 2, 0, middle + w.s / 2, arms.bounds[1] + 12))])


def without_slivers(shape, least):
    return unary_union([piece for piece in getattr(shape, 'geoms', [shape]) if piece.area >= least])


def g_z(w):
    width = 78 + w.ac
    diagonal = band((0, w.ac, 0), (width - w.ac, width, 100))
    room = diagonal.buffer(w.g, join_style='mitre')
    bars = [P(rect(0, 100 - w.h, width, 100)).difference(room), P(rect(0, 0, width, w.h)).difference(room)]
    return without_slivers(unary_union(bars + [diagonal]), 200 * (w.s / 30) ** 2)


def g_0(w, width=92):
    body = ring(w, width, 0, 100, w.ho, w.ho)
    outer = [(R, 0), (width - R, 0), (width, CUT), (width, 100 - CUT), (width - R, 100), (R, 100), (0, 100 - CUT), (0, CUT)]
    counter = P(offset(outer, [-w.ho, -w.corner, -w.s, -w.corner, -w.ho, -w.corner, -w.s, -w.corner])).buffer(-w.g, join_style='mitre')
    half = 10 * w.s / 30
    slash = band((width / 2 - half + 50 * RUN / 2, width / 2 + half + 50 * RUN / 2, 25), (width / 2 - half - 50 * RUN / 2, width / 2 + half - 50 * RUN / 2, 75))
    return unary_union([body, slash.intersection(counter)])


def four_bar(w):
    return (25 - w.h / 2, 25 + w.h / 2)


def g_1(w):
    pieces, _ = C.four(0, four_bar(w), w.d, w.s, 0)
    return unary_union([pieces[0].intersection(P(rect(-100, 60, 300, 101))), pieces[2]])


def g_2(w, width=96):
    upper = ring(w, width, w.m0, 100, w.h, w.h).difference(P(rect(-1, w.m0 - 1, width / 2, 100 - w.h)))
    run = (w.m1 - w.h) * RUN
    diagonal = band((0, w.ac, w.h - 1), (run, run + w.ac, w.m1))
    joint = P(rect(run, w.m0, width / 2 + 1, w.m1))
    return unary_union([upper, arm(width, 0, w.h), diagonal, joint])


def g_3(w, width=96):
    upper = ring(w, width, w.m0, 100, w.h, w.h).difference(P(rect(-1, w.m1, width / 2, 100 - w.h)))
    lower = ring(w, width, 0, w.m1, w.h, w.h).difference(P(rect(-1, w.h, width / 2, w.m0)))
    return unary_union([upper, lower]).difference(P(rect(-1, w.m0 - 1, 22, w.m1 + 1)))


def g_4(w, arm_out=None):
    pieces, _ = C.four(0, four_bar(w), w.d, w.s, w.sp if arm_out is None else arm_out)
    return unary_union(pieces)


def g_5(w, width=96):
    lower = ring(w, width, 0, w.m1, w.h, w.h).difference(P(rect(-1, w.h, width / 2, w.m1 + 1)))
    return unary_union([lower, P(rect(0, w.m0, w.s, 100)), arm(width, 100 - w.h, 100), P(rect(0, w.m0, width / 2 + 1, w.m1))])


def g_6(w, width=96):
    upper_outer = [(0, w.m0), (width - R, w.m0), (width, w.m0 + CUT), (width, 100 - CUT), (width - R, 100), (R, 100), (0, 100 - CUT)]
    upper_inner = offset(upper_outer, [-w.h, -w.corner, -w.s, -w.corner, -w.h, -w.corner, -w.s])
    upper = P(upper_outer).difference(P(upper_inner)).difference(P(rect(width / 2, w.m0 - 1, width + 1, 100 - w.h)))
    lower_outer = [(R, 0), (width - R, 0), (width, CUT), (width, w.m1 - CUT), (width - R, w.m1), (0, w.m1), (0, CUT)]
    lower_inner = offset(lower_outer, [-w.h, -w.corner, -w.s, -w.corner, -w.h, -w.s, -w.corner])
    return unary_union([upper, P(lower_outer).difference(P(lower_inner))])


def g_7(w, width=96):
    run = (100 - w.h) * RUN
    diagonal = band((width - run - w.ac, width - run, 0), (width - w.ac, width, 100 - w.h + 1))
    return unary_union([P(rect(0, 100 - w.h, width, 100)), diagonal])


def g_8(w, width=96):
    return unary_union([ring(w, width, w.m0, 100, w.h, w.h), ring(w, width, 0, w.m1, w.h, w.h)])


def g_9(w):
    return rotate(g_6(w), 180, origin=(48, 50))


DRAW = {name[2:]: f for name, f in globals().items() if name.startswith('g_') and len(name) == 3}


def glyph_set(w):
    glyphs = {name: B42.at_left_zero(draw(w)) for name, draw in DRAW.items()}
    bodies = dict(glyphs)
    bodies['4'] = B42.at_left_zero(g_4(w, arm_out=0))
    return glyphs, bodies


def set_line(text, glyphs, bodies, sp, space=40):
    """letters set by their least distance (sp), the 4 spaced from its stem; a space moves the next word on"""
    drawn, spaced, x_after_space = [], [], None
    for char in text:
        if char == ' ':
            x_after_space = (unary_union(spaced).bounds[2] if spaced else 0) + space
            continue
        glyph, body = glyphs[char], bodies[char]
        if not spaced:
            shift = 0
        elif x_after_space is not None:
            shift = x_after_space
        else:
            before = unary_union(spaced)
            low, high = before.bounds[0] - body.bounds[2], before.bounds[2] + sp + 1
            for _ in range(60):
                middle = (low + high) / 2
                if before.distance(translate(body, middle, 0)) >= sp - 1e-9:
                    high = middle
                else:
                    low = middle
            shift = high
        x_after_space = None
        drawn.append(translate(glyph, shift, 0))
        spaced.append(translate(body, shift, 0))
    return B44.joined(drawn)


def check_bold():
    a56 = load('a56', 'alphabet-v56.py')
    old, _ = a56.font()
    new, _ = glyph_set(BOLD)
    report = {}
    for name in sorted(new):
        a, b = new[name], old[name]
        report[name] = round(a.symmetric_difference(b).area, 2)
    return report


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {'boldCheck': check_bold()}
    texts = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789',
             'judgment': 'perfect great good miss', 'ui-1': 'song select', 'ui-2': 'high score 9876', 'ui-3': 'settings'}
    for w in [BOLD] + REGULARS:
        glyphs, bodies = glyph_set(w)
        for name, shape in glyphs.items():
            assert shape.is_valid, (w.name, name)
        for key, text in texts.items():
            shape = set_line(text, glyphs, bodies, w.sp)
            size = B42.write(shape, folder / f'{w.name}-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name})')
            report[f'{w.name}-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print('bold check (area that differs from round v56, per letter):', {k: v for k, v in report['boldCheck'].items() if v > 0.5})
    print({k: v['svg'][0] for k, v in report.items() if k != 'boldCheck'})


if __name__ == '__main__':
    main()
