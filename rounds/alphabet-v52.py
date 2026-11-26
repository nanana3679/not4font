"""Round v52 (same screen as round v51). The user, while the Q was being drawn: "Z는 n처럼 분할하는안도 보으줘"
(also a Z split like the N). The Z with square bar ends (round v50) whose diagonal, corner to corner, stands 6 apart
from the bars, as the diagonal of the N stands apart from its stems.
Needs shapely (PYTHONPATH). Usage: alphabet-v52.py <out folder>"""
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


A51 = load('a51', 'alphabet-v51.py')
A50 = A51.A50
A48 = A50.A48
B42, B43, B44, C, P, rect = A48.B42, A48.B43, A48.B44, A48.C, A48.P, A48.rect


def z_stencil():
    width = 100 * C.RUN + A48.ACROSS
    diagonal = A48.band((0, A48.ACROSS, 0), (width - A48.ACROSS, width, 100))
    room = diagonal.buffer(A48.GAP, join_style='mitre')
    bars = [P(rect(0, 76, width, 100)).difference(room), P(rect(0, 0, width, 24)).difference(room)]
    return unary_union(bars + [diagonal])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    report = {}
    shape = B42.at_left_zero(z_stencil())
    assert shape.is_valid
    width = shape.bounds[2]
    size = B42.write(shape, folder / 'glyph-z-split.svg', (-12, width + 12, -12, 112), 'Z split like the N')
    report['z-split'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
    A48.DRAW['b'] = A50.g_b
    A48.DRAW['q'] = lambda: A51.g_q(52)
    A48.DRAW['z'] = z_stencil
    glyphs, bodies = A48.full_set()
    for key in ('zebra', 'maze'):
        drawn, _ = B43.set_word(list(key), glyphs, bodies)
        line = B44.joined(drawn)
        size = B42.write(line, folder / f'word-{key}-z-split.svg', (-12, line.bounds[2] + 12, -12, 112), f'{key.upper()} with the Z split')
        report[f'word-{key}-z-split'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
