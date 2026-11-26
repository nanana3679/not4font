"""Round v36. The user: "not a right triangle, a right isosceles triangle" (the triangle version) and "the mirror
version: just the previous version (round v33) with only the gap between N and O made smaller, nothing else".
  iso          the triangle keeps its right angle at the top of the inner edge of the stem and its lower point on the
               dark line around the red diagonal; its outer edge runs at 45 degrees, so that its two legs are equal.
               The top left corner of the O runs at 45 degrees too (as tall as the other corners, 26), so that the
               channel between them keeps one width; the O stands where that channel is 6
  mirror-near  the N of round v33 as it was (the cut of the right stem pinned where the O stood in round v33, so that
               the stem no longer follows the O), the O and what follows moved left until the tip of the sweep is 6
               from the top left corner of the O; the O is not cut
Each in the word and, as a mark, turned until the red diagonal stands upright.
Needs shapely (PYTHONPATH). Usage: concepts-v36.py <out folder>"""
import importlib.util
import json
import math
import sys
from pathlib import Path
from shapely.affinity import rotate
from shapely.geometry import Point
from shapely.ops import unary_union


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load('c25', 'concepts-v25.py')
V31 = load('c31', 'concepts-v31.py')
UPRIGHT = -(90 - math.degrees(math.atan2(100, 78)))
CUT, GAP, N_WIDTH, STEM_X = 26, 6, 120, 90
V33_MIRROR_SHIFT = 35
BASE = dict(k_builder=V31.k_sweep, o_width=104, bar4=(13, 37), arm_mode='merge', seam=4, red_width=30)


def dark_line_at_stem(red_width=30, line=4.5):
    """where the dark line around the red diagonal crosses the inner edge of the right stem"""
    boundary_top = 21 + (red_width / 2 + line) / C.SIN
    return 100 - (STEM_X - boundary_top) * C.TAN


def iso_ox(run_tl=CUT):
    """where the O stands so that the outer edge of the triangle (GAP from the top left corner of the O, which runs
    run_tl along the cap line and CUT down the side) meets the inner edge of the stem on the dark line"""
    y_line = dark_line_at_stem()
    long = math.hypot(run_tl, CUT)
    out = (-CUT / long, run_tl / long)
    return STEM_X - GAP * out[0] - (y_line - 100 + CUT - GAP * out[1]) * run_tl / CUT


def pieces_of(concept):
    return list(getattr(concept['ink'], 'geoms', [concept['ink']]))


def n_and_o(concept, ox):
    pieces = pieces_of(concept)
    o_ring = next(piece for piece in pieces if piece.buffer(0.01).contains(Point(ox + 15, 50)))
    n = unary_union([piece for piece in pieces if piece.centroid.x < ox + 15])
    return n, o_ring


def mirror_near_shift():
    """the smallest shift of the O (from its place, 6 past the N) that keeps the N of round v33 GAP from the O"""
    def gap(shift):
        concept = C.concept_a(**BASE, nest_n=True, n_foot=True, n_top_sweep=True, nest_ox=N_WIDTH + GAP + V33_MIRROR_SHIFT, o_shift=shift)
        n, o_ring = n_and_o(concept, N_WIDTH + GAP + shift)
        return n.distance(o_ring)
    low, high = 0.0, float(V33_MIRROR_SHIFT)
    for _ in range(50):
        middle = (low + high) / 2
        if gap(middle) < GAP:
            low = middle
        else:
            high = middle
    return high, gap(high)


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    C.SLASH_ROOM = 0
    C.CHANNEL = C.SLASH_WEIGHT
    iso_shift = iso_ox() - (N_WIDTH + GAP)
    near_shift, near_gap = mirror_near_shift()
    print('iso shift', round(iso_shift, 2), '| mirror-near shift', round(near_shift, 2), 'gap', round(near_gap, 3))
    variants = {
        'iso': dict(n_foot=True, n_triangle=True, o_corners=(CUT * C.RUN, CUT * C.RUN, CUT * C.RUN, CUT), o_shift=iso_shift),
        'mirror-near': dict(nest_n=True, n_foot=True, n_top_sweep=True, nest_ox=N_WIDTH + GAP + V33_MIRROR_SHIFT, o_shift=near_shift),
    }
    report = {'isoShift': iso_shift, 'mirrorNearShift': near_shift, 'mirrorNearGap': near_gap}
    for label, options in variants.items():
        concept = C.concept_a(**BASE, **options)
        concept['name'] = f'A11-{label}'
        out, size, frame = C.write(concept, folder)
        C.write(concept, folder, colour=False)
        (folder / f'concept-a11-{label}.json').write_text(json.dumps({'name': concept['name'], 'svg': out.name, 'size': size, 'slash': concept['slash'], 'frame': frame, 'channel': C.CHANNEL}, indent=1) + '\n')
        ox = N_WIDTH + GAP + options['o_shift']
        n, o_ring = n_and_o(concept, ox)
        right = max((piece for piece in getattr(n, 'geoms', [n])), key=lambda piece: piece.centroid.x)
        report[label] = {'rightPiece': [(round(x, 2), round(y, 2)) for x, y in right.exterior.coords], 'gapNO': round(n.distance(o_ring), 3), 'size': size}
        mark = {'name': f'N-{label}-upright', 'ink': rotate(n, UPRIGHT, origin=(60, 50)), 'red': rotate(concept['red'], UPRIGHT, origin=(60, 50)), 'slash': concept['slash']}
        C.write(mark, folder)
        print(label, out.name, [round(v) for v in size], 'N-O gap', round(n.distance(o_ring), 2))
    (folder / 'report.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
