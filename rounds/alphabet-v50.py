"""Round v50. The user: "B 구멍 왼쪽 < 말고 직선으로할 z는 모양이 이상함".
  B   its counters straight on the left (the side of the stem), pointed only on the right, as in the D and the P:
      both bowls square on the left, 96 wide
  Z   three versions: as in round v48 (both bar ends cut parallel to the diagonal, so the whole letter is a
      parallelogram), with square ends, and with ends cut as the T and the E cut theirs (the top edge longer)
  Q   then also "Q의 마지막 선은 R처럼 상단이평평하게": the tail of the Q as a band with flat ends, like the leg of
      the R (top level at 52 inside the counter, foot on the baseline), 24 across, the ring 6 apart from it
Needs shapely (PYTHONPATH). Usage: alphabet-v50.py <out folder>"""
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


A49 = load('a49', 'alphabet-v49.py')
A48 = A49.A48
J, B42, B43, B44, C = A48.J, A48.B42, A48.B43, A48.B44, A48.C
P, rect, S, R, CORNER, ACROSS = A48.P, A48.rect, A48.S, A48.R, A48.CORNER, A48.ACROSS


def bowl_between(width, y0, y1, bottom=24, top=24):
    """a bowl square on the left (where the stem stands) and rounded as the O on the right, between y0 and y1"""
    outer = [(0, y0), (width - R, y0), (width, y0 + 26), (width, y1 - 26), (width - R, y1), (0, y1)]
    inner = J.offset(outer, [-bottom, -CORNER, -S, -CORNER, -top, -S])
    return P(outer).difference(P(inner))


def g_b(width=96):
    return unary_union([bowl_between(width, 38, 100), bowl_between(width, 0, 62), P(rect(0, 0, S, 100))])


def z_with(top_bar, bottom_bar):
    width = 100 * C.RUN + ACROSS
    return unary_union([top_bar(width), bottom_bar(width), A48.band((0, ACROSS, 0), (width - ACROSS, width, 100))])


def z_square():
    return z_with(lambda w: P(rect(0, 76, w, 100)), lambda w: P(rect(0, 0, w, 24)))


def z_t():
    cut = 24 * C.RUN
    return z_with(lambda w: P([(0, 100), (w, 100), (w, 76), (cut, 76)]), lambda w: P([(0, 0), (w - cut, 0), (w, 24), (0, 24)]))


def g_q_flat(width=104):
    body = A48.ring(width, 0, 100, 26, 26)
    across = 24 / C.SIN
    top = 52
    foot = (width - 20.6, width - 20.6 + across, 0)
    head = (foot[0] - top * C.RUN, foot[1] - top * C.RUN, top)
    tail = A48.band(foot, head)
    return unary_union([body.difference(tail.buffer(A48.GAP, join_style='mitre')), tail])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    shapes = {'b-new': g_b(), 'b-old': A49.g_b(), 'z-now': A48.g_z(), 'z-square': z_square(), 'z-t': z_t(), 'q-now': A48.g_q(), 'q-flat': g_q_flat()}
    for name, shape in shapes.items():
        shape = B42.at_left_zero(shape)
        assert shape.is_valid, name
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), name)
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    A48.DRAW['b'] = g_b
    for z in ('z-now', 'z-square', 'z-t'):
        A48.DRAW['z'] = {'z-now': A48.g_z, 'z-square': z_square, 'z-t': z_t}[z]
        glyphs, bodies = A48.full_set()
        for key, text in (('zebra', 'zebra'), ('maze', 'maze')):
            drawn, _ = B43.set_word(list(text), glyphs, bodies)
            line = B44.joined(drawn)
            size = B42.write(line, folder / f'word-{key}-{z}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{text.upper()} with {z}')
            report[f'word-{key}-{z}'] = {'svg': [round(v, 2) for v in size]}
    A48.DRAW['z'] = z_square
    for q in ('q-now', 'q-flat'):
        A48.DRAW['q'] = {'q-now': A48.g_q, 'q-flat': g_q_flat}[q]
        glyphs, bodies = A48.full_set()
        drawn, _ = B43.set_word(list('quest'), glyphs, bodies)
        line = B44.joined(drawn)
        size = B42.write(line, folder / f'word-quest-{q}.svg', (-12, line.bounds[2] + 12, -12, 112), f'QUEST with {q}')
        report[f'word-quest-{q}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
