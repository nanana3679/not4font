"""Round v49. The user: "B 8 위아래 폭 같게" (B and 8 as wide at the top as at the bottom). Both rings of the B and
of the 8 are now 96 wide (the upper ones were 88). Writes the new B and 8 beside the old ones, and the set again.
Needs shapely (PYTHONPATH). Usage: alphabet-v49.py <out folder>"""
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


A48 = load('a48', 'alphabet-v48.py')
J, B42, B43, B44 = A48.J, A48.B42, A48.B43, A48.B44
P, rect, S, ring = A48.P, A48.rect, A48.S, A48.ring


def g_b(width=96):
    return unary_union([ring(width, 38, 100, 24, 24), ring(width, 0, 62, 24, 24), P(rect(0, 0, S, 100))])


def g_8(width=96):
    return unary_union([ring(width, 38, 100, 24, 24), ring(width, 0, 62, 24, 24)])


A48.DRAW['b'] = g_b
A48.DRAW['8'] = g_8


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = A48.full_set()
    report = {}
    old = {'b-old': A48.g_b if False else None}
    for name, shape in (('b', glyphs['b']), ('8', glyphs['8'])):
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), f'Bold {name.upper()}, rings of one width')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    lines = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'b8': 'b8b8'}
    for key, text in lines.items():
        drawn, _ = B43.set_word(list(text), glyphs, bodies)
        shape = B44.joined(drawn)
        size = B42.write(shape, folder / f'line-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), text.upper())
        report[f'line-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
