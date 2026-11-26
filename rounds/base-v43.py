"""Round v43: the Bold base forms again, the 4 changed as the user asked: "4의 오른쪽은 남기는데 충돌판정을 위한
측정은 기둥 기준으로해서 지금처럼 오른쪽글자와붙게" (keep the right of the 4, but measure from the stem when
spacing, so that it joins the letter on its right as it does now).
  4  the crossbar runs on 16 past the stem (the right of the 4 stays). Its spacing body is the 4 without that arm:
     the next letter is set 6 from the stem, and the arm reaches 10 into it; where that letter has ink there, the arm
     joins it (both are ink), as the crossbar of the 4 joins the stem of the K in edition 1
The other letters as in round v42 (the N stencil, kept since nothing was said against it). Writes the glyphs, the 4
with a guide where spacing is measured, NOT4K, and the 4 before K, O and T and at the end of a word.
Needs shapely (PYTHONPATH). Usage: base-v43.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import translate
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B42 = load('b42', 'base-v42.py')
GAP = B42.GAP
ARM = 16


def glyph_set():
    glyphs = {'n': B42.n_glyph(), 'o': B42.o_glyph(), 't': B42.t_glyph(), '4': B42.four_glyph(ARM), 'k': B42.k_glyph()}
    glyphs = {name: B42.at_left_zero(shape) for name, shape in glyphs.items()}
    bodies = dict(glyphs)
    bodies['4'] = B42.at_left_zero(B42.four_glyph(0))       # the 4 without its arm: spacing is measured from the stem
    return glyphs, bodies


def set_word(names, glyphs, bodies, gap=GAP):
    """each glyph moved left until its spacing body is `gap` from the spacing bodies set before it"""
    drawn, spaced = [], []
    for name in names:
        glyph, body = glyphs[name], bodies[name]
        if not spaced:
            drawn.append(glyph)
            spaced.append(body)
            continue
        before = unary_union(spaced)
        low, high = before.bounds[0] - body.bounds[2], before.bounds[2] + gap + 1
        for _ in range(60):
            middle = (low + high) / 2
            if before.distance(translate(body, middle, 0)) >= gap - 1e-9:
                high = middle
            else:
                low = middle
        drawn.append(translate(glyph, high, 0))
        spaced.append(translate(body, high, 0))
    return drawn, spaced


GUIDE = '#ffd166'


def write_with_guide(shape, path, frame, title, guide_x=None):
    x0, x1, y0, y1 = frame
    to_svg = lambda x, y: (x - x0, y1 - y)
    w, h = x1 - x0, y1 - y0
    extra = ''
    if guide_x is not None:
        gx = guide_x - x0
        extra = f'<line x1="{gx:.2f}" y1="{y1 - 112:.2f}" x2="{gx:.2f}" y2="{y1 + 12:.2f}" stroke="{GUIDE}" stroke-width="1.5" stroke-dasharray="4 3"/>'
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}"><title>{title}</title>'
                    f'<path fill="{B42.INK}" fill-rule="evenodd" d="{B42.path_of(shape, to_svg)}"/>{extra}</svg>')
    return w, h


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = glyph_set()
    report = {}
    four_width, body_width = glyphs['4'].bounds[2], bodies['4'].bounds[2]
    write_with_guide(glyphs['4'], folder / 'base-4.svg', (-12, four_width + 12, -12, 112), 'base form 4, the arm out 16', guide_x=body_width)
    report['4'] = {'width': round(four_width, 2), 'spacingWidth': round(body_width, 2)}
    word, spaced = set_word(['n', 'o', 't', '4', 'k'], glyphs, bodies)
    line = unary_union(word)
    frame = (-34.64 - 12, line.bounds[2] + 12, 154.46 + 12 - 232.92, 154.46 + 12)
    size = write_with_guide(line, folder / 'base-word-notak.svg', frame, 'NOT4K from the base forms, gap 6, the 4 spaced from its stem')
    report['word'] = {'starts': [round(piece.bounds[0], 2) for piece in spaced], 'svg': [round(v, 2) for v in size],
                      'pieces': len(getattr(line, 'geoms', [line]))}
    for pair in ('4k', '4o', '4t', '4'):
        drawn, spaced = set_word(list(pair), glyphs, bodies)
        shape = unary_union(drawn)
        stem_right = spaced[0].bounds[2]
        size = write_with_guide(shape, folder / f'base-pair-{pair}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{pair} from the base forms', guide_x=stem_right)
        touching = len(drawn) > 1 and drawn[0].intersects(drawn[1])
        report[f'pair-{pair}'] = {'svg': [round(v, 2) for v in size], 'armJoins': touching}
    (folder / 'base-report-v43.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
