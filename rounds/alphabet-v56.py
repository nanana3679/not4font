"""Round v56. The user, asked whether the diagonals of the font go to 26: "로고 26도 괜찮긴했는데" (the logo at 26
was fine too). The font with every diagonal at 26 (N, K, M, W, R thinned as in round v55), and the wordmark of
edition 1 with its red diagonal at 26 beside the frozen one at 30 (the red weight was left for the finish; 30 and 26
were both fine then).
Needs shapely (PYTHONPATH). Usage: alphabet-v56.py <out folder>"""
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


A55 = load('a55', 'alphabet-v55.py')
A48 = A55.A48
B42, B43, B44 = A48.B42, A48.B43, A48.B44
E1 = load('e1', 'edition1-v41.py')


def font():
    A55.chosen()
    for name, draw in A55.THIN.items():
        A48.DRAW[name] = draw
    return A48.full_set()


def wordmark(red_width, folder, name):
    C, V36 = E1.C, E1.V36
    C.SLASH_ROOM = 0
    C.CHANNEL = C.SLASH_WEIGHT
    base = dict(V36.BASE, red_width=red_width)
    concept = C.concept_a(**base, **E1.OPTIONS)
    concept['name'] = name
    out, size, frame = C.write(concept, folder)
    light = out.read_text().replace('fill="#111111"', 'fill="#e6ecf5"')
    target = folder / f'{name}-light.svg'
    target.write_text(light)
    n, _ = V36.n_and_o(concept, V36.N_WIDTH + V36.GAP)
    mark = {'name': f'{name}-mark', 'ink': rotate(n, V36.UPRIGHT, origin=(60, 50)), 'red': rotate(concept['red'], V36.UPRIGHT, origin=(60, 50)), 'slash': concept['slash']}
    mark_out, _, _ = C.write(mark, folder)
    (folder / f'{name}-mark-light.svg').write_text(mark_out.read_text().replace('fill="#111111"', 'fill="#e6ecf5"'))
    return {'size': size, 'frame': frame, 'slash': concept['slash']}


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {'red30': wordmark(30, folder, 'wordmark-red30'), 'red26': wordmark(26, folder, 'wordmark-red26')}
    glyphs, bodies = font()
    lines = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789',
             'perfect': 'perfect', 'great': 'great', 'good': 'good', 'miss': 'miss', 'notak': 'not4k'}
    for key, text in lines.items():
        drawn, _ = B43.set_word(list(text), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'line-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), text.upper())
        report[f'line-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: (v.get('size') or v.get('svg')) for k, v in report.items()}))


if __name__ == '__main__':
    main()
