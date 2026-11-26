"""Exports edition 1 (1판) of the NOT4K font: every glyph A to Z and 0 to 9 of both weights as SVG (black, letter
units: cap height 100, baseline 0, 12 units of margin), a specimen per weight, and font-ed1.json with the numbers and
rules a font build needs. The drawing is decided(w) of rounds/font-v81.py.
Usage: python3 export_ed1.py [out folder, default ed1]"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('f81', HERE / 'rounds' / 'font-v81.py')
V81 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V81)
F, V72 = V81.F, V81.V72
CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
SPECIMEN = ['abcdefghijklm', 'nopqrstuvwxyz', '0123456789', 'song select', 'perfect great good miss', 'high score 9876', 'level 12 volume 85']


def write_svg(shape, path, title):
    x0, x1, y0, y1 = -12, shape.bounds[2] + 12, -12, 112
    to_svg = lambda x, y: (x - x0, y1 - y)
    w, h = x1 - x0, y1 - y0
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}"><title>{title}</title>'
                    f'<path fill="#000000" fill-rule="evenodd" d="{F.B42.path_of(shape, to_svg)}"/></svg>\n')


def main():
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'ed1')
    record = {'name': 'NOT4K font, edition 1 (1판)', 'frozen': '2026-11-26', 'units': 'cap height 100, baseline 0, x to the right',
              'drawnBy': 'rounds/font-v81.py decided(w)', 'weights': {}}
    for w, label in ((V81.REGULAR, 'regular'), (V81.BOLD, 'bold')):
        glyphs, bodies, kerns = V81.decided(w)
        folder = out / label
        folder.mkdir(parents=True, exist_ok=True)
        table = {}
        for c in CHARS:
            g, b = glyphs[c], bodies[c]
            assert g.is_valid
            write_svg(g, folder / f'{c.upper()}.svg', f'{c.upper()} ({label})')
            table[c.upper()] = {'ink': [round(v, 3) for v in g.bounds], 'spacingBody': [round(v, 3) for v in b.bounds], 'pieces': len(getattr(g, 'geoms', [g]))}
        lines = [V72.set_line_kerned(t, glyphs, bodies, w, kerns) for t in SPECIMEN]
        from shapely.affinity import translate
        from shapely.ops import unary_union
        stacked = unary_union([translate(line, 0, -140 * n) for n, line in enumerate(lines)])
        x1 = stacked.bounds[2] + 12
        y_top, y_bottom = 112, -140 * (len(lines) - 1) - 12
        to_svg = lambda x, y: (x + 12, y_top - y)
        (out / f'specimen-{label}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x1 + 12:.2f} {y_top - y_bottom:.2f}"><title>specimen ({label})</title>'
                                                   f'<rect width="100%" height="100%" fill="#ffffff"/><path fill="#000000" fill-rule="evenodd" d="{F.B42.path_of(stacked, to_svg)}"/></svg>\n')
        record['weights'][label] = {
            'numbers': {'stem': w.s, 'stackedHorizontal': w.h, 'roundHorizontal': w.ho, 'diagonal': w.d, 'stencilGap': w.g, 'letterSpace': w.sp},
            'kerning': {'RA': round(kerns[('r', 'a')], 3)},
            'glyphs': table,
        }
    record['rules'] = {
        'angle': 'every diagonal at 52 degrees (0.78 across for 1 up); corners cut 26 tall',
        'spacing': 'neighbours stand the letter space apart at their nearest points (least distance), measured on spacing bodies; the R is measured by its top (stem and bowl) so its leg reaches into the next letter; the 4 is measured by its stem so its arm runs on by the letter space and touches the next letter',
        'overlap': 'where a letter overlaps the next one, the left one wins and the next is cut one stencil gap round it; slivers smaller than 200 x (stem / 30) squared are dropped; touching is not overlapping',
        'kerning': 'only RA is set apart, by 25 percent of the distance at which the A would clear the R leg',
        'space': 40,
        'case': 'capitals only; lowercase uses the same shapes',
        'regularWidths': 'B C D E F G H J L O Q S T U and 0 2 3 5 6 8 9 at 90 percent of the Bold widths',
    }
    (out / 'font-ed1.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')
    print('exported', len(CHARS) * 2, 'glyphs to', out)


if __name__ == '__main__':
    main()
