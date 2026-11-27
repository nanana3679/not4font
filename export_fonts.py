"""Build the edition 1 Regular and Bold fonts as TTF and WOFF2."""

import argparse
import json
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase, digits

from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.affinity import translate
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from not4k_font.geometry import pieces_of
from not4k_font.glyphs import BOLD, CHARACTERS, REGULAR, build_glyphs, draw_z
from not4k_font.spacing import clear_ink, cut_overlaps, edition_kerning, least_shift, symbol_pair_shift
from not4k_font.symbols import SYMBOLS, TAIL_OVERHANGS, build_symbols
from not4k_font.word_ends import allowed_positions, preferred_position, word_end_variant


HERE = Path(__file__).parent
UNITS_PER_DESIGN_UNIT = 20
UNITS_PER_EM = 128 * UNITS_PER_DESIGN_UNIT
FONT_CHARACTERS = CHARACTERS + SYMBOLS
GLYPH_NAMES = {
    char: UV2AGL.get(ord(char.upper()), f"uni{ord(char.upper()):04X}")
    for char in FONT_CHARACTERS
}
WEIGHTS = (("Regular", REGULAR, 400), ("Bold", BOLD, 700))
FAMILY = "NOT4FONT"


def font_units(value):
    return otRound(value * UNITS_PER_DESIGN_UNIT)


def draw_glyph(shape):
    pen = TTGlyphPen(None)
    if shape.is_empty:
        return pen.glyph()
    for polygon in pieces_of(shape):
        polygon = orient(polygon, sign=-1)
        for ring in (polygon.exterior, *polygon.interiors):
            first, *rest = ring.coords[:-1]
            pen.moveTo(tuple(map(font_units, first)))
            for point in rest:
                pen.lineTo(tuple(map(font_units, point)))
            pen.closePath()
    return pen.glyph()


def glyph_class(names):
    return "[" + " ".join(names) + "]"


def kerning_feature(
    pair_shifts, metrics, clipped_names, tabular_adjustments, word_forms, outlines, glyphs, letter_space
):
    forms = {name: [name] for name in GLYPH_NAMES.values()}
    for char, variants in word_forms.items():
        forms[GLYPH_NAMES[char]].extend(name for name, _ in variants.values())
    for pair in tabular_adjustments:
        for name in pair:
            forms.setdefault(name, [name])
    for names in forms.values():
        names.extend(clipped_names[name] for name in names.copy() if name in clipped_names)

    adjustments = {
        (GLYPH_NAMES[left], GLYPH_NAMES[right]): font_units(shift) - metrics[GLYPH_NAMES[left]][0]
        for (left, right), shift in pair_shifts.items()
    }
    adjustments.update(tabular_adjustments)
    rules = []
    for (left_name, right_name), adjustment in adjustments.items():
        if adjustment:
            left_forms, right_forms = forms[left_name], forms[right_name]
            if word_forms:
                left_class = left_forms[0] if len(left_forms) == 1 else glyph_class(left_forms)
                right_class = right_forms[0] if len(right_forms) == 1 else glyph_class(right_forms)
                rules.append(f"  pos {left_class} {right_class} {adjustment};")
            else:
                rules.extend(f"  pos {left} {right} {adjustment};" for left, right in product(left_forms, right_forms))
    boundary = swash_boundary_kerning(word_forms, clipped_names, forms, outlines, glyphs, pair_shifts, letter_space)
    return "\n".join(["feature kern {", *rules, *boundary, "} kern;"])


def swash_boundary_kerning(word_forms, clipped_names, forms, outlines, glyphs, pair_shifts, letter_space):
    """Give word-end swashes room next to spaces and marks.

    Every separator moves by the swash's overhang beyond the base outline. A mark whose ink would still
    come closer than the letter space, such as a comma tail under a low swash, gets a pair rule that
    moves it until the inks clear. Pair rules come before class rules in the lookup, so they win.
    """
    if not word_forms:
        return []
    before = defaultdict(list)
    after = defaultdict(list)
    exceptions = []
    for char, variants in word_forms.items():
        base = outlines[GLYPH_NAMES[char]]
        for (start, end), (name, shape) in variants.items():
            alternates = [name, clipped_names[name]] if name in clipped_names else [name]
            outline = outlines[name]
            for side, active, overhang, groups in (
                (-1, start, base.xMin - outline.xMin, before),
                (1, end, outline.xMax - base.xMax, after),
            ):
                if not active:
                    continue
                overhang = max(overhang, 0)
                if overhang:
                    groups[overhang].extend(alternates)
                for mark in SYMBOLS:
                    pair = (char, mark) if side == 1 else (mark, char)
                    shift = pair_shifts[pair] + overhang / UNITS_PER_DESIGN_UNIT
                    amount = overhang + tail_clearance(shape, glyphs[mark], side, shift, letter_space)
                    if amount > overhang:
                        marks = forms[GLYPH_NAMES[mark]]
                        pairs = product(alternates, marks) if side == 1 else product(marks, alternates)
                        exceptions.extend(f"  pos {left} {right} {amount};" for left, right in pairs)
    separators = glyph_class(["space", *(form for char in SYMBOLS for form in forms[GLYPH_NAMES[char]])])
    return [
        "lookup SwashClearance {",
        *exceptions,
        *(f"  pos {separators} {glyph_class(names)} {amount};" for amount, names in before.items()),
        *(f"  pos {glyph_class(names)} {separators} {amount};" for amount, names in after.items()),
        "} SwashClearance;",
    ]


def tail_clearance(swash, mark, side, shift, letter_space):
    """Return the font units a mark needs beyond `shift` so its ink stays the letter space from a swash."""
    left, right = (swash, mark) if side == 1 else (mark, swash)
    return font_units(clear_ink(left, right, shift, letter_space) - shift)


def add_word_end_glyphs(glyphs, outlines, metrics):
    forms = {}
    for char in ascii_lowercase:
        name = GLYPH_NAMES[char]
        base = glyphs[char]
        starts, ends = (
            {position: word_end_variant(glyphs, char, side, position)[0] for position in allowed_positions(char, side)}
            for side in (-1, 1)
        )
        forms[char] = {}
        for start, end in product((None, *starts), (None, *ends)):
            if not start and not end:
                continue
            variant_name = name
            if start:
                variant_name += f".start{start.title()}"
            if end:
                variant_name += f".end{end.title()}"
            if start and end:
                variants = (starts[start], ends[end])
                removed = unary_union([base.difference(variant) for variant in variants])
                added = unary_union([variant.difference(base) for variant in variants])
                outline = base.difference(removed).union(added)
            else:
                outline = starts[start] if start else ends[end]
            glyph = draw_glyph(outline)
            outlines[variant_name] = glyph
            metrics[variant_name] = (metrics[name][0], glyph.coordinates.calcIntBounds()[0])
            forms[char][start, end] = (variant_name, outline)
    return forms


def add_tabular_digits(outlines, metrics, letter_space):
    bounds = {
        GLYPH_NAMES[digit]: outlines[GLYPH_NAMES[digit]].coordinates.calcIntBounds()
        for digit in digits
    }
    # Keep the widest outline inside the cell, including the crossbar of 4.
    advance = max(right - left for left, _, right, _ in bounds.values()) + font_units(letter_space)
    names = {}
    for name, (left, _, right, _) in bounds.items():
        tabular_name = f"{name}.tnum"
        side_bearing = (advance - (right - left)) // 2
        tabular_glyph = deepcopy(outlines[name])
        tabular_glyph.coordinates.translate((side_bearing - left, 0))
        outlines[tabular_name] = tabular_glyph
        metrics[tabular_name] = (advance, side_bearing)
        names[name] = tabular_name
    return names


def tabular_outlines(glyphs, tabular_names, metrics):
    """Return each tabular digit outline in design units, placed in its cell."""
    shapes = {}
    for digit in digits:
        name = GLYPH_NAMES[digit]
        tabular = tabular_names[name]
        offset = (metrics[tabular][1] - metrics[name][1]) / UNITS_PER_DESIGN_UNIT
        shapes[tabular] = translate(glyphs[digit], xoff=offset)
    return shapes


def tabular_mark_kerning(glyphs, tabular_names, metrics, letter_space):
    """Move comma tails apart from tabular digits, which take no other kerning, keeping the cells fixed."""
    adjustments = {}
    for tabular, digit in tabular_outlines(glyphs, tabular_names, metrics).items():
        for char in TAIL_OVERHANGS:
            mark = GLYPH_NAMES[char]
            for left, right, left_shape, right_shape in (
                (tabular, mark, digit, glyphs[char]),
                (mark, tabular, glyphs[char], digit),
            ):
                advance = metrics[left][0] / UNITS_PER_DESIGN_UNIT
                shift = clear_ink(left_shape, right_shape, advance, letter_space)
                adjustment = font_units(shift) - metrics[left][0]
                if adjustment > 0:
                    adjustments[left, right] = adjustment
    return adjustments


def add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, word_forms, outlines, metrics):
    r_name = GLYPH_NAMES["r"]
    r_pieces = pieces_of(glyphs["r"])
    r_advance = metrics[r_name][0] / UNITS_PER_DESIGN_UNIT
    candidates = {
        name: (glyphs[char], pair_shifts["r", char])
        for char, name in GLYPH_NAMES.items()
    }
    for char, variants in word_forms.items():
        for (start, _), (name, shape) in variants.items():
            if start is None:
                candidates[name] = (shape, pair_shifts["r", char])
    for tabular, shape in tabular_outlines(glyphs, tabular_names, metrics).items():
        candidates[tabular] = (shape, r_advance)

    names = {}
    for name, (shape, shift) in candidates.items():
        positioned = translate(shape, xoff=shift)
        cut = cut_overlaps(positioned, r_pieces, weight)
        if cut is None:
            continue
        glyph = draw_glyph(translate(cut, xoff=-shift))
        clipped_name = f"{name}.afterR"
        outlines[clipped_name] = glyph
        metrics[clipped_name] = (metrics[name][0], glyph.coordinates.calcIntBounds()[0])
        names[name] = clipped_name
    return names


def word_end_lookups(glyphs, word_forms, tabular_names):
    context = glyph_class([
        *(GLYPH_NAMES[char] for char in ascii_lowercase + digits),
        *tabular_names.values(),
        *(name for variants in word_forms.values() for name, _ in variants.values()),
    ])
    starts, ends = {}, {}
    preferences = {"PreferUpper": {}, "PreferLower": {}}
    for char, variants in word_forms.items():
        name = GLYPH_NAMES[char]
        start = preferred_position(char, -1, glyphs[char])
        end = preferred_position(char, 1, glyphs[char])
        starts[name] = variants[start, None][0]
        ends[name] = variants[None, end][0]
        for (left, right), (variant, _) in variants.items():
            if left and not right:
                ends[variant] = variants[left, end][0]
            for position, table in zip(("top", "bottom"), preferences.values()):
                preferred_left = position if left and (position, right) in variants else left
                preferred_right = position if right and (preferred_left, position) in variants else right
                target = variants[preferred_left, preferred_right][0]
                if variant != target:
                    table[variant] = target
    initial_class, final_class = glyph_class(starts), glyph_class(ends)
    return [
        "lookup WordStarts {",
        f"  ignore sub {context} {initial_class}';",
        f"  sub {initial_class}' by {glyph_class(starts.values())};",
        "} WordStarts;",
        "lookup WordEnds {",
        f"  ignore sub {final_class}' {context};",
        f"  sub {final_class}' by {glyph_class(ends.values())};",
        "} WordEnds;",
        *(
            f"lookup {lookup} {{ sub {glyph_class(table)} by {glyph_class(table.values())}; }} {lookup};"
            for lookup, table in preferences.items()
        ),
    ]


def substitution_features(glyphs, tabular_names, clipped_names, word_forms):
    # Run tnum, word endings and their style preferences before cutting after R.
    lines = [f"feature tnum {{ sub {glyph_class(tabular_names)} by {glyph_class(tabular_names.values())}; }} tnum;"]
    r = GLYPH_NAMES["r"]
    r_context = [r, clipped_names[r]]
    if word_forms:
        lines.extend(word_end_lookups(glyphs, word_forms, tabular_names))
        r_context.extend(name for (start, end), (name, _) in word_forms["r"].items() if start and not end)
    lines.append(
        f"lookup AfterR {{ sub {glyph_class(r_context)} {glyph_class(clipped_names)}'"
        f" by {glyph_class(clipped_names.values())}; }} AfterR;"
    )
    if word_forms:
        lines.extend([
            "feature calt { lookup WordStarts; lookup WordEnds; lookup AfterR; } calt;",
            "feature ss01 { featureNames { name \"Upper word-end swashes\"; }; lookup PreferUpper; } ss01;",
            "feature ss02 { featureNames { name \"Lower word-end swashes\"; }; lookup PreferLower; } ss02;",
        ])
    else:
        lines.append("feature calt { lookup AfterR; } calt;")
    return "\n".join(lines)


def pair_shifts_for(glyphs, bodies, letter_space, extra_kerning):
    shifts = {}
    for left in GLYPH_NAMES:
        for right in GLYPH_NAMES:
            if left in SYMBOLS or right in SYMBOLS:
                # Keep short marks in reading order. Letters are measured by their ink to clear the
                # overhangs of R and 4, and marks by their bodies so that comma tails hang outside.
                edge = bodies[left] if left in SYMBOLS else glyphs[left]
                shift = symbol_pair_shift(glyphs[left], glyphs[right], edge, bodies[right], letter_space)
            else:
                shift = least_shift(bodies[left], bodies[right], letter_space)
                shift += extra_kerning.get((left, right), 0)
            shifts[left, right] = shift
    return shifts


def build_font(edition, style, weight, weight_class):
    bold = style == "Bold"
    glyphs, bodies = build_glyphs(weight)
    glyphs["z"] = bodies["z"] = draw_z(weight, angled_ends=True)
    letter_space = weight.letter_space
    extra_kerning = edition_kerning(glyphs, bodies, letter_space)
    symbol_outlines, symbol_bodies = build_symbols(weight)
    glyphs.update(symbol_outlines)
    bodies.update(symbol_bodies)
    weight_record = edition["weights"][style.lower()]
    space_advance = font_units(edition["rules"]["space"])

    outlines = {name: TTGlyphPen(None).glyph() for name in (".notdef", "space")}
    metrics = {name: (space_advance, 0) for name in outlines}
    for char, name in GLYPH_NAMES.items():
        if char in SYMBOLS:
            left, _, right, _ = bodies[char].bounds
        else:
            left, _, right, _ = weight_record["glyphs"][char.upper()]["spacingBody"]
        outlines[name] = draw_glyph(glyphs[char])
        metrics[name] = (font_units(right - left), font_units(glyphs[char].bounds[0]))
    tabular_names = add_tabular_digits(outlines, metrics, letter_space)
    word_forms = add_word_end_glyphs(glyphs, outlines, metrics) if bold else {}
    pair_shifts = pair_shifts_for(glyphs, bodies, letter_space, extra_kerning)
    clipped_names = add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, word_forms, outlines, metrics)
    tabular_adjustments = tabular_mark_kerning(glyphs, tabular_names, metrics, letter_space)

    cmap = {ord(char): GLYPH_NAMES[char.lower()] for char in FONT_CHARACTERS + ascii_uppercase}
    cmap[ord(" ")] = "space"
    ps_name = f"{FAMILY}-{style}"
    frozen = datetime.fromisoformat(edition["frozen"]).replace(tzinfo=timezone.utc)
    timestamp = timestampSinceEpoch(frozen.timestamp())
    ascent, descent = font_units(112), font_units(-16)

    builder = FontBuilder(UNITS_PER_EM)
    builder.updateHead(created=timestamp, modified=timestamp, macStyle=int(bold))
    builder.setupGlyphOrder(list(outlines))
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=descent)
    builder.setupNameTable({
        "familyName": FAMILY,
        "styleName": style,
        "uniqueFontIdentifier": f"{ps_name};1.000",
        "fullName": f"{FAMILY} {style}",
        "psName": ps_name,
        "version": "Version 1.000",
    })
    builder.setupOS2(
        version=4,
        usWeightClass=weight_class,
        fsSelection=0x80 | (0x20 if bold else 0x40),
        sTypoAscender=ascent,
        sTypoDescender=descent,
        usWinAscent=ascent,
        usWinDescent=-descent,
        sCapHeight=font_units(100),
        sxHeight=font_units(100),
    )
    builder.setupPost()
    kern = kerning_feature(
        pair_shifts, metrics, clipped_names, tabular_adjustments, word_forms, outlines, glyphs, letter_space
    )
    substitutions = substitution_features(glyphs, tabular_names, clipped_names, word_forms)
    addOpenTypeFeaturesFromString(builder.font, f"{kern}\n{substitutions}")
    return builder.font


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=HERE / "out" / "fonts")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    edition = json.loads((HERE / "ed1" / "font-ed1.json").read_text())
    for style, weight, weight_class in WEIGHTS:
        font = build_font(edition, style, weight, weight_class)
        font.save(output / f"{FAMILY}-{style}.ttf")
        font.flavor = "woff2"
        font.save(output / f"{FAMILY}-{style}.woff2")


if __name__ == "__main__":
    main()
