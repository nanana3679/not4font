"""Round v69. The user: "25" — the RA pair set apart by the 25 percent step of round v68 (Regular 18.9, Bold 14.3);
and "U J 모양 이어서 고를래" — go on to choose the shapes of the U and the J.
The five U shapes of round v62 (both lower corners cut 26 as now; one corner square and the other cut 40 or 52,
either way round), now at the narrowed Regular widths of round v68 (U 75, J 66) and in the Bold (U 100, J 88).
The J is drawn from each U (its upper left part taken off above 40) and numbered alike, so that the U and the J
can be chosen apart. Words set as decided: R spaced by its top, left wins, RA kerned 25 percent.
Needs shapely (PYTHONPATH). Usage: font-v73.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V72 = load('f72', 'font-v72.py')
V64 = load('f64', 'font-v64.py')
V71, F = V72.V71, V72.F
P, rect = F.P, F.rect
RA_STEP = 0.25
VERSIONS = [('1', 'now', (26, 26)), ('2', 'r-square-40', (40, 0)), ('3', 'r-square-52', (52, 0)), ('4', 'l-square-40', (0, 40)), ('5', 'l-square-52', (0, 52))]
WIDTHS = {'r16': (75, 66), 'bold': (100, 88)}


def font(w):
    """the glyphs as decided so far and the kerning of the RA pair"""
    glyphs, bodies = V71.regular_set(w, narrow=(w is V71.REGULAR))
    kerns = {('r', 'a'): RA_STEP * V72.full_kern(w, glyphs, bodies, 'r', 'a')}
    return glyphs, bodies, kerns


def u_and_j(w, cuts):
    uw, jw = WIDTHS[w.name]
    u = F.B42.at_left_zero(V64.u_cuts(w, uw, *cuts))
    j = F.B42.at_left_zero(V64.u_cuts(w, jw, *cuts).difference(P(rect(-1, 40, jw / 2, 101))))
    assert u.is_valid and j.is_valid
    return u, j


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (V71.REGULAR, F.BOLD):
        glyphs, bodies, kerns = font(w)
        report[f'{w.name}-ra-kern'] = round(kerns[('r', 'a')], 2)
        for number, label, cuts in VERSIONS:
            u, j = u_and_j(w, cuts)
            for name, shape in (('u', u), ('j', j)):
                size = F.B42.write(shape, folder / f'{w.name}-{name}-{number}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{name.upper()} {number} {label} ({w.name})')
                report[f'{w.name}-{name}-{number}'] = {'svg': [round(v, 2) for v in size], 'cuts': cuts}
            g, b = dict(glyphs), dict(bodies)
            g['u'] = b['u'] = u
            g['j'] = b['j'] = j
            for key, text in (('words', 'unit jump run'), ('words2', 'judge music bonus')):
                shape = V72.set_line_kerned(text, g, b, w, kerns)
                size = F.B42.write(shape, folder / f'{w.name}-{key}-{number}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()}, U and J {number} ({w.name})')
                report[f'{w.name}-{key}-{number}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v for k, v in report.items() if not isinstance(v, dict)})


if __name__ == '__main__':
    main()
