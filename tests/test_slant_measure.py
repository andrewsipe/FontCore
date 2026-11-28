import math

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from FontCore import core_slant_measure
from FontCore.core_slant_measure import check_slant, confirmed_slant, measure_slant, stem_centre_lean


def font_with_stem(shear_degrees: float, declared: float, letters: str = "HIlE"):
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

    names = [".notdef", *letters]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): c for c in letters})
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


def test_a_stair_stepped_slant_is_not_called_upright():
    from FontCore.core_slant_measure import STAIR_GAP  # noqa: F401

    def stairs():
        pen = TTGlyphPen(None)
        pts = []
        # a stem 100 wide built from 100-tall blocks, each shifted right 25: vertical edges, slanted overall
        x = 0
        left, right = [], []
        for i in range(8):
            y0, y1 = i * 100, (i + 1) * 100
            left += [(x, y0), (x, y1)]
            right += [(x + 100, y0), (x + 100, y1)]
            x += 25
        pen.moveTo(left[0])
        for pt in left[1:]:
            pen.lineTo(pt)
        for pt in reversed(right):
            pen.lineTo(pt)
        pen.closePath()
        return pen.glyph()

    names = [".notdef", "H", "I", "l", "E"]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): c for c in "HIlE"})
    fb.setupGlyf({n: (TTGlyphPen(None).glyph() if n == ".notdef" else stairs()) for n in names})
    fb.setupHorizontalMetrics({n: (500, 0) for n in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Italic"})
    fb.setupOS2()
    fb.setupPost(italicAngle=-15)
    assert check_slant(fb.font).verdict == "unmeasurable"


def test_the_stem_centre_line_follows_the_shear():
    assert abs(stem_centre_lean(font_with_stem(12, -12)) + 12) < 0.3
    assert abs(stem_centre_lean(font_with_stem(0, 0))) < 0.1


def test_a_second_measure_confirms_a_clean_italic():
    assert abs(confirmed_slant(font_with_stem(9, -9, "HIlEhnmu")) + 9) < 0.3


def test_an_upright_is_not_confirmed_as_leaning():
    assert confirmed_slant(font_with_stem(0, 0)) is None


def test_edges_the_centre_line_does_not_back_are_not_confirmed(monkeypatch):
    monkeypatch.setattr(core_slant_measure, "stem_centre_lean", lambda font: 33.0)
    assert confirmed_slant(font_with_stem(9, -9)) is None


def test_no_centre_line_means_not_confirmed(monkeypatch):
    monkeypatch.setattr(core_slant_measure, "stem_centre_lean", lambda font: None)
    assert confirmed_slant(font_with_stem(9, -9)) is None


def _with_axis(font, tag="ROTA", low=-15, default=-15, high=15):
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables._f_v_a_r import Axis

    fvar = newTable("fvar")
    axis = Axis()
    axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue, axis.axisNameID = tag, low, default, high, 256
    fvar.axes = [axis]
    fvar.instances = []
    font["fvar"] = fvar
    return font


def test_an_axis_that_moves_the_lean_is_named(monkeypatch):
    from fontTools.varLib import instancer

    from FontCore.core_slant_measure import lean_axes

    base = _with_axis(font_with_stem(0, 0))
    monkeypatch.setattr(instancer, "instantiateVariableFont", lambda f, loc, inplace=False: font_with_stem(15, -15))
    moves = lean_axes(base)
    assert list(moves) == ["ROTA"] and abs(moves["ROTA"] - 15) < 0.5


def test_an_axis_that_leaves_the_lean_alone_is_not_named(monkeypatch):
    from fontTools.varLib import instancer

    from FontCore.core_slant_measure import lean_axes

    base = _with_axis(font_with_stem(9, -9), tag="wght", low=100, default=400, high=900)
    monkeypatch.setattr(instancer, "instantiateVariableFont", lambda f, loc, inplace=False: font_with_stem(9, -9))
    assert lean_axes(base) == {}


def test_a_static_font_has_no_lean_axes():
    from FontCore.core_slant_measure import lean_axes

    assert lean_axes(font_with_stem(9, -9)) == {}


def test_an_axis_that_cannot_be_built_is_skipped_not_fatal(monkeypatch):
    from fontTools.varLib import instancer

    from FontCore.core_slant_measure import lean_axes

    def boom(*a, **k):
        raise ValueError("cannot instantiate")

    monkeypatch.setattr(instancer, "instantiateVariableFont", boom)
    assert lean_axes(_with_axis(font_with_stem(9, -9))) == {}


def test_lean_axes_does_not_print_the_fonts_own_faults(monkeypatch, caplog):
    import logging

    from fontTools.varLib import instancer

    from FontCore.core_slant_measure import lean_axes

    def noisy(f, loc, inplace=False):
        logging.getLogger("fontTools.varLib.instancer").warning("Invalid avar SegmentMap record")
        return font_with_stem(15, -15)

    monkeypatch.setattr(instancer, "instantiateVariableFont", noisy)
    with caplog.at_level(logging.WARNING):
        lean_axes(_with_axis(font_with_stem(0, 0)))
    assert "Invalid avar" not in caplog.text
