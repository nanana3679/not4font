"""Round v68 (continued). The RA pair set apart by kerning, in steps: from the setting of round v66 (spaced by the
R's top, the A cut round the leg) to the setting where the A no longer touches the leg (spaced by the whole R).
Also lists which pairs R+letter overlap at all in the top-spaced setting (where the left-wins cut acts).
Needs shapely (PYTHONPATH). Usage: font-v72.py <out folder>"""
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


V71 = load('f71', 'font-v71.py')
V69 = V71.V69
F = V71.F
STEPS = (0, 0.25, 0.5, 0.75, 1)


def least_shift(before, body, sp):
    low, high = before.bounds[0] - body.bounds[2], before.bounds[2] + sp + 1
    for _ in range(60):
        middle = (low + high) / 2
        if before.distance(translate(body, middle, 0)) >= sp - 1e-9:
            high = middle
        else:
            low = middle
    return high


def set_line_kerned(text, glyphs, bodies, w, kerns, space=40):
    """the left-wins setting of round v66; a listed pair moves the right letter on by its kerning value"""
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
            shift = least_shift(unary_union([s for _, s in placed]), body, w.sp) + kerns.get((prev, char), 0)
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


def full_kern(w, glyphs, bodies, left, right):
    """how far the right letter must move on from the top-spaced place so that it stands the letter space from
    the whole left letter"""
    return least_shift(glyphs[left], bodies[right], w.sp) - least_shift(bodies[left], bodies[right], w.sp)


def overlaps(w, glyphs, bodies):
    found = {}
    for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
        shift = least_shift(bodies['r'], bodies[char], w.sp)
        area = glyphs['r'].intersection(translate(glyphs[char], shift, 0)).area
        if area > 0.5:
            found[char] = round(area, 1)
    return found


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    for w in (V71.REGULAR, F.BOLD):
        glyphs, bodies = V71.regular_set(w, narrow=(w is V71.REGULAR))
        full = full_kern(w, glyphs, bodies, 'r', 'a')
        report[f'{w.name}-full'] = round(full, 2)
        report[f'{w.name}-overlaps'] = overlaps(w, glyphs, bodies)
        for step in STEPS:
            kern = full * step
            tag = f'{round(step * 100):03d}'
            for key, text in (('pair', 'ra'), ('words', 'rank track brave')):
                shape = set_line_kerned(text, glyphs, bodies, w, {('r', 'a'): kern})
                size = F.B42.write(shape, folder / f'{w.name}-{key}-{tag}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{text.upper()} ({w.name}, RA kerned {kern:.1f})')
                report[f'{w.name}-{key}-{tag}'] = {'kern': round(kern, 1), 'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, dict) or 'svg' not in v}))


if __name__ == '__main__':
    main()
