"""Round v48: the rest of the Bold capitals and the numerals, the user having taken the G with a spur of 24 ("응
고친게낫다 다른 알파벳이랑 숫자도 ㄱㄱ"). Rules as before: stems 30; horizontals 26 in the O family (O, C, G, D, Q, U,
J, 0) and the T, 24 where they stack (E, F, S, B, 2, 3, 5, 6, 8, 9), on arms (L, Z, 7) and in crossbars (A, H);
rounded corners cut 26 tall at 52 degrees; new diagonals 26 across at 52 degrees, as in the 4 and the A (those of
the logo, N, K, M, R, stay 30); a diagonal meeting a stem stands 6 apart from it (stencil), except where a letter is
built like the 4 (A, V, 1), which joins as the 4 does.
  B  a stem and two stacked rings, the upper narrower      H  two stems and a crossbar
  J  the lower part of a U, the left side cut at 40        L  a stem and an arm, its end cut like the arm of the E
  Q  the O with a tail at 52 degrees through its lower right corner, standing 6 apart from the ring
  U  the O open at the top                                 V  the A built like the 4 turned upside down, no crossbar
  W  the M upside down                                     X  two diagonals, the one at the angle of the red in front
  Y  two arms meeting in the middle on a stem              Z  bars of 24 with a diagonal from corner to corner
  0  an O 92 wide with a short slash at the angle of the red inside, 6 from the ring
  1  the stem of the 4 with the top of its diagonal as a flag
  2  the upper ring open on the left, a diagonal down to the lower bar   3  two rings open on the left
  5  a square upper left, the lower ring open on the left  6  the upper ring open on the right on a full lower ring
  7  a bar and a diagonal from its right end to the baseline              8  two rings, the upper narrower
  9  the 6 turned half round
Needs shapely (PYTHONPATH). Usage: alphabet-v48.py <out folder>"""
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


J47 = load('j47', 'judgment-v47.py')
J46, J = J47.J46, J47.J
B42, B43, B44, C = J.B42, J.B43, J.B44, J.C
P, rect, S, R, CORNER, GAP, ring, arm = J.P, J.rect, J.S, J.R, J.CORNER, J.GAP, J.ring, J.arm
DIAG = 26
ACROSS = DIAG / C.SIN                     # a diagonal of 26 measured along a horizontal: 33


def blade(p, q, width=DIAG):
    return P(C.blade(p, q, width))


def band(points_bottom, points_top):
    """a diagonal band given by its two ends on horizontal lines: (x_left, x_right, y) at the bottom and at the top"""
    (b0, b1, yb), (t0, t1, yt) = points_bottom, points_top
    return P([(b0, yb), (b1, yb), (t1, yt), (t0, yt)])


def g_b():
    upper = ring(88, 38, 100, 24, 24)
    lower = ring(96, 0, 62, 24, 24)
    return unary_union([upper, lower, P(rect(0, 0, S, 100))])


def g_h(width=100):
    return unary_union([P(rect(0, 0, S, 100)), P(rect(width - S, 0, width, 100)), P(rect(S - 1, 38, width - S + 1, 62))])


def u_ring(width):
    outer = [(0, 100), (0, 26), (R, 0), (width - R, 0), (width, 26), (width, 100)]
    inner = J.offset(outer, [-S, -CORNER, -26, -CORNER, -S, 10])
    return P(outer).difference(P(inner))


def g_j(width=88):
    return u_ring(width).difference(P(rect(-1, 40, width / 2, 101)))


def g_l(width=80):
    return unary_union([P(rect(0, 0, S, 100)), arm(width, 0, 24)])


def g_q(width=104):
    body = ring(width, 0, 100, 26, 26)
    tail = P(C.box(C.blade((width - 46, 52), (width + 16, -27.4), 24), y0=0))
    return unary_union([body.difference(tail.buffer(GAP, join_style='mitre')), tail])


def g_u(width=100):
    return u_ring(width)


def v_like_four():
    run = 100 * C.RUN
    diagonal = band((run, run + ACROSS, 0), (0, ACROSS, 100))
    return unary_union([diagonal, P(rect(run, 0, run + S, 100))]).intersection(P(rect(0, 0, run + S, 100)))


def g_w():
    return scale(J.g_m(), yfact=-1, origin=(68, 50))


def g_x():
    width = 100 * C.RUN + ACROSS
    falling = band((width - ACROSS, width, 0), (0, ACROSS, 100))
    rising = band((0, ACROSS, 0), (width - ACROSS, width, 100))
    return unary_union([falling, rising.difference(falling.buffer(GAP, join_style='mitre'))])


def g_y():
    width = 100 * C.RUN + ACROSS
    middle = width / 2
    left = band((middle - ACROSS / 2, middle + ACROSS / 2, 50), (0, ACROSS, 100)).intersection(P(rect(-1, 0, middle, 101)))
    right = band((middle - ACROSS / 2, middle + ACROSS / 2, 50), (width - ACROSS, width, 100)).intersection(P(rect(middle, 0, width + 1, 101)))
    arms = unary_union([left, right])
    low = arms.bounds[1]
    stem = P(rect(middle - S / 2, 0, middle + S / 2, low + 12))
    return unary_union([arms, stem])


def g_z():
    width = 100 * C.RUN + ACROSS
    cut = 24 * C.RUN
    top = P([(0, 76), (cut, 100), (width, 100), (width, 76)])
    bottom = P([(0, 0), (width - cut, 0), (width, 24), (0, 24)])
    return unary_union([top, bottom, band((0, ACROSS, 0), (width - ACROSS, width, 100))])


def g_0(width=92):
    body = ring(width, 0, 100, 26, 26)
    outer = [(R, 0), (width - R, 0), (width, 26), (width, 74), (width - R, 100), (R, 100), (0, 74), (0, 26)]
    counter = P(J.offset(outer, [-26, -CORNER, -S, -CORNER, -26, -CORNER, -S, -CORNER])).buffer(-GAP, join_style='mitre')
    slash = band((width / 2 - 10 + 50 * C.RUN / 2, width / 2 + 10 + 50 * C.RUN / 2, 25), (width / 2 - 10 - 50 * C.RUN / 2, width / 2 + 10 - 50 * C.RUN / 2, 75))
    return unary_union([body, slash.intersection(counter)])


def g_1():
    pieces, stem_x = C.four(0, (13, 37), 26, S, 0)
    flag = pieces[0].intersection(P(rect(-100, 60, 300, 101)))
    return unary_union([flag, pieces[2]])


def g_2(width=96):
    upper = ring(width, 38, 100, 24, 24).difference(P(rect(-1, 37, width / 2, 76)))
    bottom = arm(width, 0, 24)
    run = (62 - 24) * C.RUN
    diagonal = band((0, ACROSS, 24 - 1), (run, run + ACROSS, 62))
    joint = P(rect(run, 38, width / 2 + 1, 62))
    return unary_union([upper, bottom, diagonal, joint])


def g_3(width=96):
    upper = ring(width, 38, 100, 24, 24).difference(P(rect(-1, 62, width / 2, 76)))
    lower = ring(width, 0, 62, 24, 24).difference(P(rect(-1, 24, width / 2, 38)))
    return unary_union([upper, lower]).difference(P(rect(-1, 37, 22, 63)))


def g_5(width=96):
    lower = ring(width, 0, 62, 24, 24).difference(P(rect(-1, 24, width / 2, 63)))
    return unary_union([lower, P(rect(0, 38, S, 100)), arm(width, 76, 100), P(rect(0, 38, width / 2 + 1, 62))])


def g_6(width=96):
    upper = ring(width, 38, 100, 24, 24).difference(P(rect(width / 2, 37, width + 1, 76)))
    return unary_union([upper, ring(width, 0, 62, 24, 24)])


def g_7(width=96):
    run = 76 * C.RUN
    diagonal = band((width - run - ACROSS, width - run, 0), (width - ACROSS, width, 76 + 1))
    return unary_union([P(rect(0, 76, width, 100)), diagonal])


def g_8():
    upper = translate(ring(88, 38, 100, 24, 24), 4, 0)
    return unary_union([upper, ring(96, 0, 62, 24, 24)])


def g_9():
    return rotate(g_6(), 180, origin=(48, 50))


DRAW = {
    'b': g_b, 'h': g_h, 'j': g_j, 'l': g_l, 'q': g_q, 'u': g_u, 'v': v_like_four, 'w': g_w, 'x': g_x, 'y': g_y, 'z': g_z,
    '0': g_0, '1': g_1, '2': g_2, '3': g_3, '5': g_5, '6': g_6, '7': g_7, '8': g_8, '9': g_9,
}


def full_set():
    glyphs, bodies = B43.glyph_set()
    for name, shape in {'p': J.g_p(), 'e': J.g_e(), 'r': J.g_r(), 'f': J.g_f(), 'c': J.g_c(), 'd': J.g_d(), 'm': J.g_m(), 'i': J.g_i(), 's': J.g_s(), 'a': J46.a_like_four(), 'g': J47.g_bar()}.items():
        glyphs[name] = bodies[name] = B42.at_left_zero(shape)
    for name, draw in DRAW.items():
        glyphs[name] = bodies[name] = B42.at_left_zero(draw())
    return glyphs, bodies


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = full_set()
    report = {}
    for name in sorted(glyphs):
        shape = glyphs[name]
        assert shape.is_valid, name
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), f'Bold {name.upper()}')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size], 'pieces': len(getattr(shape, 'geoms', [shape]))}
    lines = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789',
             'perfect': 'perfect', 'great': 'great', 'good': 'good', 'miss': 'miss', 'combo': '1024', 'quick': 'jumpqxz'}
    for key, text in lines.items():
        drawn, _ = B43.set_word(list(text), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'line-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), text.upper())
        report[f'line-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
