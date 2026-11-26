"""Round v75. The user: "직각이낫다" — the G's ㄱ with a square foot (decided). Next, as announced in round v71: the V
of the Regular reads as a backslash and an I when small (VS reads as a backslash, an I and an S), because its right arm is an
upright stem and the two strokes meet at a flat foot.
Four Vs, the same width as now (Regular 94, Bold 108):
  1 now      the 52 degree diagonal and an upright stem on the right
  2 corner   the same with the lower right corner cut at 52 degrees, so that the two strokes meet in a point
  3 pencil   upright arms above, both coming down at 52 degrees to a point in the middle (like a pencil's tip)
  4 steep    two straight arms to a point in the middle; their angle is not 52 degrees (about 65)
Needs shapely (PYTHONPATH). Usage: font-v80.py <out folder>"""
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


V79 = load('f79', 'font-v79.py')
V72, F = V79.V72, V79.F
P, rect, offset, RUN = F.P, F.rect, F.offset, F.RUN
REGULAR, BOLD = V79.REGULAR, V79.BOLD


def v_corner(w):
    v = F.g_v(w)
    run = 100 * RUN
    # the half-plane right of the rising 52 degree line through the foot of the diagonal's left edge (run, 0)
    cut = P([(run, 0), (run + 300 * RUN, 300), (run + 600, 300), (run + 600, -10), (run - 10 * RUN, -10)])
    return v.difference(cut)


def v_pencil(w):
    width = 100 * RUN + w.s
    turn = width / 2 / RUN                      # where the upright arms turn into the 52 degree diagonals
    outer = [(0, 100), (0, turn), (width / 2, 0), (width, turn), (width, 100)]
    inner = offset(outer, [-w.s, -w.d, -w.d, -w.s, 10])
    return P(outer).difference(P(inner))


def v_steep(w):
    width = 100 * RUN + w.s
    outer = [(0, 100), (width / 2, 0), (width, 100)]
    inner = offset(outer, [-w.d, -w.d, 10])
    return P(outer).difference(P(inner))


WAYS = {'1': ('now', F.g_v), '2': ('corner', v_corner), '3': ('pencil', v_pencil), '4': ('steep', v_steep)}


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    texts = {'lv': 'level volume over', 'vs': 'vs move save view'}
    for w in (REGULAR, BOLD):
        glyphs, bodies, kerns = V79.decided(w)
        for number, (label, draw) in WAYS.items():
            v = F.B42.at_left_zero(draw(w))
            assert v.is_valid and not hasattr(v, 'geoms'), (w.name, label)
            size = F.B42.write(v, folder / f'{w.name}-v-{number}.svg', (-12, v.bounds[2] + 12, -12, 112), f'V {number} {label} ({w.name})')
            report[f'{w.name}-v-{number}'] = {'width': round(v.bounds[2], 1), 'svg': [round(x, 2) for x in size]}
            gl, bo = dict(glyphs), dict(bodies)
            gl['v'] = bo['v'] = v
            for key, text in texts.items():
                line = V72.set_line_kerned(text, gl, bo, w, kerns)
                size = F.B42.write(line, folder / f'{w.name}-{key}-{number}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{text.upper()}, V {number} ({w.name})')
                report[f'{w.name}-{key}-{number}'] = {'svg': [round(x, 2) for x in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v['width'] for k, v in report.items() if 'width' in v})


if __name__ == '__main__':
    main()
