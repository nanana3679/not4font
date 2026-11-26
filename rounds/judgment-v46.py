"""Round v46. The user: "26인 경우, a를 4와 비슷하게 만든 경우 보여줘". Read two ways, both shown:
  - the A with its top corners cut 26 tall like every other corner (instead of 52), and the A built like the 4 (a
    diagonal leg at 52 degrees on the left joined at the top to a stem on the right, the crossbar where the 4 has it);
  - every horizontal 26 (E, F, S, the lower bar of the bowls of P and R, the crossbar of the A), instead of 24.
Writes the A versions beside the 4, GREAT with each A, and the four words and changed letters with horizontals 26.
Needs shapely (PYTHONPATH). Usage: judgment-v46.py <out folder>"""
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


J = load('j45', 'judgment-v45.py')
B42, B43, B44, C = J.B42, J.B43, J.B44, J.C
P, rect, S = J.P, J.rect, J.S


def a_like_four(leg=26, bar=(13, 37)):
    """the A built like the 4: the outer edge of a diagonal leg runs from (0, 0) at 52 degrees up to the top of a stem
    on the right, joined to it there; a crossbar between them where the 4 has its crossbar"""
    stem_x = 100 * C.RUN
    axis_start = C.add((0, 0), C.LOWER_RIGHT, leg / 2)
    diagonal = P(C.box(C.blade(axis_start, C.add(axis_start, C.UP, 160), leg, before=40), y0=0, y1=100, x1=stem_x + S))
    crossbar = P(C.keep(rect(-40, bar[0], stem_x + S, bar[1]), (0, 0), (stem_x, 100), (stem_x, 5)))
    return unary_union([diagonal, crossbar, P(rect(stem_x, 0, stem_x + S, 100))])


def all_26():
    """the letters whose horizontals were 24, redrawn with 26"""
    def e(width=84):
        return unary_union([P(rect(0, 0, S, 100)), J.arm(width, 74, 100), J.arm(width - 8, 37, 63), J.arm(width, 0, 26)])

    def f(width=82):
        return unary_union([P(rect(0, 0, S, 100)), J.arm(width, 74, 100), J.arm(width - 8, 37, 63)])

    def s(width=96):
        upper = J.ring(width, 37, 100, 26, 26).difference(P(rect(width / 2, 37 - 1, width + 1, 74)))
        lower = J.ring(width, 0, 63, 26, 26).difference(P(rect(-1, 26, width / 2, 63 + 1)))
        return unary_union([upper, lower])

    def p(width=96):
        return unary_union([P(rect(0, 0, S, 100)), J.bowl(width, 34, bottom=26)])

    def r(width=100):
        leg_across = S / C.SIN
        top = 34 - J.GAP
        leg = P([(width - leg_across, 0), (width, 0), (width - top * C.RUN, top), (width - leg_across - top * C.RUN, top)])
        return unary_union([P(rect(0, 0, S, 100)), J.bowl(width, 34, bottom=26), leg])

    def a(width=112, deep=52):
        run = deep * C.RUN
        outer = [(0, 0), (0, 100 - deep), (run, 100), (width - run, 100), (width, 100 - deep), (width, 0)]
        inner = J.offset(outer, [-S, -J.CORNER, -26, -J.CORNER, -S, 10])
        crossbar = P(rect(0, 22, width, 48)).intersection(P(outer))
        return unary_union([P(outer).difference(P(inner)), crossbar])

    return {'e': e(), 'f': f(), 's': s(), 'p': p(), 'r': r(), 'a': a()}


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = B43.glyph_set()
    base = {'p': J.g_p(), 'e': J.g_e(), 'r': J.g_r(), 'f': J.g_f(), 'c': J.g_c(), 'g': J.g_g(), 'a': J.g_a(), 'd': J.g_d(), 'm': J.g_m(), 'i': J.g_i(), 's': J.g_s()}
    for name, shape in base.items():
        glyphs[name] = bodies[name] = B42.at_left_zero(shape)
    report = {}
    versions = {'a52': J.g_a(), 'a26': J.g_a(deep=26), 'a4': a_like_four()}
    for name, shape in versions.items():
        shape = B42.at_left_zero(shape)
        assert shape.is_valid, name
        versions[name] = shape
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), name)
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    four = glyphs['4']
    size = B42.write(four, folder / 'glyph-4.svg', (-12, four.bounds[2] + 12, -12, 112), '4')
    report['4'] = {'width': round(four.bounds[2], 2), 'svg': [round(v, 2) for v in size]}
    for name, shape in versions.items():
        g, b = dict(glyphs), dict(bodies)
        g['a'] = b['a'] = shape
        drawn, _ = B43.set_word(list('great'), g, b)
        word = B44.joined(drawn)
        size = B42.write(word, folder / f'word-great-{name}.svg', (-12, word.bounds[2] + 12, -12, 112), f'GREAT with {name}')
        report[f'word-great-{name}'] = {'svg': [round(v, 2) for v in size]}
    heavier = {name: B42.at_left_zero(shape) for name, shape in all_26().items()}
    g, b = dict(glyphs), dict(bodies)
    for name, shape in heavier.items():
        assert shape.is_valid, name
        g[name] = b[name] = shape
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph26-{name}.svg', (-12, width + 12, -12, 112), f'{name} with horizontals 26')
        report[f'26-{name}'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    for word in ('perfect', 'great', 'good', 'miss'):
        drawn, _ = B43.set_word(list(word), g, b)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'word26-{word}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{word.upper()} with horizontals 26')
        report[f'word26-{word}'] = {'svg': [round(v, 2) for v in size]}
        drawn, _ = B43.set_word(list(word), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'word24-{word}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{word.upper()} as in round v45')
        report[f'word24-{word}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
