"""Round v71. The user: "90 u2 j4" — the Regular's boxy letters at 90 percent of the widths taken over from the Bold;
the U of number 2 (right corner square, left cut 40) and the J of number 4 (left corner square, right cut 40), in
both weights (as the U and J shapes were shown in both).
decided(w) gives the whole font as decided so far, with the RA kerning, for each weight. The page shows the whole
set in both weights, words, and the Regular small (letters 14 px tall).
Needs shapely (PYTHONPATH). Usage: font-v76.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V75 = load('f75', 'font-v75.py')
V73, V72, V71, F = V75.V73, V75.V72, V75.V71, V75.F
V64 = V73.V64
P, rect = F.P, F.rect
REGULAR, BOLD = V71.REGULAR, F.BOLD
REGULAR_WIDTH = 0.9
U_CUTS = (40, 0)        # number 2: lower left cut 40, lower right square
J_CUTS = (0, 40)        # number 4: lower left square, lower right cut 40


def decided(w):
    if w is REGULAR:
        glyphs, bodies, _ = V75.regular_at(REGULAR_WIDTH)
        factor = REGULAR_WIDTH
    else:
        glyphs, bodies = V71.regular_set(w, narrow=False)
        factor = 1.0
    uw, jw = round(100 * factor), round(88 * factor)
    u = F.B42.at_left_zero(V64.u_cuts(w, uw, *U_CUTS))
    j = F.B42.at_left_zero(V64.u_cuts(w, jw, *J_CUTS).difference(P(rect(-1, 40, jw / 2, 101))))
    assert u.is_valid and j.is_valid
    glyphs['u'] = bodies['u'] = u
    glyphs['j'] = bodies['j'] = j
    kerns = {('r', 'a'): V73.RA_STEP * V72.full_kern(w, glyphs, bodies, 'r', 'a')}
    return glyphs, bodies, kerns


TEXTS = {
    'r16': {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'ui-1': 'song select', 'ui-2': 'high score 9876', 'ui-3': 'level 12 volume 85', 'ui-4': 'judge music bonus'},
    'bold': {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'judgment': 'perfect great', 'judgment-2': 'good miss', 'menu': 'song select'},
}


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (REGULAR, BOLD):
        glyphs, bodies, kerns = decided(w)
        report[f'{w.name}-widths'] = {n: round(glyphs[n].bounds[2], 1) for n in 'oeujprv'}
        report[f'{w.name}-ra-kern'] = round(kerns[('r', 'a')], 2)
        for key, text in TEXTS[w.name].items():
            shape = V72.set_line_kerned(text, glyphs, bodies, w, kerns)
            size = F.B42.write(shape, folder / f'{w.name}-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name})')
            report[f'{w.name}-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v for k, v in report.items() if not (isinstance(v, dict) and 'svg' in v)})


if __name__ == '__main__':
    main()
