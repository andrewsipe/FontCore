"""What the font's tables say about a variable font: free axes and slope (DECISIONS.md, Area 5)."""

from __future__ import annotations

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables

from FontCore.core_variable_traits import analyze_variable_traits


def make(axes=(("wght", 100, 400, 900),), *, style="Regular", italic_bits=False, oblique_bit=False,
         stat_ital=None, instances=(), weight_class=400, filename=None, id17=None):
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
            {"location": {t: d for t, lo, d, hi in axes}, "stylename": name} for name in instances
        ])
    font = fb.font
    if id17:
        font["name"].setName(id17, 17, 3, 1, 0x409)
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


@pytest.mark.parametrize("extra,word", [(("wdth", 75, 100, 125), "Width"), (("opsz", 8, 14, 144), "OpticalSize")])
def test_weight_plus_one_registered_axis_is_named(extra, word):
    assert traits(make(axes=(("wght", 100, 400, 900), extra))).axes_word == word


@pytest.mark.parametrize("extra", [("slnt", -12, 0, 0), ("ital", 0, 0, 1)])
def test_a_free_slope_axis_is_the_baseline_and_has_no_word(extra):
    t = traits(make(axes=(("wght", 100, 400, 900), extra)))
    assert t.axes_word is None and t.slope == "free"


def test_any_unregistered_axis_is_custom_however_many():
    assert traits(make(axes=(("wght", 100, 400, 900), ("GRAD", -50, 0, 100)))).axes_word == "Custom"
    many = (("wght", 100, 400, 900), ("GRAD", -50, 0, 100), ("XTRA", 0, 0, 10), ("YOPQ", 0, 0, 10))
    assert traits(make(axes=many)).axes_word == "Custom"


def test_registered_extras_come_in_a_fixed_order_then_custom():
    axes = (("wght", 100, 400, 900), ("GRAD", -50, 0, 100), ("opsz", 8, 14, 144), ("wdth", 75, 100, 125))
    t = traits(make(axes=axes))
    assert t.axes_word == "WidthOpticalSizeCustom"


def test_all_four_registered_axes_free_is_a_collection_with_no_axis_words():
    axes = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("opsz", 8, 14, 144), ("slnt", -12, 0, 0))
    t = traits(make(axes=axes))
    assert t.collection and t.axes_word is None and t.slope == "free"


def test_a_collection_with_a_custom_axis_keeps_custom():
    axes = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("opsz", 8, 14, 144), ("ital", 0, 0, 1), ("GRAD", -50, 0, 100))
    t = traits(make(axes=axes))
    assert t.collection and t.axes_word == "Custom"


def test_three_registered_axes_with_a_locked_slope_is_not_a_collection():
    axes = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("opsz", 8, 14, 144))
    t = traits(make(axes=axes))
    assert not t.collection and t.axes_word == "WidthOpticalSize"


def test_a_locked_axis_in_fvar_is_not_free():
    t = traits(make(axes=(("wght", 100, 400, 900), ("ital", 0, 0, 0))))
    assert t.free_axes == ("wght",) and t.axes_word is None


def test_no_weight_axis_is_named_by_the_same_rules_and_never_gets_a_derived_weight_word():
    t = traits(make(axes=(("wdth", 75, 100, 125),), weight_class=100))
    assert not t.weight_free and t.axes_word == "Width" and t.locked_weight is None
    assert any("weight axis" in w.lower() for w in t.warnings)


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


# ---- the designer's slope word -------------------------------------------------------------------------------

@pytest.mark.parametrize("instances,word", [(("Light Backslant", "Bold Backslant"), "Backslant"), (("Light Reclined", "Bold Reclined"), "Reclined"), (("Light Slant", "Bold Slant"), "Slant")])
def test_the_word_comes_from_the_instance_suffix_in_the_designer_s_spelling(instances, word):
    t = traits(make(style="Regular", italic_bits=True, instances=instances))
    assert t.slope == "italic" and t.slope_word == word


def test_the_instance_suffix_beats_a_different_word_in_the_names():
    t = traits(make(style="Italic", italic_bits=True, instances=("Light Oblique", "Bold Oblique")))
    assert t.slope_word == "Oblique"


def test_the_name_cue_keeps_the_designer_s_spelling_too():
    assert traits(make(style="Slant", italic_bits=True)).slope_word == "Slant"
    assert traits(make(style="Backslant", italic_bits=True)).slope_word == "Backslant"
    assert traits(make(style="Reclined", italic_bits=True)).slope_word == "Reclined"


# ---- the names never supply a weight: only the filename can state one ----------------------------------------------

WIDTH_ONLY = (("wdth", 75, 100, 125),)


@pytest.mark.parametrize("kwargs", [dict(id17="Black"), dict(style="Light"), dict(id17="Regular"), dict(instances=("Bold", "Bold")), dict(weight_class=900)])
def test_a_font_with_no_weight_axis_gets_no_weight_word_from_its_names_or_weight_class(kwargs):
    # Danfo says Regular in ID17 and looks Black: the name table is not evidence of a weight
    t = traits(make(axes=WIDTH_ONLY, **kwargs))
    assert t.locked_weight is None and not t.weight_free


def test_a_weight_less_font_says_so_in_a_warning_for_a_report():
    assert any("weight axis" in w.lower() for w in traits(make(axes=WIDTH_ONLY)).warnings)


# ---- a font with no free axes at all is static in effect -----------------------------------------------------

def test_a_font_whose_every_axis_is_locked_has_no_free_axes():
    t = traits(make(axes=(("wght", 400, 400, 400),)))
    assert t.no_free_axes and t.free_axes == ()


def test_a_font_with_a_free_axis_is_not_static_like():
    assert not traits(make()).no_free_axes


# ---- instances vote only when they positively end in a slope word -----------------------------------------------

def test_instances_that_do_not_end_in_a_slope_word_do_not_vote_upright():
    assert traits(make(instances=("Light", "Bold"))).slope_votes["instances"] is None


def test_italic_bits_and_names_win_over_upright_looking_instances_and_stat_without_a_tie():
    t = traits(make(style="Italic", italic_bits=True, stat_ital=(0, "Roman"), instances=("Light", "Bold")))
    assert t.slope == "italic" and not any("tied" in w for w in t.warnings)


def test_the_filename_slope_word_decides_the_traits_word():
    font = make(style="Italic", italic_bits=True, id17="Italic", instances=("Italic",))
    assert analyze_variable_traits(font, "QualionNeue-VariableOblique.ttf").slope_word == "Oblique"
    assert analyze_variable_traits(font, "QualionNeue-VariableItalic.ttf").slope_word == "Italic"


def test_a_font_with_every_axis_pinned_is_called_out(tmp_path):
    from FontCore.core_nameid_replacer_base import pinned_axes_note

    pinned = make(axes=(("wght", 400, 400, 400),))
    pinned.save(tmp_path / "Probe-Variable.ttf")
    assert "wght = 400" in pinned_axes_note(str(tmp_path / "Probe-Variable.ttf"))
    free = make(axes=(("wght", 100, 400, 900),))
    free.save(tmp_path / "Free-Variable.ttf")
    assert pinned_axes_note(str(tmp_path / "Free-Variable.ttf")) is None


def test_stat_and_an_upright_filename_beat_stale_italic_flags_and_names():
    font = make(style="Italic", italic_bits=True, id17="Italic", stat_ital=(0, "Roman"), instances=("Light", "Bold"))
    t = analyze_variable_traits(font, "Baudricourt-VariableUpright.ttf")
    assert t.slope == "upright" and t.slope_word is None
    assert any("Upright filename" in w for w in t.warnings)
    # without the Upright filename the earlier rule stands: the flags and names win over STAT
    assert analyze_variable_traits(font, "Baudricourt-Variable.ttf").slope == "italic"
