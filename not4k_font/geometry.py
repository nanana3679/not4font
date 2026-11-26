"""Polygon operations in design units, with Y increasing above the baseline."""

import math

from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

DIAGONAL_TAN = 100 / 78
DIAGONAL_SIN = DIAGONAL_TAN / math.hypot(1, DIAGONAL_TAN)
DIAGONAL_COS = 1 / math.hypot(1, DIAGONAL_TAN)
DIAGONAL_RUN = 1 / DIAGONAL_TAN
RISING = (DIAGONAL_COS, DIAGONAL_SIN)
FALLING = (DIAGONAL_COS, -DIAGONAL_SIN)
UPPER_LEFT = (-DIAGONAL_SIN, DIAGONAL_COS)
LOWER_RIGHT = (DIAGONAL_SIN, -DIAGONAL_COS)
CORNER_HEIGHT = 26
CORNER_RUN = CORNER_HEIGHT * DIAGONAL_RUN


def rectangle(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def unit_vector(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def diagonal_stroke(start, end, width, *, before=0.0, after=0.0):
    """Build a square-ended stroke with optional extensions along its axis."""
    ux, uy = unit_vector(start, end)
    x0, y0 = start[0] - ux * before, start[1] - uy * before
    x1, y1 = end[0] + ux * after, end[1] + uy * after
    nx, ny = -uy * width / 2, ux * width / 2
    return [(x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny), (x0 + nx, y0 + ny)]


def clip_half_plane(poly, a, b, c):
    """keeps the part of a convex polygon where a*x + b*y + c >= 0"""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def keep_side(poly, p, q, inside):
    """keeps the side of the line through p and q on which the point `inside` lies"""
    a, b = -(q[1] - p[1]), q[0] - p[0]
    c = -(a * p[0] + b * p[1])
    if a * inside[0] + b * inside[1] + c < 0:
        a, b, c = -a, -b, -c
    return clip_half_plane(poly, a, b, c)


def clip_to_box(poly, x0=-1e9, y0=-1e9, x1=1e9, y1=1e9):
    for a, b, c in ((1, 0, -x0), (0, 1, -y0), (-1, 0, x1), (0, -1, y1)):
        poly = clip_half_plane(poly, a, b, c)
    return poly


def offset_edges(poly, distance):
    """moves every edge of a convex polygon outwards by `distance` (a number, or one number per edge)"""
    area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))
    turn = 1 if area > 0 else -1
    count = len(poly)
    ds = distance if isinstance(distance, (list, tuple)) else [distance] * count
    lines = []
    for i in range(count):
        p, q = poly[i], poly[(i + 1) % count]
        ux, uy = unit_vector(p, q)
        nx, ny = uy * turn, -ux * turn  # outwards
        lines.append(((p[0] + nx * ds[i], p[1] + ny * ds[i]), (ux, uy)))
    out = []
    for i in range(count):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def polygon(points):
    return Polygon(points).buffer(0)


def add_vector(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def at_left_origin(shape):
    return translate(shape, -shape.bounds[0], 0)


def pieces_of(shape):
    return getattr(shape, "geoms", (shape,))


def discard_small_pieces(shape, minimum_area):
    return unary_union([piece for piece in pieces_of(shape) if piece.area >= minimum_area])
