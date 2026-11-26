"""Round v76. The user: "2" — the V of number 2 (the 52 degree diagonal and an upright stem, the lower right corner cut
at 52 degrees so that the strokes meet in a point), in both weights as the U and J were.
decided(w) = the whole font as decided so far: font-v79.decided (G way b, square foot) with this V.
Draws the whole set in both weights, words, and the Regular small (the page sizes the small lines).
Needs shapely (PYTHONPATH). Usage: font-v81.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V80 = load('f80', 'font-v80.py')
V79, V72, F = V80.V79, V80.V72, V80.F
REGULAR, BOLD = V80.REGULAR, V80.BOLD


def decided(w):
    glyphs, bodies, kerns = V79.decided(w, square_foot=True)
    v = F.B42.at_left_zero(V80.v_corner(w))
    glyphs['v'] = bodies['v'] = v
    return glyphs, bodies, kerns


TEXTS = {
    'r16': {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'ui-1': 'song select', 'ui-2': 'high score 9876', 'ui-3': 'level 12 volume 85', 'ui-4': 'judge music bonus', 'ui-5': 'vs move save view'},
    'bold': {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'judgment': 'perfect great', 'judgment-2': 'good miss', 'menu': 'song select'},
}


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (REGULAR, BOLD):
        glyphs, bodies, kerns = decided(w)
        for name, shape in glyphs.items():
            assert shape.is_valid, (w.name, name)
        for key, text in TEXTS[w.name].items():
            shape = V72.set_line_kerned(text, glyphs, bodies, w, kerns)
            size = F.B42.write(shape, folder / f'{w.name}-{key}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name})')
            report[f'{w.name}-{key}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(report))


if __name__ == '__main__':
    main()
