"""Round v70 (continued). The user: "근데 글자들 너비가 너무 좁아진 기분이 드는데?" — the letters feel too narrow now.
In round v68 the boxy letters of the Regular (B C D E F G H J L O Q S T U, 0 2 3 5 6 8 9) were narrowed to three
quarters as the P was. Here the same letters at six steps between the widths taken over from the Bold (100 percent)
and three quarters (75 percent, as now): 100 95 90 85 80 75. The P and the R keep the bowl of 72 that was chosen;
the U and the J are drawn as now (both corners 26). Words set as decided (RA kerned 25 percent).
Needs shapely (PYTHONPATH). Usage: font-v75.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import rotate


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V73 = load('f73', 'font-v73.py')
V72, V71, F = V73.V72, V73.V71, V73.F
V69, V70 = V71.V69, V71.V70
STEPS = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75)
TEXTS = {'ui': 'high score 9876', 'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789'}


def regular_at(factor):
    """the Regular 16 as decided, with the boxy letters at factor times the widths taken over from the Bold"""
    w = V71.REGULAR
    glyphs, bodies = V69.glyphs_for(w)
    glyphs['p'] = bodies['p'] = F.B42.at_left_zero(V70.p_like_r(w))
    for name, width in V71.WIDTHS.items():
        glyphs[name] = bodies[name] = F.B42.at_left_zero(F.DRAW[name](w, width=round(width * factor)))
    six = round(96 * factor)
    glyphs['9'] = bodies['9'] = F.B42.at_left_zero(rotate(F.g_6(w, width=six), 180, origin=(six / 2, 50)))
    kerns = {('r', 'a'): V73.RA_STEP * V72.full_kern(w, glyphs, bodies, 'r', 'a')}
    return glyphs, bodies, kerns


def check():
    """the ends match what was shown before: 75 percent is round v68, 100 percent the set before it"""
    for factor, narrow in ((0.75, True), (1.0, False)):
        mine, _, _ = regular_at(factor)
        old, _ = V71.regular_set(V71.REGULAR, narrow)
        assert all(mine[n].symmetric_difference(old[n]).area < 1e-6 for n in old), factor


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    check()
    report = {}
    for factor in STEPS:
        glyphs, bodies, kerns = regular_at(factor)
        tag = f'{round(factor * 100):03d}'
        report[f'widths-{tag}'] = {n: round(glyphs[n].bounds[2], 1) for n in 'oeu'}
        for key, text in TEXTS.items():
            shape = V72.set_line_kerned(text, glyphs, bodies, V71.REGULAR, kerns)
            size = F.B42.write(shape, folder / f'r16-{key}-{tag}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} (Regular 16, {tag} percent)')
            report[f'r16-{key}-{tag}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v for k, v in report.items() if k.startswith('widths')})


if __name__ == '__main__':
    main()
