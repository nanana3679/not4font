"""Round v45: the Bold letters the judgment words need (PERFECT, GREAT, GOOD, MISS), drawn by the rules of the base
forms: stems 30; horizontals 26 in the O family and the T, 24 where three of them stack (E, F, S) and for the lower
bar of a bowl and the crossbar of the A; rounded sides as the O, corners cut 26 tall at the angle of the red
diagonal (52 degrees); arm ends of E and F cut like the right end of the T; diagonals 30 across standing 6 apart from
stems and bowls (stencil), as in the N and the K.
  P  stem and a bowl from 34 up, its right side rounded as the O
  E  stem and three arms 24 thick (the middle one shorter), their right ends cut at 52 degrees
  R  the P with a leg at 52 degrees under the bowl, 6 below it, reaching the baseline at the right
  F  the E without its lower arm
  C  the O 96 wide, open on the right between its arms
  G  the O open on the upper right, with a spur from the right side inwards, standing on the lower bar up to 56
  A  vertical legs, the top corners cut deep (52 tall, still at 52 degrees) so that it reads as A and not as 4
  D  stem on the left, rounded on the right as the O
  M  two stems and a V standing 6 apart from them, its arms on the axis of the diagonal of the N
  I  a stem
  S  two rings stacked, the upper open on the right and the lower open on the left
Also the four words set with nothing but the gap of 6. Needs shapely (PYTHONPATH). Usage: judgment-v45.py <out>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B43 = load('b43', 'base-v43.py')
B42 = B43.B42
B44 = load('b44', 'base-v44.py')
B43.ARM = B42.GAP                     # the arm of the 4 runs on by the letter spacing (round v44); base-v44 sets it only in its own copy
C = B42.C
P, rect, offset = C.P, C.rect, C.offset
S, GAP, CUT = 30, 6, 26
R = CUT * C.RUN                       # how far a corner cut runs along a horizontal edge: 20.28
CORNER = S * 0.93                     # how far the inner edge of a cut corner stands from the outer one (as in the O)


def ring(width, y0, y1, top, bottom):
    """an O-like ring between y0 and y1: sides S, top and bottom bars as given, every corner cut CUT tall"""
    outer = [(R, y0), (width - R, y0), (width, y0 + CUT), (width, y1 - CUT), (width - R, y1), (R, y1), (0, y1 - CUT), (0, y0 + CUT)]
    inner = offset(outer, [-bottom, -CORNER, -S, -CORNER, -top, -CORNER, -S, -CORNER])
    return P(outer).difference(P(inner))


def arm(x_end, y0, y1):
    """a horizontal arm from the stem, its right end cut at 52 degrees (the top longer), as the right end of the T"""
    return P([(0, y0), (0, y1), (x_end, y1), (x_end - (y1 - y0) * C.RUN, y0)])


def bowl(width, y0, bottom=24, top=26):
    """a bowl on a stem: square on the left, rounded as the O on the right, from y0 to the cap height"""
    outer = [(0, y0), (width - R, y0), (width, y0 + CUT), (width, 100 - CUT), (width - R, 100), (0, 100)]
    inner = offset(outer, [-bottom, -CORNER, -S, -CORNER, -top, -S])
    return P(outer).difference(P(inner))


def g_p():
    return unary_union([P(rect(0, 0, S, 100)), bowl(96, 34)])


def g_e(width=84):
    return unary_union([P(rect(0, 0, S, 100)), arm(width, 76, 100), arm(width - 8, 38, 62), arm(width, 0, 24)])


def g_f(width=82):
    return unary_union([P(rect(0, 0, S, 100)), arm(width, 76, 100), arm(width - 8, 38, 62)])


def g_r(width=100):
    leg_across = S / C.SIN                  # the width of the leg along a horizontal line
    top = 34 - GAP
    leg = P([(width - leg_across, 0), (width, 0), (width - top * C.RUN, top), (width - leg_across - top * C.RUN, top)])
    return unary_union([P(rect(0, 0, S, 100)), bowl(width, 34), leg])


def g_c(width=96):
    return ring(width, 0, 100, 26, 26).difference(P(rect(width / 2, 26, width + 1, 74)))


def g_g(width=104):
    body = ring(width, 0, 100, 26, 26).difference(P(rect(width / 2, 56, width + 1, 74)))
    # the spur fills the counter from the lower bar up to 56, so that no notch is left under it
    spur = P(rect(width - S - 22, 20, width - S + 1, 56))
    return unary_union([body, spur])


def g_a(width=112, deep=52):
    run = deep * C.RUN
    outer = [(0, 0), (0, 100 - deep), (run, 100), (width - run, 100), (width, 100 - deep), (width, 0)]
    inner = offset(outer, [-S, -CORNER, -26, -CORNER, -S, 10])
    crossbar = P(rect(0, 24, width, 48)).intersection(P(outer))
    return unary_union([P(outer).difference(P(inner)), crossbar])


def g_d(width=100):
    outer = [(0, 0), (width - R, 0), (width, CUT), (width, 100 - CUT), (width - R, 100), (0, 100)]
    inner = offset(outer, [-26, -CORNER, -S, -CORNER, -26, -S])
    return P(outer).difference(P(inner))


def g_m(width=136):
    def blade(start, direction):
        far = (start[0] + direction[0] * 200, start[1] + direction[1] * 200)
        return P(C.box(C.blade(start, far, 30, before=40), y1=100))
    left = blade((21, 100), (C.COS, -C.SIN)).intersection(P(rect(-100, -100, width / 2, 200)))
    right = blade((width - 21, 100), (-C.COS, -C.SIN)).intersection(P(rect(width / 2, -100, width + 100, 200)))
    v = unary_union([left, right]).intersection(P(rect(0, 0, width, 100)))
    room = v.buffer(GAP, join_style='mitre')
    stems = [P(rect(0, 0, S, 100)).difference(room), P(rect(width - S, 0, width, 100)).difference(room)]
    return unary_union(stems + [v])


def g_i():
    return P(rect(0, 0, S, 100))


def g_s(width=96):
    upper = ring(width, 38, 100, 24, 24).difference(P(rect(width / 2, 38 - 1, width + 1, 76)))
    lower = ring(width, 0, 62, 24, 24).difference(P(rect(-1, 24, width / 2, 62 + 1)))
    return unary_union([upper, lower])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = B43.glyph_set()
    new = {'p': g_p(), 'e': g_e(), 'r': g_r(), 'f': g_f(), 'c': g_c(), 'g': g_g(), 'a': g_a(), 'd': g_d(), 'm': g_m(), 'i': g_i(), 's': g_s()}
    report = {}
    for name, shape in new.items():
        shape = B42.at_left_zero(shape)
        assert shape.is_valid, name
        glyphs[name] = bodies[name] = shape
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), f'Bold {name.upper()}')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size], 'pieces': len(getattr(shape, 'geoms', [shape]))}
    for name in ('o', 't'):
        width = glyphs[name].bounds[2]
        size = B42.write(glyphs[name], folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), f'Bold {name.upper()}')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    for word in ('perfect', 'great', 'good', 'miss'):
        drawn, spaced = B43.set_word(list(word), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'word-{word}.svg', (-12, shape.bounds[2] + 12, -12, 112), word.upper())
        report[f'word-{word}'] = {'svg': [round(v, 2) for v in size], 'starts': [round(piece.bounds[0], 2) for piece in spaced]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v.get('svg')) for k, v in report.items()}))


if __name__ == '__main__':
    main()
