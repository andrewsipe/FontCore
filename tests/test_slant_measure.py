import math

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from FontCore.core_slant_measure import check_slant, measure_slant


def font_with_stem(shear_degrees: float, declared: float):
    """A font whose H, I, l and E are plain rectangles sheared right by ``shear_degrees``."""
    k = math.tan(math.radians(shear_degrees))

    def stem():
        pen = TTGlyphPen(None)
        pts = [(100, 0), (200, 0), (200, 700), (100, 700)]
        pen.moveTo((round(pts[0][0] + k * pts[0][1]), pts[0][1]))
        for x, y in pts[1:]:
            pen.lineTo((round(x + k * y), y))
        pen.closePath()
        return pen.glyph()

    names = [".notdef", "H", "I", "l", "E"]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): c for c in "HIlE"})
    fb.setupGlyf({n: (TTGlyphPen(None).glyph() if n == ".notdef" else stem()) for n in names})
    fb.setupHorizontalMetrics({n: (500, 0) for n in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost(italicAngle=declared)
    return fb.font


def test_a_sheared_stem_measures_with_the_italic_angle_sign():
    assert abs(measure_slant(font_with_stem(12, -12)).measured + 12) < 0.3


def test_upright_outlines_measure_zero():
    assert abs(measure_slant(font_with_stem(0, 0)).measured) < 0.1


def test_upright_outlines_with_a_declared_angle_are_flagged_not_zeroed_silently():
    c = check_slant(font_with_stem(0, 11.93))
    assert c.verdict == "upright-declared-slanted" and c.declared > 11


def test_a_real_italic_with_the_right_angle_is_ok():
    assert check_slant(font_with_stem(9, -9)).verdict == "ok"


def test_a_real_italic_declared_zero_is_called_out():
    assert check_slant(font_with_stem(9, 0)).verdict == "slanted-declared-upright"


def test_a_flipped_sign_is_named():
    assert check_slant(font_with_stem(9, 9)).verdict == "sign-flipped"


def test_a_font_with_no_stems_is_unmeasurable():
    assert check_slant(_empty()).verdict == "unmeasurable"


def _empty():
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    return fb.font
