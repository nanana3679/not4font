"""Round v42: the base forms (기본형) of N, O, T, 4, K in the Bold weight, as they stand alone: the shapes of
edition 1 with nothing their neighbours did to them (no joins, no sweeps, no red, no lit slash). The user: the
present weight is the Bold, for menu names and judgment words; a Regular may follow for the rest of the UI, where
no word script and no sweeps are needed.
  N  stems 30, the diagonal 30 across on the axis of the red diagonal (21, 100) to (99, 0), held to the cap height;
     stencil: the diagonal stands apart from the stems by 6, as the leg of the K does (other version: joined)
  O  the O of edition 1, uncut: 104 wide, sides 30, top and bottom 26, corners cut 26 tall at the angle of the red
  T  crossbar 26 thick and 97 wide on top, both ends cut at the angle of the red (the top wider), stem 30 in the middle
  4  the 4 of edition 1, its crossbar ending flush with the stem (other version: running on 16 past it)
  K  the capital K of edition 1 without the sweep at the end of its leg
Also NOT4K set from these forms with nothing but the gap of 6 at the closest point between letters (what general UI
text would look like), in the frame of edition 1 so that the two compare at one scale.
Needs shapely (PYTHONPATH). Usage: base-v42.py <out folder>"""
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


C = load('c25', 'concepts-v25.py')
K26 = load('c26', 'concepts-v26.py')
S, B, GAP, CUT = 30, 26, 6, 26
INK = '#e6ecf5'


def n_glyph(stencil=True):
    diagonal = C.P(C.box(C.blade((21, 100), (99, 0), 30, before=60, after=60), y0=0, y1=100))
    stems = [C.P(C.rect(0, 0, S, 100)), C.P(C.rect(120 - S, 0, 120, 100))]
    if stencil:
        room = diagonal.buffer(GAP, join_style='mitre')
        return unary_union([stem.difference(room) for stem in stems] + [diagonal])
    return unary_union(stems + [diagonal])


def o_glyph():
    run = CUT * C.RUN
    outer = [(run, 0), (104 - run, 0), (104, CUT), (104, 100 - CUT), (104 - run, 100), (run, 100), (0, 100 - CUT), (0, CUT)]
    corner = S * 0.93
    inner = C.offset(outer, [-B, -corner, -S, -corner, -B, -corner, -S, -corner])
    return C.P(outer).difference(C.P(inner))


def t_glyph(width=97):
    run = B * C.RUN
    bar = C.P([(0, 100), (width, 100), (width - run, 100 - B), (run, 100 - B)])
    left = (width - S) / 2
    return unary_union([bar, C.P(C.rect(left, 0, left + S, 100 - B + 1))])


def four_glyph(arm=0):
    pieces, _ = C.four(0, (13, 37), 26, S, arm)
    return unary_union(pieces)


def k_glyph():
    return unary_union(K26.k_capital(0, S, GAP))


def at_left_zero(shape):
    return translate(shape, -shape.bounds[0], 0)


def set_word(glyphs, gap=GAP):
    """each glyph moved left until its closest point is `gap` from everything set before it"""
    placed = []
    for glyph in glyphs:
        if not placed:
            placed.append(glyph)
            continue
        before = unary_union(placed)
        low, high = before.bounds[0] - glyph.bounds[2], before.bounds[2] + gap + 1
        for _ in range(60):
            middle = (low + high) / 2
            if before.distance(translate(glyph, middle, 0)) >= gap - 1e-9:
                high = middle
            else:
                low = middle
        placed.append(translate(glyph, high, 0))
    return placed


def path_of(shape, to_svg):
    polys = list(getattr(shape, 'geoms', [shape]))
    parts = []
    for poly in polys:
        for ring in [poly.exterior] + list(poly.interiors):
            points = [to_svg(x, y) for x, y in list(ring.coords)[:-1]]
            parts.append('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in points) + ' Z')
    return ' '.join(parts)


def write(shape, path, frame, title):
    """frame = (x0, x1, y0, y1) in letter units"""
    x0, x1, y0, y1 = frame
    to_svg = lambda x, y: (x - x0, y1 - y)
    w, h = x1 - x0, y1 - y0
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}"><title>{title}</title>'
                    f'<path fill="{INK}" fill-rule="evenodd" d="{path_of(shape, to_svg)}"/></svg>')
    return w, h


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs = {
        'n': n_glyph(), 'n-joined': n_glyph(stencil=False), 'o': o_glyph(), 't': t_glyph(),
        '4': four_glyph(), '4-out': four_glyph(16), 'k': k_glyph(),
    }
    report = {}
    for name, shape in glyphs.items():
        shape = at_left_zero(shape)
        glyphs[name] = shape
        width = shape.bounds[2]
        size = write(shape, folder / f'base-{name}.svg', (-12, width + 12, -12, 112), f'base form {name}')
        report[name] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    word = set_word([glyphs[name] for name in ('n', 'o', 't', '4', 'k')])
    starts = [round(piece.bounds[0], 2) for piece in word]
    line = unary_union(word)
    # the frame of edition 1: x0 -34.64, top 154.46, pad 12, height 232.92
    frame = (-34.64 - 12, line.bounds[2] + 12, 154.46 + 12 - 232.92, 154.46 + 12)
    size = write(line, folder / 'base-word-notak.svg', frame, 'NOT4K set from the base forms, gap 6 only')
    gaps = [round(unary_union(word[:i]).distance(word[i]), 3) for i in range(1, len(word))]
    report['word'] = {'starts': starts, 'gaps': gaps, 'svg': [round(v, 2) for v in size]}
    (folder / 'base-report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
