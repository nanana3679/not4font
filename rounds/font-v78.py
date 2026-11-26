"""Round v73. The user: "직관적이진않네 그럼 c 와 ㄱ 획을 분리만 해볼까" — the G made from the C and the Q's tail is not
intuitive; instead keep the present G and only separate its two strokes: the C (top arm, left side, bottom arm) and
the ㄱ (the jaw and the right side below it), by one stencil gap.
They meet at the lower right corner, so there are three ways to part them:
  a  across   the C keeps its whole bottom arm; the ㄱ's stem stops one gap above it (the ㄱ hangs free)
  b  upright  the ㄱ's stem runs down to the baseline with the corner; the bottom arm stops one gap before it
  c  slanted  one gap at 52 degrees (falling, as the N's diagonal and the K's leg) from the inner corner down
              through the outer corner; the ㄱ's stem ends in a point
Widths as now (Regular 94, Bold 104). Nothing else changes.
Needs shapely (PYTHONPATH). Usage: font-v78.py <out folder>"""
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


V76 = load('f76', 'font-v76.py')
V72, F = V76.V72, V76.F
P, rect = F.P, F.rect
REGULAR, BOLD = V76.REGULAR, V76.BOLD
WIDTH = {'r16': 94, 'bold': 104}


def parts(w, width):
    """the present G (g_g) as its ring body and its jaw"""
    body = F.ring(w, width, 0, 100, w.ho, w.ho).difference(P(rect(width / 2, w.m1, width + 1, 100 - w.ho)))
    jaw = P(rect(width - w.s - 22, w.m0, width - w.s + 1, w.m1))
    return body, jaw


def split(w, width, way):
    """the C (top arm, left side, bottom arm up to ho) and the ㄱ (jaw and right side), parted one gap"""
    body, jaw = parts(w, width)
    least = 200 * (w.s / 30) ** 2
    # the C: the ring without its right part between the arms (that part, with the inner corner, goes to the ㄱ)
    c = body.difference(P(rect(width / 2, w.ho, width + 1, 100 - w.ho)))
    band = P(rect(width - w.s, -1, width + 1, w.m1))
    if way == 'a':
        stem = body.intersection(band).intersection(P(rect(-1, w.ho, width + 1, w.m1)))
        hook = unary_union([jaw, stem]).difference(c.buffer(w.g, join_style='mitre'))
    elif way == 'b':
        hook = unary_union([jaw, body.intersection(band)])
        c = c.difference(hook.buffer(w.g, join_style='mitre'))
    else:
        # a falling line at 52 degrees through the meeting of the arm's top (ho) and the stem's inner edge
        x0, y0, far = width - w.s, w.ho, 300
        right = P([(x0 - far * F.RUN, y0 + far), (x0 + far * F.RUN, y0 - far), (x0 + 2 * far, y0 - far), (x0 + 2 * far, y0 + far)])
        stem = body.intersection(right).intersection(unary_union([band, P(rect(-1, -1, width + 1, w.ho))]))
        hook = unary_union([jaw, stem])
        # the gap: the same line moved one gap to the lower left; the arm ends on it (only the arm is near it)
        n = (-1 / (1 + F.RUN ** 2) ** 0.5, -F.RUN / (1 + F.RUN ** 2) ** 0.5)
        x1, y1 = x0 + w.g * n[0], y0 + w.g * n[1]
        gap_right = P([(x1 - far * F.RUN, y1 + far), (x1 + far * F.RUN, y1 - far), (x1 + 2 * far, y1 - far), (x1 + 2 * far, y1 + far)])
        c = c.difference(gap_right.intersection(P(rect(-1, -1, width + 1, w.ho + 1))))
    c = F.without_slivers(c, least)
    hook = F.without_slivers(hook, least)
    shape = unary_union([c, hook])
    assert shape.is_valid and len(getattr(shape, 'geoms', [shape])) == 2, way
    return shape


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    texts = {'r16': {'words': 'song settings high', 'words2': 'progress login gauge'}, 'bold': {'words': 'good great', 'words2': 'song gauge'}}
    for w in (REGULAR, BOLD):
        glyphs, bodies, kerns = V76.decided(w)
        width = WIDTH[w.name]
        body, jaw = parts(w, width)
        assert F.B42.at_left_zero(unary_union([body, jaw])).symmetric_difference(glyphs['g']).area < 1e-6, 'the present G'
        versions = {'now': glyphs['g']}
        for way in 'abc':
            versions[way] = F.B42.at_left_zero(split(w, width, way))
        for label, shape in versions.items():
            size = F.B42.write(shape, folder / f'{w.name}-g-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'G {label} ({w.name})')
            report[f'{w.name}-g-{label}'] = {'pieces': len(getattr(shape, 'geoms', [shape])), 'svg': [round(v, 2) for v in size]}
            gl, bo = dict(glyphs), dict(bodies)
            gl['g'] = bo['g'] = shape
            for key, text in texts[w.name].items():
                line = V72.set_line_kerned(text, gl, bo, w, kerns)
                size = F.B42.write(line, folder / f'{w.name}-{key}-{label}.svg', (-12, line.bounds[2] + 12, -12, 112), f'{text.upper()}, G {label} ({w.name})')
                report[f'{w.name}-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v['pieces'] for k, v in report.items() if 'pieces' in v})


if __name__ == '__main__':
    main()
