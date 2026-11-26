"""Round v47. The user chose the A built like the 4 and horizontals of 24, and asked whether the heavy lower right of
the G (the spur filled down to the lower bar in round v45, 52 wide against stems of 30) is character. It is not:
it was filled only to close a notch. Two ways that keep the weight even, beside it:
  g-now  round v45: the lower right of the counter filled from the lower bar up to 56
  g-bar  a spur 24 thick (38 to 62) inwards from the right side, a slit under it; the opening above it 62 to 74
  g-open no spur: the right side rises from the lower corner to half the height (50), open above
Also GREAT and GOOD with each G and the A built like the 4.
Needs shapely (PYTHONPATH). Usage: judgment-v47.py <out folder>"""
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


J46 = load('j46', 'judgment-v46.py')
J = J46.J
B42, B43, B44 = J.B42, J.B43, J.B44
P, rect, S = J.P, J.rect, J.S


def g_bar(width=104):
    body = J.ring(width, 0, 100, 26, 26).difference(P(rect(width / 2, 62, width + 1, 74)))
    return unary_union([body, P(rect(width - S - 22, 38, width - S + 1, 62))])


def g_open(width=104):
    return J.ring(width, 0, 100, 26, 26).difference(P(rect(width / 2, 50, width + 1, 74)))


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = B43.glyph_set()
    for name, shape in {'p': J.g_p(), 'e': J.g_e(), 'r': J.g_r(), 'f': J.g_f(), 'c': J.g_c(), 'd': J.g_d(), 'm': J.g_m(), 'i': J.g_i(), 's': J.g_s(), 'a': J46.a_like_four()}.items():
        glyphs[name] = bodies[name] = B42.at_left_zero(shape)
    versions = {'g-now': J.g_g(), 'g-bar': g_bar(), 'g-open': g_open()}
    report = {}
    for name, shape in versions.items():
        shape = B42.at_left_zero(shape)
        assert shape.is_valid, name
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-{name}.svg', (-12, width + 12, -12, 112), name)
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
        g, b = dict(glyphs), dict(bodies)
        g['g'] = b['g'] = shape
        for word in ('great', 'good'):
            drawn, _ = B43.set_word(list(word), g, b)
            line = B44.joined(drawn)
            size = B42.write(line, folder / f'word-{word}-{name}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{word.upper()} with {name}')
            report[f'word-{word}-{name}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
