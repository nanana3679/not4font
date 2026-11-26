"""Round v53. The user: "40 n처럼 잘랐을때 조그만 조각 없애줘" — the tail of the Q with its top at 40, and the Z split
like the N without the small pieces the cut leaves (the corners of the bars beyond the diagonal: a top bar's lower
right and a bottom bar's upper left, about 80 square units each). Pieces under 200 square units are dropped, the
word rule "slivers left after a cut are removed" applied inside a letter. The whole set again with every choice:
A built like the 4, G with a spur of 24, horizontals 24, B with counters straight on the left, B and 8 with rings of
one width, Q tail top 40, Z split.
Needs shapely (PYTHONPATH). Usage: alphabet-v53.py <out folder>"""
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


A52 = load('a52', 'alphabet-v52.py')
A51, A50 = A52.A51, A52.A50
A48 = A50.A48
B42, B43, B44 = A48.B42, A48.B43, A48.B44
SLIVER = 200


def without_slivers(shape):
    pieces = [piece for piece in getattr(shape, 'geoms', [shape]) if piece.area >= SLIVER]
    return unary_union(pieces)


def z_split_clean():
    return without_slivers(A52.z_stencil())


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    A48.DRAW['b'] = A50.g_b
    A48.DRAW['q'] = lambda: A51.g_q(40)
    A48.DRAW['z'] = z_split_clean
    glyphs, bodies = A48.full_set()
    report = {}
    before = A52.z_stencil()
    report['z-pieces'] = {'before': [round(p.area, 1) for p in getattr(before, 'geoms', [before])], 'after': [round(p.area, 1) for p in getattr(glyphs['z'], 'geoms', [glyphs['z']])]}
    for name in ('z', 'q'):
        shape = glyphs[name]
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), f'Bold {name.upper()}')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    old = B42.at_left_zero(before)
    size = B42.write(old, folder / 'glyph-z-before.svg', (-12, old.bounds[2] + 12, -12, 112), 'Z split, with the small pieces')
    report['z-before'] = {'svg': [round(v, 2) for v in size]}
    lines = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789',
             'perfect': 'perfect', 'great': 'great', 'good': 'good', 'miss': 'miss', 'zebra': 'zebra', 'maze': 'maze', 'quest': 'quest'}
    for key, text in lines.items():
        drawn, _ = B43.set_word(list(text), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'line-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), text.upper())
        report[f'line-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report['z-pieces']))
    print(json.dumps({k: v.get('width', v.get('svg', [0])[0]) for k, v in report.items() if k != 'z-pieces'}))


if __name__ == '__main__':
    main()
