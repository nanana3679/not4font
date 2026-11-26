"""Round v31, the first round of the punch list: concept A (merge, narrow channel, red 30) with the top right corner
of the right stem of the N cut parallel to the top left corner of the O (the wedge of dark between N and O becomes a
channel of 6), and an optional K whose leg ends in a sweep along the baseline (the user read the long leg of the K
as the long final stroke of a brush).
Needs shapely (PYTHONPATH). Usage: concepts-v31.py <out folder>"""
import importlib.util
import json
import math
import sys
from pathlib import Path


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load('c25', 'concepts-v25.py')
K = load('c26', 'concepts-v26.py')


def k_sweep(x, weight, gap):
    """the capital K of round v26, its leg ending in a sweep: from 20 above the baseline on the outer edge of the leg, a
    straight edge at 30 degrees runs down to a point on the baseline"""
    pieces = K.k_capital(x, weight, gap)
    leg_axis = (x + weight + 24, 40)
    outer = C.add(leg_axis, (C.SIN, C.COS), weight / 2)       # a point on the outer (upper right) edge of the leg
    start = C.at_height(outer, C.DOWN, 20)
    at_base = C.at_height(outer, C.DOWN, 0)
    tip = (start[0] + 20 / math.tan(math.radians(30)), 0)
    tail = C.P([start, tip, (at_base[0] - 20, 0), (start[0] - 10, 20)])   # the last two points lie inside the leg
    return pieces + [tail]


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    C.SLASH_ROOM = 0
    C.CHANNEL = C.SLASH_WEIGHT
    for label, builder in (('plain', K.k_capital), ('sweep', k_sweep)):
        concept = C.concept_a(k_builder=builder, o_width=104, bar4=(13, 37), arm_mode='merge', seam=4, red_width=30, nest_n=True)
        concept['name'] = f'A7-{label}'
        out, size, frame = C.write(concept, folder)
        C.write(concept, folder, colour=False)
        (folder / f'concept-a7-{label}.json').write_text(json.dumps({'name': concept['name'], 'svg': out.name, 'size': size, 'slash': concept['slash'], 'frame': frame, 'channel': C.CHANNEL}, indent=1) + '\n')
        print(out.name, [round(v) for v in size])


if __name__ == '__main__':
    main()
