"""Round v62. The user: "U 한쪽만 직각으로 하고 꺾이는쪽을 키우면 어떰?" — the U with one lower corner square and the
other corner cut larger. Both ways round (square on the right like the stem of the V, or on the left), the larger
cut at 40 or 52 tall (52 as the top of the A was cut in round v45), at 52 degrees. The J is the lower part of the U,
so it follows the U. Regular 16 and Bold.
Needs shapely (PYTHONPATH). Usage: font-v64.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = load('f57', 'font-v57.py')
P, rect, offset, RUN = F.P, F.rect, F.offset, F.RUN
REGULAR = F.Weight('r16', 16, 14, 15, 14, 4, 12)
VERSIONS = {'now': (26, 26), 'r-square-40': (40, 0), 'r-square-52': (52, 0), 'l-square-40': (0, 40), 'l-square-52': (0, 52)}


def u_cuts(w, width, bl, br):
    """the U with its lower left corner cut bl tall and its lower right br tall (0: square)"""
    points, dists = [(0, 100)], []
    dists.append(-w.s)                                  # left side, from the top down
    if bl:
        points += [(0, bl), (bl * RUN, 0)]
        dists.append(-w.corner)
    else:
        points.append((0, 0))
    dists.append(-w.ho)                                 # bottom
    if br:
        points += [(width - br * RUN, 0), (width, br)]
        dists.append(-w.corner)
    else:
        points.append((width, 0))
    dists.append(-w.s)                                  # right side, up
    points.append((width, 100))
    dists.append(10)                                    # the top, pushed out so that the U is open
    inner = offset(points, dists)
    return P(points).difference(P(inner))


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (REGULAR, F.BOLD):
        for label, (bl, br) in VERSIONS.items():
            u = F.B42.at_left_zero(u_cuts(w, 100, bl, br))
            j = F.B42.at_left_zero(u_cuts(w, 88, bl, br).difference(P(rect(-1, 40, 44, 101))))
            assert u.is_valid and j.is_valid, (w.name, label)
            for name, shape in (('u', u), ('j', j)):
                width = shape.bounds[2]
                size = F.B42.write(shape, folder / f'{w.name}-{name}-{label}.svg', (-12, width + 12, -12, 112), f'{name.upper()} {label} ({w.name})')
                report[f'{w.name}-{name}-{label}'] = {'svg': [round(v, 2) for v in size]}
            glyphs, bodies = F.glyph_set(w)
            glyphs['u'] = bodies['u'] = u
            glyphs['j'] = bodies['j'] = j
            shape = F.set_line('unit jump run', glyphs, bodies, w.sp)
            size = F.B42.write(shape, folder / f'{w.name}-words-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'UNIT JUMP RUN, U {label} ({w.name})')
            report[f'{w.name}-words-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(report))


if __name__ == '__main__':
    main()
