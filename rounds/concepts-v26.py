"""Round v26: concept A of round v25 (the billet) with a capital K. The user did not like the K of concept A (the K
of the shared logo, whose stem is cut along \\ at the top, read as a small k) and asked for a capital K that keeps
its leg apart. The stem now runs full height with a flat top; the arm leaves the stem low and reaches the cap line
with a flat end, leaving a small V between the top of the stem and the arm; the leg still leaves from under the arm
behind a narrow gap and touches nothing.
Needs shapely (PYTHONPATH). Usage: concepts-v26.py <out folder>"""
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('c25', Path(__file__).parent / 'concepts-v25.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def k_capital(x, weight, gap):
    stem = C.rect(x, 0, x + weight, 100)
    vertex = (x + weight, 38)                       # where the lower edge of the arm leaves the stem
    arm_axis = C.add(vertex, C.UPPER_LEFT, weight / 2)
    arm = C.box(C.blade(arm_axis, C.add(arm_axis, C.UP, 120), weight, before=40), x0=x, y1=100)
    gap_at = C.add(vertex, C.LOWER_RIGHT, gap)
    leg_axis = (x + weight + 24, 40)
    leg = C.box(C.blade(C.add(leg_axis, C.DOWN, -60), C.add(leg_axis, C.DOWN, 120), weight), y0=0)
    leg = C.keep(leg, gap_at, C.add(gap_at, C.UP, 50), (x + weight + 60, 5))
    return [C.P(stem), C.P(arm), C.P(leg)]


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    concept = C.concept_a(k_builder=k_capital)
    concept['name'] = 'A2'
    out, size, frame = C.write(concept, folder)
    C.write(concept, folder, colour=False)
    C.write(concept, folder, slash=True)
    (folder / 'concept-a2.json').write_text(json.dumps({'name': 'A2', 'svg': out.name, 'size': size, 'slash': concept['slash'], 'frame': frame}, indent=1) + '\n')
    print(out.name, [round(v) for v in size])


if __name__ == '__main__':
    main()
