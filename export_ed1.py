"""Exports edition 1 (1판) of the NOT4K font: every glyph A to Z and 0 to 9 of both weights as SVG (black, letter
units: cap height 100, baseline 0, 12 units of margin), a specimen per weight, and font-ed1.json with the numbers and
rules a font build needs. The outlines and spacing rules come from not4k_font.
Usage: python3 export_ed1.py [out folder, default ed1]"""
import json
import sys
from pathlib import Path

from shapely.affinity import translate
from shapely.ops import unary_union

from not4k_font.geometry import pieces_of
from not4k_font.glyphs import BOLD, CHARACTERS, REGULAR, build_glyphs
from not4k_font.spacing import SPACE_WIDTH, compose_line, edition_kerning


HERE = Path(__file__).parent
SPECIMEN = ['abcdefghijklm', 'nopqrstuvwxyz', '0123456789', 'song select', 'perfect great good miss', 'high score 9876', 'level 12 volume 85']


def svg_path(shape, to_svg):
    parts = []
    for polygon in pieces_of(shape):
        for ring in (polygon.exterior, *polygon.interiors):
            points = [to_svg(x, y) for x, y in ring.coords[:-1]]
            parts.append('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in points) + ' Z')
    return ' '.join(parts)


def write_svg(shape, path, title):
    x0, x1, y0, y1 = -12, shape.bounds[2] + 12, -12, 112
    to_svg = lambda x, y: (x - x0, y1 - y)
    w, h = x1 - x0, y1 - y0
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}"><title>{title}</title>'
                    f'<path fill="#000000" fill-rule="evenodd" d="{svg_path(shape, to_svg)}"/></svg>\n')


def export_edition(out):
    # Keep the recorded drawing source from the day edition 1 was frozen.
    record = {'name': 'NOT4K font, edition 1 (1판)', 'frozen': '2026-11-26', 'units': 'cap height 100, baseline 0, x to the right',
              'drawnBy': 'rounds/font-v81.py decided(w)', 'weights': {}}
    for weight, label in ((REGULAR, 'regular'), (BOLD, 'bold')):
        glyphs, bodies = build_glyphs(weight)
        kerns = edition_kerning(glyphs, bodies, weight.letter_space)
        folder = out / label
        folder.mkdir(parents=True, exist_ok=True)
        table = {}
        for c in CHARACTERS:
            g, b = glyphs[c], bodies[c]
            assert g.is_valid
            write_svg(g, folder / f'{c.upper()}.svg', f'{c.upper()} ({label})')
            table[c.upper()] = {'ink': [round(v, 3) for v in g.bounds], 'spacingBody': [round(v, 3) for v in b.bounds], 'pieces': len(pieces_of(g))}
        lines = [compose_line(text, glyphs, bodies, weight, kerns) for text in SPECIMEN]
        stacked = unary_union([translate(line, 0, -140 * n) for n, line in enumerate(lines)])
        x1 = stacked.bounds[2] + 12
        y_top, y_bottom = 112, -140 * (len(lines) - 1) - 12
        to_svg = lambda x, y: (x + 12, y_top - y)
        (out / f'specimen-{label}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x1 + 12:.2f} {y_top - y_bottom:.2f}"><title>specimen ({label})</title>'
                                                   f'<rect width="100%" height="100%" fill="#ffffff"/><path fill="#000000" fill-rule="evenodd" d="{svg_path(stacked, to_svg)}"/></svg>\n')
        record['weights'][label] = {
            'numbers': {
                'stem': weight.stem,
                'stackedHorizontal': weight.stacked_horizontal,
                'roundHorizontal': weight.round_horizontal,
                'diagonal': weight.diagonal,
                'stencilGap': weight.stencil_gap,
                'letterSpace': weight.letter_space,
            },
            'kerning': {'RA': round(kerns[('r', 'a')], 3)},
            'glyphs': table,
        }
    record['rules'] = {
        'angle': 'every diagonal at 52 degrees (0.78 across for 1 up); corners cut 26 tall',
        'spacing': 'neighbours stand the letter space apart at their nearest points (least distance), measured on spacing bodies; the R is measured by its top (stem and bowl) so its leg reaches into the next letter; the 4 is measured by its stem so its arm runs on by the letter space and touches the next letter',
        'overlap': 'where a letter overlaps the next one, the left one wins and the next is cut one stencil gap round it; slivers smaller than 200 x (stem / 30) squared are dropped; touching is not overlapping',
        'kerning': 'only RA is set apart, by 25 percent of the distance at which the A would clear the R leg',
        'space': SPACE_WIDTH,
        'case': 'capitals only; lowercase uses the same shapes',
        'regularWidths': 'B C D E F G H J L O Q S T U and 0 2 3 5 6 8 9 at 90 percent of the Bold widths',
    }
    (out / 'font-ed1.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')


def main():
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'ed1')
    export_edition(out)
    print('exported', len(CHARACTERS) * 2, 'glyphs to', out)


if __name__ == '__main__':
    main()
