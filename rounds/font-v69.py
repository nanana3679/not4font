"""Round v66. The user: "겹치면 왼쪽이 이기고 이긴애 주변으로 잘라줘 R 다리 주변처럼 72 88" — where letters overlap,
the left one wins and the right one is cut around it (one gap, as the leg of the R is cut around its bowl); the R's
bowl at 72 in the Regular and 88 in the Bold (read so: one width per weight).
Setting: the R is spaced by its top (stem and bowl) and its leg (run up along the bowl) reaches into the next
letter's room. Where a letter's ink truly overlaps the next letter (more than touching), the next letter is cut one
gap around the overlapping pieces, and slivers left by the cut are dropped. Touching is not overlapping, so the arm
of the 4 still joins the next letter as before.
Needs shapely (PYTHONPATH). Usage: font-v69.py <out folder>"""
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


F = load('f57', 'font-v57.py')
R68 = load('f68', 'font-v68.py')
REGULAR = R68.REGULAR
BOWL = {'r16': 72, 'bold': 88}


def pieces_of(shape):
    return list(getattr(shape, 'geoms', [shape]))


def set_line_cut(text, glyphs, bodies, w, space=40):
    """as F.set_line, then: a letter overlapping the next one wins; the next is cut one gap around it"""
    placed = []                      # (drawn, spaced) per letter
    x_after_space = None
    for char in text:
        if char == ' ':
            x_after_space = (unary_union([s for _, s in placed]).bounds[2] if placed else 0) + space
            continue
        glyph, body = glyphs[char], bodies[char]
        if not placed:
            shift = 0
        elif x_after_space is not None:
            shift = x_after_space
        else:
            before = unary_union([s for _, s in placed])
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
            winners = [piece for d, _ in placed for piece in pieces_of(d) if piece.intersection(drawn).area > 0.5]
            if winners:
                drawn = drawn.difference(unary_union(winners).buffer(w.g, join_style='mitre'))
                least = 200 * (w.s / 30) ** 2
                drawn = unary_union([piece for piece in pieces_of(drawn) if piece.area >= least])
        placed.append((drawn, translate(body, shift, 0)))
    return F.B44.joined([d for d, _ in placed])


def glyphs_for(w):
    glyphs, bodies = F.glyph_set(w)
    r, upper = R68.r_long_leg(w, BOWL[w.name])
    glyphs['r'], bodies['r'] = F.B42.at_left_zero(r), F.B42.at_left_zero(upper)
    return glyphs, bodies


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    texts = {'pairs': 're ra rn rt ro rr rb', 'words': 'rank marker error', 'judgment': 'perfect great', 'four': '4k 4o 45'}
    for w in (REGULAR, F.BOLD):
        glyphs, bodies = glyphs_for(w)
        r = glyphs['r']
        size = F.B42.write(r, folder / f'{w.name}-r.svg', (-12, r.bounds[2] + 12, -12, 112), f'R ({w.name}, bowl {BOWL[w.name]})')
        report[f'{w.name}-r'] = {'svg': [round(v, 2) for v in size]}
        for key, text in texts.items():
            for label, setter in (('cut', lambda t: set_line_cut(t, glyphs, bodies, w)), ('plain', lambda t: F.set_line(t, glyphs, bodies, w.sp))):
                shape = setter(text)
                size = F.B42.write(shape, folder / f'{w.name}-{key}-{label}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name}, {label})')
                report[f'{w.name}-{key}-{label}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(report))


if __name__ == '__main__':
    main()
