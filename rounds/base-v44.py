"""Round v44: the arm of the 4 runs on past its stem by exactly the letter spacing (6), as the user asked ("오른쪽
획 튀어나오는 길이를 자간만큼으로 하자"), and it joins letters without a stem there too ("응"). Spacing is still
measured from the stem, so the arm ends where the next letter begins: it meets a stem standing there (K) and joins
it, meets the side of an O over the part where the side is upright, and otherwise stands out by 6.
Unions are closed by 0.01 so that edges that meet exactly become one shape (no hairline seam).
Needs shapely (PYTHONPATH). Usage: base-v44.py <out folder>"""
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


B43 = load('b43', 'base-v43.py')
B42 = B43.B42
B43.ARM = B42.GAP


def joined(shapes):
    return unary_union(shapes).buffer(0.01, join_style='mitre').buffer(-0.01, join_style='mitre')


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    glyphs, bodies = B43.glyph_set()
    report = {}
    four_width, body_width = glyphs['4'].bounds[2], bodies['4'].bounds[2]
    B43.write_with_guide(glyphs['4'], folder / 'base-4.svg', (-12, four_width + 12, -12, 112), 'base form 4, the arm out 6', guide_x=body_width)
    report['4'] = {'width': round(four_width, 2), 'spacingWidth': round(body_width, 2)}
    word, spaced = B43.set_word(['n', 'o', 't', '4', 'k'], glyphs, bodies)
    line = joined(word)
    frame = (-34.64 - 12, line.bounds[2] + 12, 154.46 + 12 - 232.92, 154.46 + 12)
    size = B43.write_with_guide(line, folder / 'base-word-notak.svg', frame, 'NOT4K from the base forms, the arm of the 4 out 6')
    report['word'] = {'starts': [round(piece.bounds[0], 2) for piece in spaced], 'svg': [round(v, 2) for v in size], 'pieces': len(getattr(line, 'geoms', [line]))}
    for pair in ('4k', '4o', '4t', '4'):
        drawn, spaced = B43.set_word(list(pair), glyphs, bodies)
        shape = joined(drawn)
        size = B43.write_with_guide(shape, folder / f'base-pair-{pair}.svg', (-12, shape.bounds[2] + 12, -12, 112), f'{pair} from the base forms', guide_x=spaced[0].bounds[2])
        meets = len(drawn) > 1 and drawn[0].distance(drawn[1]) < 1e-6
        report[f'pair-{pair}'] = {'svg': [round(v, 2) for v in size], 'armMeets': meets, 'pieces': len(getattr(shape, 'geoms', [shape]))}
    (folder / 'base-report-v44.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
