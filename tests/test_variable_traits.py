"""What the font's tables say about a variable font: free axes and slope (DECISIONS.md, Area 5)."""

from __future__ import annotations

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables

from FontCore.core_variable_traits import analyze_variable_traits


def make(axes=(("wght", 100, 400, 900),), *, style="Regular", italic_bits=False, oblique_bit=False,
         stat_ital=None, instances=(), weight_class=400, filename=None):
    """A tiny variable font. ``axes`` is (tag, min, default, max)."""
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": style})
    fb.setupOS2(usWeightClass=weight_class)
    fb.setupPost()
    if axes:
        fb.setupFvar([(t, lo, d, hi, t) for t, lo, d, hi in axes], [
            {"location": {axes[0][0]: axes[0][2]}, "stylename": name} for name in instances
        ])
    font = fb.font
    sel = font["OS/2"].fsSelection
    if italic_bits:
        sel |= 1
        font["head"].macStyle |= 2
    if oblique_bit:
        sel |= 1 << 9
    font["OS/2"].fsSelection = sel
    if stat_ital is not None:
        fb.setupStat(
            [dict(tag="ital", name="Italic", ordering=0)] + [dict(tag=t, name=t, ordering=i + 1) for i, (t, *_ ) in enumerate(axes) if t != "ital"],
            [dict(location={"ital": stat_ital[0]}, name=stat_ital[1])],
        )
    return font


def traits(font, filename=None):
    return analyze_variable_traits(font, filename=filename)


# ---- free axes ---------------------------------------------------------------------------------------------

def test_a_static_font_is_not_variable():
    font = make(axes=())
    assert traits(font).is_variable is False


def test_weight_only():
    t = traits(make())
    assert t.is_variable and t.free_axes == ("wght",) and t.weight_free
    assert t.axes_word is None


@pytest.mark.parametrize(
    "extra,word",
    [(("wdth", 75, 100, 125), "Width"), (("opsz", 8, 14, 144), "OpticalSize"), (("slnt", -12, 0, 0), "Slope"), (("ital", 0, 0, 1), "Slope")],
)
def test_weight_plus_one_common_axis_is_named(extra, word):
    t = traits(make(axes=(("wght", 100, 400, 900), extra)))
    assert t.axes_word == word


def test_weight_plus_one_custom_axis_is_a_count_never_a_name():
    assert traits(make(axes=(("wght", 100, 400, 900), ("GRAD", -50, 0, 100)))).axes_word == "2Axis"


def test_three_or_more_axes_are_counted_including_weight_and_a_free_slope():
    axes = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("slnt", -12, 0, 0))
    t = traits(make(axes=axes))
    assert t.axes_word == "3Axis" and t.slope == "free"


def test_a_locked_axis_in_fvar_is_not_free():
    t = traits(make(axes=(("wght", 100, 400, 900), ("ital", 0, 0, 0))))
    assert t.free_axes == ("wght",) and t.axes_word is None


def test_no_weight_axis_means_weight_is_locked_and_comes_from_the_weight_class():
    t = traits(make(axes=(("wdth", 75, 100, 125),), weight_class=900))
    assert not t.weight_free and t.axes_word == "Width" and t.locked_weight == "Black"
    assert any("weight" in w.lower() for w in t.warnings)


# ---- slope -------------------------------------------------------------------------------------------------

def test_a_free_slope_axis_is_free_and_nothing_else_is_asked():
    t = traits(make(axes=(("wght", 100, 400, 900), ("slnt", -12, 0, 0)), style="Italic", italic_bits=True))
    assert t.slope == "free" and t.slope_word is None


def test_upright_when_every_signal_says_so():
    t = traits(make(stat_ital=(0, "Roman")))
    assert t.slope == "upright" and t.slope_word is None and not t.warnings


def test_italic_when_every_signal_says_so():
    t = traits(make(style="Italic", italic_bits=True, stat_ital=(1, "Italic")))
    assert t.slope == "italic" and t.slope_word == "Italic"


def test_stat_says_upright_but_the_bits_and_names_say_italic_the_bits_and_names_win_with_a_warning():
    t = traits(make(style="Italic", italic_bits=True, stat_ital=(0, "Roman")))
    assert t.slope == "italic"
    assert any("STAT" in w for w in t.warnings)


def test_no_stat_slope_axis_falls_back_to_bits_and_names():
    assert traits(make(style="Italic", italic_bits=True)).slope == "italic"
    assert traits(make()).slope == "upright"


def test_instance_names_ending_in_an_italic_word_vote_italic():
    t = traits(make(style="Regular", instances=("Light Italic", "Bold Italic")))
    assert t.slope_votes["instances"] == "italic"


def test_mixed_or_missing_instances_do_not_vote():
    assert traits(make(instances=("Light", "Bold Italic"))).slope_votes["instances"] is None
    assert traits(make()).slope_votes["instances"] is None


def test_the_angle_word_comes_from_the_font_s_own_name():
    t = traits(make(style="Backslanted", italic_bits=True))
    assert t.slope == "italic" and t.slope_word == "Backslanted"


def test_the_oblique_bit_means_oblique():
    t = traits(make(style="Regular", italic_bits=True, oblique_bit=True, stat_ital=(1, "Slanted")))
    assert t.slope_word == "Oblique"


def test_an_italic_with_no_word_anywhere_falls_back_to_italic_with_a_warning():
    t = traits(make(style="Regular", italic_bits=True, stat_ital=(1, "X")))
    assert t.slope == "italic" and t.slope_word == "Italic"


def test_the_filename_counts_as_a_name_cue():
    t = traits(make(style="Regular"), filename="Probe-VariableItalic.ttf")
    assert t.slope_votes["name"] == "italic"


def test_italic_angle_is_never_a_vote():
    font = make()
    font["post"].italicAngle = -12.0
    font["hhea"].caretSlopeRun = 213
    assert traits(font).slope == "upright"
