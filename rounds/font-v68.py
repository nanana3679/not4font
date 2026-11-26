"""Round v65 (continued). While the R was being spaced by its top, the user added: "R 다리를 위쪽으로 좀더 늘려줘 움푹
파인부위없게" — the leg longer upwards, with no dent. With a narrowed bowl a wedge opened between the flat top of the
leg and the cut lower right corner of the bowl. Here the leg runs on upwards along its own slope and is cut 1 gap
from the stem and the bowl, so its top follows the bowl round its corner and the wedge is filled.
The R is then set measured by its top (the user's proposal), and, for comparison, by the rule of the 4 (the leg
running out beyond the bowl by just the letter space). Regular 16 and Bold.
Needs shapely (PYTHONPATH). Usage: font-v68.py <out folder>"""
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
R66 = load('f66', 'font-v66.py')
P, rect, RUN = F.P, F.rect, F.RUN
REGULAR = R66.REGULAR


def r_long_leg(w, bowl_width, width=100):
    upper = unary_union([F.stem(w), F.bowl(w, bowl_width, w.bowl0, 100, w.h, w.ho)])
    band = P([(width - w.ac, 0), (width, 0), (width - 100 * RUN, 100), (width - w.ac - 100 * RUN, 100)])
    cut = band.difference(upper.buffer(w.g, join_style='mitre'))
    leg = next(piece for piece in getattr(cut, 'geoms', [cut]) if piece.bounds[1] < 1e-6)
    return unary_union([upper, leg]), upper


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    steps = {'r16': (84, 72), 'bold': (88, 78)}
    for w in (REGULAR, F.BOLD):
        glyphs, bodies = F.glyph_set(w)
        four_rule = round(100 - w.sp)
        for bowl_width in list(steps[w.name]) + [four_rule]:
            old = F.B42.at_left_zero(R66.r_narrow(w, bowl_width))
            new, upper = r_long_leg(w, bowl_width)
            new, upper = F.B42.at_left_zero(new), F.B42.at_left_zero(upper)
            assert new.is_valid
            for label, shape in (('old', old), ('long', new)):
                width = shape.bounds[2]
                size = F.B42.write(shape, folder / f'{w.name}-r{bowl_width}-{label}.svg', (-12, width + 12, -12, 112), f'R {bowl_width} {label} ({w.name})')
                report[f'{w.name}-r{bowl_width}-{label}'] = {'svg': [round(v, 2) for v in size]}
            g, b = dict(glyphs), dict(bodies)
            g['r'], b['r'] = new, upper
            for key, text in (('words', 'rank marker error'), ('pairs', 're ra rn rt ro')):
                shape = F.set_line(text, g, b, w.sp)
                size = F.B42.write(shape, folder / f'{w.name}-r{bowl_width}-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name}, R {bowl_width}, by its top)')
                report[f'{w.name}-r{bowl_width}-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(report))


if __name__ == '__main__':
    main()
