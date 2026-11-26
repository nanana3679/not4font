"""Round v74. The user: "B로하고 ㄱ 아래부분사선으로 안깎고 직각으로해봐" — the G is way b (the ㄱ's stem down to the
baseline, the C's bottom arm stopping one gap before it); and try the foot of the ㄱ square instead of cut at 52
degrees (the ring's lower right corner).
decided(w) = the whole font as decided so far (font-v76.decided) with the G of way b; square_foot chooses the foot.
Needs shapely (PYTHONPATH). Usage: font-v79.py <out folder>"""
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


V78 = load('f78', 'font-v78.py')
V76, V72, F = V78.V76, V78.V72, V78.F
P, rect = F.P, F.rect
REGULAR, BOLD = V76.REGULAR, V76.BOLD
WIDTH = V78.WIDTH


def g_parted(w, width, square_foot):
    """the G parted into the C and the ㄱ by an upright gap; the ㄱ's foot square or cut as the ring's corner"""
    body, jaw = V78.parts(w, width)
    c = body.difference(P(rect(width / 2, w.ho, width + 1, 100 - w.ho)))
    if square_foot:
        stem = P(rect(width - w.s, 0, width, w.m1))
    else:
        stem = body.intersection(P(rect(width - w.s, -1, width + 1, w.m1)))
    hook = unary_union([jaw, stem])
    c = c.difference(hook.buffer(w.g, join_style='mitre'))
    least = 200 * (w.s / 30) ** 2
    shape = unary_union([F.without_slivers(c, least), F.without_slivers(hook, least)])
    assert shape.is_valid and len(shape.geoms) == 2
    return F.B42.at_left_zero(shape)


def decided(w, square_foot=True):
    glyphs, bodies, kerns = V76.decided(w)
    g = g_parted(w, WIDTH[w.name], square_foot)
    glyphs['g'] = bodies['g'] = g
    return glyphs, bodies, kerns


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    texts = {'r16': {'words': 'song settings high', 'words2': 'progress login gauge'}, 'bold': {'words': 'good great', 'words2': 'song gauge'}}
    for w in (REGULAR, BOLD):
        cut = g_parted(w, WIDTH[w.name], False)
        assert cut.symmetric_difference(F.B42.at_left_zero(V78.split(w, WIDTH[w.name], 'b'))).area < 1e-6, 'way b of round v73'
        for label, square in (('cut', False), ('square', True)):
            glyphs, bodies, kerns = decided(w, square)
            g = glyphs['g']
            size = F.B42.write(g, folder / f'{w.name}-g-{label}.svg', (-12, g.bounds[2] + 12, -12, 112), f'G {label} ({w.name})')
            report[f'{w.name}-g-{label}'] = {'svg': [round(v, 2) for v in size]}
            for key, text in texts[w.name].items():
                line = V72.set_line_kerned(text, glyphs, bodies, w, kerns)
                size = F.B42.write(line, folder / f'{w.name}-{key}-{label}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{text.upper()}, G foot {label} ({w.name})')
                report[f'{w.name}-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(report))


if __name__ == '__main__':
    main()
