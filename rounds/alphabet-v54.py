"""Round v54. The user: "숫자 너비 달라도 ㄱㅊ 6 9가기둥평평한게 나으려나" — numerals may keep their own widths; and
would the 6 and the 9 be better with a flat stem? Their stem side had a notch in the middle, where the cut corners
of the two stacked rings met. Here the stem side runs straight from the lower cut corner to the upper one, and the
counters are square on that side (as the B became in round v50); the outer corners at the top and the bottom stay
cut. The 9 is the 6 turned half round, as before.
Needs shapely (PYTHONPATH). Usage: alphabet-v54.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import rotate
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A53 = load('a53', 'alphabet-v53.py')
A52, A51, A50 = A53.A52, A53.A51, A53.A50
A48 = A50.A48
J, B42, B43, B44 = A48.J, A48.B42, A48.B43, A48.B44
P, rect, S, R, CORNER = A48.P, A48.rect, A48.S, A48.R, A48.CORNER


def g_6_flat(width=96):
    # the upper part: rounded at the top left, square at the lower left where the stem runs on; open on the right
    upper_outer = [(0, 38), (width - R, 38), (width, 64), (width, 74), (width - R, 100), (R, 100), (0, 74)]
    upper_inner = J.offset(upper_outer, [-24, -CORNER, -S, -CORNER, -24, -CORNER, -S])
    upper = P(upper_outer).difference(P(upper_inner)).difference(P(rect(width / 2, 37, width + 1, 76)))
    # the lower bowl: rounded at the bottom left and on the right, square at the upper left where the stem runs on
    lower_outer = [(R, 0), (width - R, 0), (width, 26), (width, 36), (width - R, 62), (0, 62), (0, 26)]
    lower_inner = J.offset(lower_outer, [-24, -CORNER, -S, -CORNER, -24, -S, -CORNER])
    lower = P(lower_outer).difference(P(lower_inner))
    return unary_union([upper, lower])


def g_9_flat():
    return rotate(g_6_flat(), 180, origin=(48, 50))


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    A48.DRAW['b'] = A50.g_b
    A48.DRAW['q'] = lambda: A51.g_q(40)
    A48.DRAW['z'] = A53.z_split_clean
    report = {}
    shapes = {'6-now': A48.g_6(), '6-flat': g_6_flat(), '9-now': A48.g_9(), '9-flat': g_9_flat()}
    for name, shape in shapes.items():
        shape = B42.at_left_zero(shape)
        assert shape.is_valid, name
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), name)
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    for label, six, nine in (('now', A48.g_6, A48.g_9), ('flat', g_6_flat, g_9_flat)):
        A48.DRAW['6'], A48.DRAW['9'] = six, nine
        glyphs, bodies = A48.full_set()
        for key, text in (('digits', '0123456789'), ('sample', '1969')):
            drawn, _ = B43.set_word(list(text), glyphs, bodies)
            line = B44.joined(drawn)
            size = B42.write(line, folder / f'line-{key}-{label}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{text} with the 6 and 9 {label}')
            report[f'line-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
