"""Reviewed Bold swashes for the left and right edges of a word."""

import math
from string import ascii_lowercase

from shapely.affinity import affine_transform, rotate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from .geometry import CORNER_HEIGHT, DIAGONAL_RUN, pieces_of, polygon
from .glyphs import BOLD, draw_t


BLOCKED_PLACEMENTS = {
    (-1, "bottom"): frozenset("juv"),
    (1, "top"): frozenset("l"),
    (1, "bottom"): frozenset("efjpuv"),
}

SWASH_HEIGHT = 12
SWASH_RUN = SWASH_HEIGHT / math.tan(math.radians(30))
J_HOOK_HEIGHT = 40
J_DECORATED_HEIGHT = J_HOOK_HEIGHT + BOLD.stem / (2 * DIAGONAL_RUN)


def allowed_positions(char, side):
    return tuple(
        position
        for position in ("top", "bottom")
        if char in ascii_lowercase and char not in BLOCKED_PLACEMENTS.get((side, position), ())
    )


def outer_span(shape, level, side, min_length=4):
    section = shape.intersection(LineString([(-200, level), (400, level)]))
    segments = [part for part in pieces_of(section) if part.length > min_length]
    if not segments:
        return None
    index = 0 if side == -1 else 2
    edge = max(segments, key=lambda segment: side * segment.bounds[index])
    return edge.bounds[index], min(10, edge.length / 2)


def sweep_polygon(side, level, inward, edge, anchor):
    base_x, base_inset = edge
    anchor_x, anchor_inset = anchor
    tip = anchor_x + side * SWASH_RUN
    inner_level = level + inward * SWASH_HEIGHT
    return polygon([
        (anchor_x, inner_level), (tip, level),
        (base_x - side * base_inset, level), (anchor_x - side * anchor_inset, inner_level),
    ])


def original_sweep(shape, side, levels=((0, 1), (100, -1))):
    extreme = shape.bounds[0 if side == -1 else 2]
    candidates = []
    for level, inward in levels:
        edge = outer_span(shape, level + inward * 0.01, side)
        anchor = outer_span(shape, level + inward * SWASH_HEIGHT, side)
        if edge is None or anchor is None:
            continue
        if (anchor[0] + side * SWASH_RUN - extreme) * side < 8:
            continue
        distance = abs(extreme - anchor[0]) + abs(extreme - edge[0]) * 0.25
        candidates.append((distance, sweep_polygon(side, level, inward, edge, anchor)))
    return min(candidates, key=lambda candidate: candidate[0])[1] if candidates else polygon([])


def preferred_position(char, side, shape):
    positions = allowed_positions(char, side)
    if len(positions) == 1:
        return positions[0]
    if char in "sz":
        return "top" if (char, side) in (("s", 1), ("z", -1)) else "bottom"
    sweep = original_sweep(shape, side)
    return "top" if not sweep.is_empty and sweep.bounds[3] == 100 else "bottom"


def supported_sweep(edge, level, inward, side, cut=0):
    support = polygon([
        (edge, level), (edge - side * cut * DIAGONAL_RUN, level),
        (edge, level + inward * cut),
    ]) if cut else polygon([])
    tip = edge + side * SWASH_RUN
    back = edge - side * 10
    anchor_y = level + inward * SWASH_HEIGHT
    extension = polygon([(tip, level), (back, level), (back, anchor_y), (edge, anchor_y)])
    return support, extension


def rounded_sweep(char, shape, side, position):
    top = position == "top"
    level, inward = (100, -1) if top else (0, 1)
    if side == -1:
        cut = 0 if char in "pr" else CORNER_HEIGHT
        return supported_sweep(0, level, inward, side, cut)
    if char in "qr" and not top:
        return polygon([]), original_sweep(shape, side, levels=((0, 1),))
    if char in "pr":
        bowl_edge = 100 if top else BOLD.bowl_bottom
        return supported_sweep(BOLD.bowl_width, bowl_edge, inward, side, CORNER_HEIGHT)
    if char == "g" and not top:
        return supported_sweep(shape.bounds[2], level, inward, side)
    edge = BOLD.scaled_width(104) if char == "q" else shape.bounds[2]
    return supported_sweep(edge, level, inward, side, CORNER_HEIGHT)


def stroke_sweep(char, shape, side, position):
    top = position == "top"
    level, inward = (100, -1) if top else (0, 1)
    if char == "s":
        edge = shape.bounds[0 if side == -1 else 2]
        return supported_sweep(edge, level, inward, side, CORNER_HEIGHT)
    if char == "j" and side == 1 and not top:
        cut = 20
        return supported_sweep(shape.bounds[2] - cut * DIAGONAL_RUN, 0, 1, side, cut)
    edge, _ = outer_span(shape, level + inward * 0.01, side)
    return supported_sweep(edge, level, inward, side)


T_OUTLINE = draw_t(BOLD)
T_RIGHT_EDGE = T_OUTLINE.bounds[2]
T_SWEEP = original_sweep(T_OUTLINE, 1)


def decorated_recut_bar(char, shape, side):
    height = BOLD.stacked_horizontal
    edge = shape.bounds[2] if char == "l" else (CORNER_HEIGHT - height) * DIAGONAL_RUN
    outward = 1 if char == "l" else -1
    heel = edge - outward * height * DIAGONAL_RUN
    inner = heel - outward * 2
    cap = polygon([(inner, 0), (edge, 0), (heel, height), (inner, height)])
    cut = box(min(inner, edge), 0, max(inner, edge), height)
    sweep = affine_transform(T_SWEEP, (outward, 0, 0, -1, edge - outward * T_RIGHT_EDGE, 100))
    if char == "s" and side == 1:
        origin = (shape.bounds[2] / 2, 50)
        cap, cut, sweep = (rotate(part, 180, origin=origin) for part in (cap, cut, sweep))
    base = shape.difference(cut).union(cap)
    return base.union(sweep), sweep.difference(base)


def rotated_l_cap(glyphs):
    height = BOLD.stacked_horizontal
    l_shape = glyphs["l"]
    heel = l_shape.bounds[2] - height * DIAGONAL_RUN
    clip = box(heel - BOLD.stem, 0, l_shape.bounds[2] + SWASH_RUN + 1, height)
    decorated, accent = decorated_recut_bar("l", l_shape, 1)
    transform = (-1, 0, 0, -1, glyphs["j"].bounds[0] + heel, J_DECORATED_HEIGHT)
    cap = affine_transform(decorated.intersection(clip), transform)
    return cap, affine_transform(accent.intersection(clip), transform)


def cap_sweep(shape, side, position):
    level, inward = (100, -1) if position == "top" else (0, 1)
    inside = level + 16 * inward
    band = box(-200, min(level, inside), 400, max(level, inside))
    edge_index = 0 if side == -1 else 2
    in_band = [(part, part.intersection(band)) for part in pieces_of(shape)]
    stroke, _ = max(
        ((part, cropped) for part, cropped in in_band if not cropped.is_empty),
        key=lambda pair: side * pair[1].bounds[edge_index],
    )
    other_strokes = shape.difference(stroke).buffer(BOLD.stencil_gap, join_style="mitre")
    for inset in (0, 4, 8, 16):
        end = level + inset * inward
        edge = outer_span(stroke, end + inward * 0.01, side, min_length=0)
        anchor = outer_span(stroke, end + inward * SWASH_HEIGHT, side)
        if edge is None or anchor is None:
            continue
        candidate = sweep_polygon(side, end, inward, edge, anchor).difference(other_strokes)
        attached = unary_union([piece for piece in pieces_of(candidate) if piece.intersection(stroke).area > 1])
        if attached.difference(shape).area >= 25:
            return attached
    raise ValueError(f"No connected {position} sweep on side {side}")


def word_end_variant(glyphs, char, side, position):
    shape = glyphs[char]
    if (char, side, position) == ("j", -1, "top"):
        cap, accent = rotated_l_cap(glyphs)
        old_cap = box(shape.bounds[0] - 1, cap.bounds[1], cap.bounds[2], J_HOOK_HEIGHT + 1)
        return shape.difference(old_cap).union(cap), accent, polygon([])
    if (char, side, position) in (("s", -1, "bottom"), ("s", 1, "top"), ("l", 1, "bottom")):
        outline, accent = decorated_recut_bar(char, shape, side)
        return outline, accent, polygon([])
    if char in "bdcgoqpr":
        support, sweep = rounded_sweep(char, shape, side, position)
    elif char in "slj":
        support, sweep = stroke_sweep(char, shape, side, position)
    elif (char, side, position) in (("z", -1, "top"), ("z", 1, "bottom")):
        upper_left = affine_transform(T_SWEEP, (-1, 0, 0, 1, T_RIGHT_EDGE, 0))
        sweep = upper_left if side == -1 else rotate(upper_left, 180, origin=(shape.bounds[2] / 2, 50))
        support = polygon([])
    else:
        support, sweep = polygon([]), cap_sweep(shape, side, position)
    supported = shape.union(support)
    return supported.union(sweep), sweep.difference(supported), support.difference(shape)
