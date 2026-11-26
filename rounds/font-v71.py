"""Round v68. The user: "볼드아닌일반 O E같은거만 커보여서 너비를 P 줄인것처럼 맞춰야겠다" — in the Regular the
letters like O and E look large; narrow them as the P was narrowed (96 to 72, a quarter off); and "ra조합만 따로
띄우겠다는 뜻이면 한번해봐" — try setting the RA pair apart on its own (kerning).
  widths   in the Regular the letters whose width was taken over from the Bold (not those whose width follows from
           the 52 degree angle: A, V, N, M, W, X, Y, Z, K, 4, 7, 1) are three quarters as wide; the P and the R's
           bowl stay at 72
  kerning  a pair listed as kerned is spaced by the whole left letter instead of its spacing body, so the R's leg
           does not reach the A; the left-wins cut stays for every other pair
Needs shapely (PYTHONPATH). Usage: font-v71.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import rotate, translate
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V70 = load('f70', 'font-v70.py')
V69 = V70.V69
F = V69.F
REGULAR = V69.REGULAR
NARROW = 0.75
WIDTHS = {'o': 104, 'c': 96, 'g': 104, 'd': 100, 'q': 104, 'u': 100, 's': 96, 'b': 96, '8': 96, '0': 92, 'e': 84, 'f': 82,
          'l': 80, 'h': 100, 't': 97, 'j': 88, '2': 96, '3': 96, '5': 96, '6': 96}
KERNED = {('r', 'a')}


def regular_set(w, narrow=True):
    glyphs, bodies = V69.glyphs_for(w)
    glyphs['p'] = bodies['p'] = F.B42.at_left_zero(V70.p_like_r(w))
    if narrow:
        for name, width in WIDTHS.items():
            glyphs[name] = bodies[name] = F.B42.at_left_zero(F.DRAW[name](w, width=round(width * NARROW)))
        six = F.g_6(w, width=round(96 * NARROW))
        glyphs['9'] = bodies['9'] = F.B42.at_left_zero(rotate(six, 180, origin=(round(96 * NARROW) / 2, 50)))
    return glyphs, bodies


def set_line_kern(text, glyphs, bodies, w, kerned=KERNED, space=40):
    """the left-wins setting of round v66, where a kerned pair is spaced by the whole left letter"""
    placed, prev, x_after_space = [], None, None
    for char in text:
        if char == ' ':
            x_after_space = (unary_union([s for _, s in placed]).bounds[2] if placed else 0) + space
            prev = None
            continue
        glyph, body = glyphs[char], bodies[char]
        if not placed:
            shift = 0
        elif x_after_space is not None:
            shift = x_after_space
        else:
            spaced = [s for _, s in placed[:-1]] + [placed[-1][0] if (prev, char) in kerned else placed[-1][1]]
            before = unary_union(spaced)
            low, high = before.bounds[0] - body.bounds[2], before.bounds[2] + w.sp + 1
            for _ in range(60):
                middle = (low + high) / 2
                if before.distance(translate(body, middle, 0)) >= w.sp - 1e-9:
                    high = middle
                else:
                    low = middle
            shift = high
        x_after_space = None
        drawn = translate(glyph, shift, 0)
        if placed:
            winners = [piece for d, _ in placed for piece in V69.pieces_of(d) if piece.intersection(drawn).area > 0.5]
            if winners:
                drawn = drawn.difference(unary_union(winners).buffer(w.g, join_style='mitre'))
                least = 200 * (w.s / 30) ** 2
                drawn = unary_union([piece for piece in V69.pieces_of(drawn) if piece.area >= least])
        placed.append((drawn, translate(body, shift, 0)))
        prev = char
    return F.B44.joined([d for d, _ in placed])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    texts = {'alphabet-1': 'abcdefghijklm', 'alphabet-2': 'nopqrstuvwxyz', 'digits': '0123456789', 'ui-1': 'high score 9876', 'ui-2': 'song select', 'judgment': 'perfect great good miss'}
    for label, narrow in (('before', False), ('after', True)):
        glyphs, bodies = regular_set(REGULAR, narrow)
        for name, shape in glyphs.items():
            assert shape.is_valid, (label, name)
        for key, text in texts.items():
            shape = set_line_kern(text, glyphs, bodies, REGULAR)
            size = F.B42.write(shape, folder / f'r16-{key}-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} (Regular 16, {label})')
            report[f'r16-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    for w in (REGULAR, F.BOLD):
        glyphs, bodies = regular_set(w, narrow=(w is REGULAR))
        for label, kerned in (('cut', set()), ('kerned', KERNED)):
            for key, text in (('ra', 'ra rank track brave'),):
                shape = set_line_kern(text, glyphs, bodies, w, kerned)
                size = F.B42.write(shape, folder / f'{w.name}-{key}-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name}, {label})')
                report[f'{w.name}-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print({k: v['svg'][0] for k, v in report.items()})


if __name__ == '__main__':
    main()
