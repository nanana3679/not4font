"""Round v51. The user: "Q 선 약간만 짧게" (the tail of the Q a little shorter). The tail keeps its foot on the
baseline (like the leg of the R) and its slope; its flat top comes down from 52 to 46, 40 or 34 (steps).
Needs shapely (PYTHONPATH). Usage: alphabet-v51.py <out folder>"""
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


A50 = load('a50', 'alphabet-v50.py')
A48 = A50.A48
B42, B43, B44, C = A48.B42, A48.B43, A48.B44, A48.C
TOPS = [52, 46, 40, 34]


def g_q(top, width=104):
    body = A48.ring(width, 0, 100, 26, 26)
    across = 24 / C.SIN
    foot = (width - 20.6, width - 20.6 + across, 0)
    head = (foot[0] - top * C.RUN, foot[1] - top * C.RUN, top)
    tail = A48.band(foot, head)
    return unary_union([body.difference(tail.buffer(A48.GAP, join_style='mitre')), tail])


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    A48.DRAW['b'] = A50.g_b
    A48.DRAW['z'] = A50.z_square
    report = {}
    for top in TOPS:
        shape = B42.at_left_zero(g_q(top))
        assert shape.is_valid, top
        width = shape.bounds[2]
        size = B42.write(shape, folder / f'glyph-q{top}.svg', (-12, width + 12, -12, 112), f'Q, tail top {top}')
        report[f'q{top}'] = {'width': round(width, 2), 'svg': [round(v, 2) for v in size]}
        A48.DRAW['q'] = lambda top=top: g_q(top)
        glyphs, bodies = A48.full_set()
        drawn, _ = B43.set_word(list('quest'), glyphs, bodies)
        line = B44.joined(drawn)
        size = B42.write(line, folder / f'word-quest-q{top}.svg', (-12, line.bounds[2] + 12, -12, 112), f'QUEST, tail top {top}')
        report[f'word-quest-q{top}'] = {'svg': [round(v, 2) for v in size]}
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v.get('width', v['svg'][0]) for k, v in report.items()}))


if __name__ == '__main__':
    main()
