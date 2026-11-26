"""Round v55. The user took the flat 6 and 9 ("ㅇㅋ") and was unsure about the two diagonal weights ("아까말한
대각선 길이 다른건 잘모르겠음"). To make the question visible: the letters whose diagonals are 30 across (N, K, M,
W, R, which came from the logo) beside the same letters with diagonals of 26 (as in the 4, A, V, X, Y, Z, 2, 7),
in words and in the whole set. Stems stay 30; the logo itself keeps its own N.
Needs shapely (PYTHONPATH). Usage: alphabet-v55.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import scale
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A54 = load('a54', 'alphabet-v54.py')
A53, A51, A50 = A54.A53, A54.A51, A54.A50
A48 = A50.A48
J, B42, B43, B44, C = A48.J, A48.B42, A48.B43, A48.B44, A48.C
P, rect, S, GAP = A48.P, A48.rect, A48.S, A48.GAP
D = 26


def n26():
    diagonal = P(C.box(C.blade((21, 100), (99, 0), D, before=60, after=60), y0=0, y1=100))
    room = diagonal.buffer(GAP, join_style='mitre')
    stems = [P(rect(0, 0, S, 100)).difference(room), P(rect(120 - S, 0, 120, 100)).difference(room)]
    return unary_union(stems + [diagonal])


def k26(x=0, gap=GAP):
    stem = C.rect(x, 0, x + S, 100)
    vertex = (x + S, 38)
    arm_axis = C.add(vertex, C.UPPER_LEFT, S / 2)
    arm = C.box(C.blade(arm_axis, C.add(arm_axis, C.UP, 120), D, before=40), x0=x, y1=100)
    gap_at = C.add(vertex, C.LOWER_RIGHT, gap)
    leg_axis = (x + S + 24, 40)
    leg = C.box(C.blade(C.add(leg_axis, C.DOWN, -60), C.add(leg_axis, C.DOWN, 120), D), y0=0)
    leg = C.keep(leg, gap_at, C.add(gap_at, C.UP, 50), (x + S + 60, 5))
    return unary_union([P(stem), P(arm), P(leg)])


def m26(width=136):
    def blade(start, direction):
        far = (start[0] + direction[0] * 200, start[1] + direction[1] * 200)
        return P(C.box(C.blade(start, far, D, before=40), y1=100))
    left = blade((21, 100), (C.COS, -C.SIN)).intersection(P(rect(-100, -100, width / 2, 200)))
    right = blade((width - 21, 100), (-C.COS, -C.SIN)).intersection(P(rect(width / 2, -100, width + 100, 200)))
    v = unary_union([left, right]).intersection(P(rect(0, 0, width, 100)))
    room = v.buffer(GAP, join_style='mitre')
    return unary_union([P(rect(0, 0, S, 100)).difference(room), P(rect(width - S, 0, width, 100)).difference(room), v])


def w26():
    return scale(m26(), yfact=-1, origin=(68, 50))


def r26(width=100):
    leg_across = D / C.SIN
    top = 34 - GAP
    leg = P([(width - leg_across, 0), (width, 0), (width - top * C.RUN, top), (width - leg_across - top * C.RUN, top)])
    return unary_union([P(rect(0, 0, S, 100)), J.bowl(width, 34), leg])


THIN = {'n': n26, 'k': k26, 'm': m26, 'w': w26, 'r': r26}


def chosen():
    A48.DRAW['b'] = A50.g_b
    A48.DRAW['q'] = lambda: A51.g_q(40)
    A48.DRAW['z'] = A53.z_split_clean
    A48.DRAW['6'] = A54.g_6_flat
    A48.DRAW['9'] = A54.g_9_flat


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    chosen()
    glyphs, bodies = A48.full_set()
    thin_glyphs, thin_bodies = dict(glyphs), dict(bodies)
    for name, draw in THIN.items():
        thin_glyphs[name] = thin_bodies[name] = B42.at_left_zero(draw())
    report = {}
    for name in ('n', 'k', 'm', 'w', 'r', 'z', 'x'):
        for label, g in (('30', glyphs), ('26', thin_glyphs)):
            if name in ('z', 'x') and label == '30':
                continue
            shape = g[name]
            assert shape.is_valid, (name, label)
            width = shape.bounds[2]
            size = B42.write(shape, folder / f'glyph-{name}{label}.svg', (-12, width + 12, -12, 112), f'{name.upper()}, diagonals {label}')
            report[f'{name}{label}'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    lines = {'network': 'network', 'market': 'market', 'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz'}
    for key, text in lines.items():
        for label, g, b in (('30', glyphs, bodies), ('26', thin_glyphs, thin_bodies)):
            drawn, _ = B43.set_word(list(text), g, b)
            shape = B44.joined(drawn)
            size = B42.write(shape, folder / f'line-{key}-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()}, diagonals {label}')
            report[f'line-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
