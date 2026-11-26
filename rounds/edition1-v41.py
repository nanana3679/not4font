"""Round v41: freezes the first edition (1판) of the NOT4K wordmark, the user having agreed ("ㅇㅇ") after the third
punch list (round v40, choice A). Writes into <gallery>/logo/edition1/:
  not4k-wordmark-ed1.svg / -light.svg   the word, black and light
  not4k-mark-ed1-light.svg              the N alone, turned until the red diagonal stands upright
  not4k-wordmark-ed1-joins-light.svg    the light word with the places where letters were shaped by their
                                        neighbours marked 1 to 5 (they stay in the logo and do not carry over
                                        to other letters)
  not4k-wordmark-ed1.json               how to draw it again, the frame and the lit slash
The shape is concept A with the options below; the channel of the lit slash is 10 (for the animated title).
Needs shapely (PYTHONPATH). Usage: edition1-v41.py <gallery folder> <scratch folder>"""
import importlib.util
import json
import sys
from pathlib import Path
from shapely.affinity import rotate


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V36 = load('c36', 'concepts-v36.py')
C = V36.C
OPTIONS = dict(nest_n=True, nest_ox=V36.N_WIDTH + V36.GAP + V36.V33_MIRROR_SHIFT, n_foot=True, n_top_sweep=True, o_shift=0, o_cut_for_sweep=True, o_cut_square=True)
LIGHT = lambda text: text.replace('fill="#111111"', 'fill="#e6ecf5"')
# where the letters were shaped by their neighbours, in letter units (cap height 100, baseline 0)
JOINS = [
    (1, (143.0, 89.8), 'the sweep at the top right of the N runs over the O, and the top left of the O is cut under it'),
    (2, (222.2, 88.8), 'the left end of the crossbar of the T is cut parallel to the top right corner of the O'),
    (3, None, 'the channel between the T and the 4, where the lit slash stands'),
    (4, (359.7, 25.0), 'the crossbar of the 4 runs on into the stem of the K'),
    (5, (118.0, 22.0), 'the foot of the right stem of the N is cut along a line once laid against the corner of the O'),
]


def main():
    gallery, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir = gallery / 'logo' / 'edition1'
    out_dir.mkdir(parents=True, exist_ok=True)
    C.SLASH_ROOM = 0
    C.CHANNEL = C.SLASH_WEIGHT
    concept = C.concept_a(**V36.BASE, **OPTIONS)
    concept['name'] = 'NOT4K wordmark, edition 1'
    out, size, frame = C.write(concept, scratch)
    svg = out.read_text()
    (out_dir / 'not4k-wordmark-ed1.svg').write_text(svg)
    (out_dir / 'not4k-wordmark-ed1-light.svg').write_text(LIGHT(svg))
    n, _ = V36.n_and_o(concept, V36.N_WIDTH + V36.GAP)
    mark = {'name': 'NOT4K mark, edition 1', 'ink': rotate(n, V36.UPRIGHT, origin=(60, 50)), 'red': rotate(concept['red'], V36.UPRIGHT, origin=(60, 50)), 'slash': concept['slash']}
    mark_out, _, _ = C.write(mark, scratch)
    (out_dir / 'not4k-mark-ed1-light.svg').write_text(LIGHT(mark_out.read_text()))
    (x0, y1, pad) = frame
    to = lambda x, y: (x - x0 + pad, y1 - y + pad)
    (fx, fy), (hx, hy) = concept['slash']
    marks = []
    for number, at, _ in JOINS:
        if at is None:
            at = ((fx + hx) / 2, 50.0)
        sx, sy = to(*at)
        marks.append(f'<g><circle cx="{sx:.1f}" cy="{sy:.1f}" r="15" fill="#070b14" fill-opacity="0.8" stroke="#ffd166" stroke-width="2.5"/>'
                     f'<text x="{sx:.1f}" y="{sy + 6.2:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#ffd166">{number}</text></g>')
    light = LIGHT(svg)
    (out_dir / 'not4k-wordmark-ed1-joins-light.svg').write_text(light.replace('</svg>', ''.join(marks) + '</svg>'))
    record = {
        'name': 'NOT4K wordmark, edition 1 (1판)', 'frozen': '2026-11-26', 'size': size, 'frame': frame, 'slash': concept['slash'], 'slashChannel': C.CHANNEL,
        'drawWith': {'tool': 'concepts-v25.py concept_a', 'base': {'k_builder': 'concepts-v31.py k_sweep', 'o_width': 104, 'bar4': [13, 37], 'arm_mode': 'merge', 'seam': 4, 'red_width': 30}, 'options': OPTIONS, 'SLASH_ROOM': 0},
        'joins': [{'number': number, 'at': at, 'what': what} for number, at, what in JOINS],
    }
    (out_dir / 'not4k-wordmark-ed1.json').write_text(json.dumps(record, indent=1) + '\n')
    print('edition 1 written', [round(v, 2) for v in size], 'slash', [[round(v, 2) for v in p] for p in concept['slash']])


if __name__ == '__main__':
    main()
