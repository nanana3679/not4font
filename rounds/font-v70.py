"""Round v67. The user: "p도 r에 맞춰야하지않나" — the P should match the R. The P's bowl takes the R's bowl width
(72 in the Regular 16, 88 in the Bold; it was 96), the same height (from bowl0), so P and R share one bowl.
Words set with the R spaced by its top and the left-wins cut (font-v69.py).
Needs shapely (PYTHONPATH). Usage: font-v70.py <out folder>"""
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


V69 = load('f69', 'font-v69.py')
F = V69.F


def p_like_r(w):
    return unary_union([F.stem(w), F.bowl(w, V69.BOWL[w.name], w.bowl0, 100, w.h, w.ho)])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (V69.REGULAR, F.BOLD):
        glyphs, bodies = V69.glyphs_for(w)
        old_p = glyphs['p']
        new_p = F.B42.at_left_zero(p_like_r(w))
        for name, shape in (('p-old', old_p), ('p-new', new_p), ('r', glyphs['r'])):
            width = shape.bounds[2]
            size = F.B42.write(shape, folder / f'{w.name}-{name}.svg', (-12, width + 12, -12, 112), f'{name} ({w.name})')
            report[f'{w.name}-{name}'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
        for label, p in (('old', old_p), ('new', new_p)):
            g, b = dict(glyphs), dict(bodies)
            g['p'] = b['p'] = p
            for key, text in (('words', 'proper paper'), ('judgment', 'perfect'), ('pr', 'pr rp')):
                shape = V69.set_line_cut(text, g, b, w)
                size = F.B42.write(shape, folder / f'{w.name}-{key}-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name}, P {label})')
                report[f'{w.name}-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v.get('width', v['svg'][0]) for k, v in report.items() if 'p-' in k or k.endswith('-r')})


if __name__ == '__main__':
    main()
