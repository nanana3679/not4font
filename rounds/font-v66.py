"""Round v64. The user put it plainly: "R윗부분 너비를 좁게 해달라는 말이야" — "like the K" meant the R narrower at the
top: the K's arm reaches less far to the right at the top than its leg at the baseline. The R here keeps its leg
as it is (flat top, reaching the full width at the baseline) and narrows its bowl, in two steps, so that the leg
runs out beyond the bowl as the K's leg runs out beyond its arm. Regular 16 and Bold, beside the R as it is and the K.
Needs shapely (PYTHONPATH). Usage: font-v66.py <out folder>"""
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


F = load('f57', 'font-v57.py')
P, rect, RUN = F.P, F.rect, F.RUN
REGULAR = F.Weight('r16', 16, 14, 15, 14, 4, 12)
STEPS = {'r16': (84, 72), 'bold': (88, 78)}


def r_narrow(w, bowl_width, width=100):
    top = w.bowl0 - w.g
    leg = P([(width - w.ac, 0), (width, 0), (width - top * RUN, top), (width - w.ac - top * RUN, top)])
    return unary_union([F.stem(w), F.bowl(w, bowl_width, w.bowl0, 100, w.h, w.ho), leg])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (REGULAR, F.BOLD):
        glyphs, bodies = F.glyph_set(w)
        a, b = STEPS[w.name]
        shapes = {'r-now': glyphs['r'], f'r-{a}': F.B42.at_left_zero(r_narrow(w, a)), f'r-{b}': F.B42.at_left_zero(r_narrow(w, b)), 'k': glyphs['k']}
        for name, shape in shapes.items():
            assert shape.is_valid, (w.name, name)
            width = shape.bounds[2]
            size = F.B42.write(shape, folder / f'{w.name}-{name}.svg', (-12, width + 12, -12, 112), f'{name} ({w.name})')
            report[f'{w.name}-{name}'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
        for label in ('r-now', f'r-{a}', f'r-{b}'):
            g, bo = dict(glyphs), dict(bodies)
            g['r'] = bo['r'] = shapes[label]
            shape = F.set_line('rank marker error', g, bo, w.sp)
            size = F.B42.write(shape, folder / f'{w.name}-words-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'RANK MARKER ERROR ({w.name}, {label})')
            report[f'{w.name}-words-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v.get('width', v['svg'][0]) for k, v in report.items()})


if __name__ == '__main__':
    main()
