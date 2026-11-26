"""Draw the punctuation, numeric operators, and key labels used in the game UI."""

from shapely.affinity import scale, translate
from shapely.ops import unary_union

from .geometry import DIAGONAL_RUN, at_left_origin, polygon, rectangle


def chamfered_block(width, height, cut):
    run = cut * DIAGONAL_RUN
    return polygon(
        [
            (run, 0),
            (width - run, 0),
            (width, cut),
            (width, height - cut),
            (width - run, height),
            (run, height),
            (0, height - cut),
            (0, cut),
        ]
    )


def dot(weight):
    size = round(weight.stem * 0.7) + 3
    return chamfered_block(size, size, 4)


def comma(weight):
    head = dot(weight)
    width = head.bounds[2]
    tail = polygon(
        [
            (0, -12),
            (width - 12 * DIAGONAL_RUN, -12),
            (width, 0),
            (width, width - 4),
            (width - 4 * DIAGONAL_RUN, width - 4),
        ]
    )
    return head.union(tail)


def colon(weight, bottom):
    return unary_union([translate(bottom, yoff=14), translate(dot(weight), yoff=62)])


def ellipse_dots(weight):
    point = dot(weight)
    step = point.bounds[2] + weight.stencil_gap * 2
    return unary_union([translate(point, xoff=step * index) for index in range(3)])


def horizontal_bar(weight, width, center=50):
    height = weight.stacked_horizontal
    return translate(chamfered_block(width, height, 4), yoff=center - height / 2)


def diagonal_bar(height, thickness, bottom=0):
    run = height * DIAGONAL_RUN
    return polygon(
        [
            (0, bottom),
            (thickness, bottom),
            (run + thickness, bottom + height),
            (run, bottom + height),
        ]
    )


def reflect(shape):
    return scale(shape, xfact=-1, origin="center")


def plus(weight):
    width = 66
    left = (width - weight.stem) / 2
    upright = polygon(rectangle(left, 16, left + weight.stem, 84))
    return horizontal_bar(weight, width).union(upright)


def multiply(weight):
    rising = diagonal_bar(64, weight.diagonal_across * 0.72, bottom=18)
    return rising.union(reflect(rising))


def percent(weight):
    width = weight.scaled_width(36)
    height = 40
    stroke = round(weight.stem * 0.37) + 2
    frame = chamfered_block(width, height, 8)
    hole = chamfered_block(width - 2 * stroke, height - 2 * stroke, 3)
    counter = frame.difference(translate(hole, xoff=stroke, yoff=stroke))
    slash = diagonal_bar(100, weight.diagonal_across * 0.74)
    return unary_union(
        [
            translate(counter, yoff=60),
            translate(slash, xoff=16),
            translate(counter, xoff=slash.bounds[2] - width + 34),
        ]
    )


def parenthesis(weight):
    turn = 22
    run = turn * DIAGONAL_RUN
    wall = round(weight.stem * 0.65) + 2
    return polygon(
        [
            (run, 0),
            (run + wall, 0),
            (wall, turn),
            (wall, 100 - turn),
            (run + wall, 100),
            (run, 100),
            (0, 100 - turn),
            (0, turn),
        ]
    )


def bracket(weight):
    height = weight.stacked_horizontal
    wall = round(weight.stem * 0.65) + 2
    return unary_union(
        [
            polygon(rectangle(0, 0, wall, 100)),
            horizontal_bar(weight, 37, height / 2),
            horizontal_bar(weight, 37, 100 - height / 2),
        ]
    )


def quote(weight):
    shape = comma(weight)
    return translate(shape, yoff=100 - shape.bounds[3])


def exclamation(weight):
    point = dot(weight)
    width = point.bounds[2]
    upright = chamfered_block(width, 56, 5)
    return point.union(translate(upright, yoff=44))


def question(weight):
    width = weight.scaled_width(70)
    stroke = weight.stacked_horizontal
    outline = chamfered_block(width, 45, 12)
    hole = chamfered_block(width - 2 * stroke, 45 - stroke, 8)
    hook = outline.difference(translate(hole, xoff=stroke)).difference(
        polygon(rectangle(0, 0, width / 2, 22))
    )
    neck = polygon(rectangle(width / 2, 37, width / 2 + stroke, 56))
    point = translate(dot(weight), xoff=width / 2)
    return unary_union([translate(hook, yoff=55), neck, point])


def number_sign(weight):
    stem = diagonal_bar(88, weight.diagonal_across * 0.5, bottom=6)
    width = stem.bounds[2] + 30
    return unary_union(
        [
            stem,
            translate(stem, xoff=30),
            horizontal_bar(weight, width, 32),
            horizontal_bar(weight, width, 68),
        ]
    )


def ampersand(weight):
    width = weight.scaled_width(90)
    stroke = round(weight.stacked_horizontal * 0.66)
    top = chamfered_block(width * 0.66, 46, 12)
    top_hole = chamfered_block(width * 0.66 - 2 * stroke, 46 - 2 * stroke, 5)
    bowl = translate(
        top.difference(translate(top_hole, xoff=stroke, yoff=stroke)), xoff=10, yoff=54
    )

    bottom = chamfered_block(width * 0.8, 54, 13)
    hole = chamfered_block(width * 0.8 - 2 * stroke, 54 - 2 * stroke, 5)
    loop = bottom.difference(translate(hole, xoff=stroke, yoff=stroke))
    loop = loop.difference(polygon(rectangle(width * 0.54, 36, width, 55)))

    tail = reflect(diagonal_bar(78, weight.diagonal_across * 0.74))
    return unary_union([bowl, loop, translate(tail, xoff=10)])


def asterisk(weight):
    cross = scale(multiply(weight), xfact=0.6, yfact=0.6)
    shift = 72 - (cross.bounds[1] + cross.bounds[3]) / 2
    cross = translate(cross, yoff=shift)
    left, _, right, _ = cross.bounds
    bar = translate(horizontal_bar(weight, right - left, center=72), xoff=left)
    return cross.union(bar)


def horizontal_arrow(weight):
    width, head = 96, 34
    thickness = weight.stacked_horizontal
    tip = polygon(
        [
            (width, 50),
            (width - head, 50 + head / DIAGONAL_RUN),
            (width - head, 50 - head / DIAGONAL_RUN),
        ]
    )
    return horizontal_bar(weight, width - head + thickness).union(tip)


def vertical_arrow(weight):
    width, height = 64, 90
    left = (width - weight.stem) / 2
    head_height = width / 2 / DIAGONAL_RUN
    shaft = polygon(rectangle(left, 5, left + weight.stem, height - head_height + 2))
    tip = polygon([(width / 2, height), (width, height - head_height), (0, height - head_height)])
    return shaft.union(tip)


def judgment_diamond(weight):
    half_height = 32
    half_width = half_height * DIAGONAL_RUN
    diamond = polygon([(0, 50), (half_width, 18), (2 * half_width, 50), (half_width, 82)])
    return diamond.difference(diamond.buffer(-round(weight.stem * 0.42), join_style="mitre"))


SYMBOLS = ".,:;-/%+()'\"!?#&×·—…=←→↑↓[]\\`*◇"


def build_symbols(weight):
    point = dot(weight)
    apostrophe = quote(weight)
    paren = parenthesis(weight)
    square = bracket(weight)
    slash = diagonal_bar(100, weight.diagonal_across)
    right = horizontal_arrow(weight)
    up = vertical_arrow(weight)
    shapes = {
        ".": point,
        ",": comma(weight),
        ":": colon(weight, point),
        ";": colon(weight, comma(weight)),
        "-": horizontal_bar(weight, 46),
        "/": slash,
        "%": percent(weight),
        "+": plus(weight),
        "(": paren,
        ")": reflect(paren),
        "'": apostrophe,
        '"': apostrophe.union(
            translate(apostrophe, xoff=apostrophe.bounds[2] + weight.stencil_gap * 2)
        ),
        "!": exclamation(weight),
        "?": question(weight),
        "#": number_sign(weight),
        "&": ampersand(weight),
        "×": multiply(weight),
        "·": translate(point, yoff=50 - point.bounds[3] / 2),
        "—": horizontal_bar(weight, 108),
        "…": ellipse_dots(weight),
        "=": horizontal_bar(weight, 64, 34).union(horizontal_bar(weight, 64, 66)),
        "←": reflect(right),
        "→": right,
        "↑": up,
        "↓": scale(up, yfact=-1, origin=(0, 50)),
        "[": square,
        "]": reflect(square),
        "\\": reflect(slash),
        "`": reflect(apostrophe),
        "*": asterisk(weight),
        "◇": judgment_diamond(weight),
    }
    return {char: at_left_origin(shape) for char, shape in shapes.items()}
