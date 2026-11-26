"""Variable-font filenames and IDs, one table from DECISIONS.md (Area 5)."""

from __future__ import annotations

import pytest

from FontCore.core_name_policies import (
    build_id1_from_variable_slots,
    build_id4_from_variable_slots,
    build_id16_from_variable_slots,
    build_id17_from_variable_slots,
)
from FontCore.core_variable_filename_parser import format_variable_filename, parse_variable_filename

# filename stem -> (ID1, ID16, ID17, ID4)   (ID2 follows the existing ID2 rule)
TABLE = [
    ("Probe-Variable", "Probe Variable", "Probe Variable", "Upright Italic", "Probe Variable Upright Italic"),
    ("Probe-VariableUpright", "Probe Variable", "Probe Variable", "Upright", "Probe Variable Upright"),
    ("Probe-VariableItalic", "Probe Variable", "Probe Variable", "Italic", "Probe Variable Italic"),
    ("Probe-VariableOblique", "Probe Variable Oblique", "Probe Variable", "Oblique", "Probe Variable Oblique"),
    ("Probe-VariableBackslant", "Probe Variable Backslant", "Probe Variable", "Backslant", "Probe Variable Backslant"),
    ("Probe-VariableWidth", "Probe Variable Width", "Probe Variable", "Width Upright Italic", "Probe Variable Width Upright Italic"),
    ("Probe-VariableWidthUpright", "Probe Variable Width", "Probe Variable", "Width Upright", "Probe Variable Width Upright"),
    ("Probe-VariableWidthItalic", "Probe Variable Width", "Probe Variable", "Width Italic", "Probe Variable Width Italic"),
    ("Probe-VariableOpticalSizeItalic", "Probe Variable Optical Size", "Probe Variable", "Optical Size Italic",
     "Probe Variable Optical Size Italic"),
    ("Probe-VariableWidthOpticalSizeUpright", "Probe Variable Width Optical Size", "Probe Variable",
     "Width Optical Size Upright", "Probe Variable Width Optical Size Upright"),
    ("Probe-VariableCustom", "Probe Variable Custom", "Probe Variable", "Custom Upright Italic", "Probe Variable Custom Upright Italic"),
    ("Probe-VariableCustomUpright", "Probe Variable Custom", "Probe Variable", "Custom Upright", "Probe Variable Custom Upright"),
    ("Probe-VariableWidthCustomItalic", "Probe Variable Width Custom", "Probe Variable", "Width Custom Italic",
     "Probe Variable Width Custom Italic"),
    ("Probe-VariableBlackItalic", "Probe Variable Black", "Probe Variable", "Black Italic", "Probe Variable Black Italic"),
    ("Probe-VariableWidthRegularUpright", "Probe Variable Width Regular", "Probe Variable", "Width Regular Upright",
     "Probe Variable Width Regular Upright"),
    ("ProbeDisplayCondensed-Variable", "Probe Display Condensed Variable", "Probe Display Condensed Variable", "Upright Italic",
     "Probe Display Condensed Variable Upright Italic"),
    ("ProbeDisplayCondensed-VariableItalic", "Probe Display Condensed Variable", "Probe Display Condensed Variable", "Italic",
     "Probe Display Condensed Variable Italic"),
    ("ProbeCollection-Variable", "Probe Collection Variable", "Probe Collection Variable", "Upright Italic",
     "Probe Collection Variable Upright Italic"),
    ("RobotoFlex-VariableCustom", "Roboto Flex Variable Custom", "Roboto Flex Variable", "Custom Upright Italic",
     "Roboto Flex Variable Custom Upright Italic"),
]


@pytest.mark.parametrize("stem,id1,id16,id17,id4", TABLE)
def test_the_id_table(stem, id1, id16, id17, id4):
    slots = parse_variable_filename(stem + ".ttf")
    assert slots is not None
    assert build_id1_from_variable_slots(slots) == id1
    assert build_id16_from_variable_slots(slots) == id16
    assert build_id17_from_variable_slots(slots) == id17
    assert build_id4_from_variable_slots(slots) == id4


@pytest.mark.parametrize("stem", [row[0] for row in TABLE])
def test_the_filename_round_trips(stem):
    slots = parse_variable_filename(stem + ".ttf")
    assert format_variable_filename(slots) == stem


def test_the_big_picture_slots():
    s = parse_variable_filename("ProbeDisplayCondensed-VariableCustomItalic.ttf")
    assert (s.root_family, s.optical, s.width, s.axes, s.weight, s.slope) == ("Probe", "Display", "Condensed", "Custom", None, "Italic")
    s = parse_variable_filename("Probe-VariableWidthRegularUpright.ttf")
    assert (s.axes, s.weight, s.slope, s.upright) == ("Width", "Regular", None, True)


def test_a_bare_variable_is_a_free_slope_and_a_slope_word_or_upright_is_a_fixed_one():
    assert parse_variable_filename("Probe-Variable.ttf").slope_free is True
    assert parse_variable_filename("Probe-VariableUpright.ttf").upright is True
    s = parse_variable_filename("Probe-VariableItalic.ttf")
    assert s.slope == "Italic" and s.slope_free is False


def test_the_designer_s_slope_spelling_is_kept():
    for word in ("Slant", "Slanted", "Backslant", "Backslanted", "Reclined", "Oblique", "Reverse", "Cursive"):
        assert parse_variable_filename(f"Probe-Variable{word}.ttf").slope == word


def test_the_old_slope_and_count_words_are_read_and_dropped():
    # (Regular is no longer one of the old words: see the locked-Regular tests below)
    for old, new in (("Probe-VariableSlope", "Probe-Variable"), ("Probe-Variable3AxisItalic", "Probe-VariableItalic"),
                     ("Probe-Variable2Axis", "Probe-Variable"), ("Probe-Variable4Axes", "Probe-Variable")):
        assert format_variable_filename(parse_variable_filename(old + ".ttf")) == new, old


def test_a_regular_or_normal_after_variable_is_read_as_a_weight_word():
    for name, weight in (("Probe-VariableRegular", "Regular"), ("Probe-VariableNormal", "Normal")):
        assert parse_variable_filename(name + ".ttf").weight == weight


def test_a_regular_weight_word_is_dropped_when_the_font_has_a_free_weight_axis(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "Probe-VariableRegular.ttf"))
    assert format_variable_filename(slots) == "Probe-VariableUpright"


def test_a_locked_regular_is_kept_so_it_is_not_taken_for_a_free_weight(tmp_path):
    font = make(axes=(("wdth", 75, 100, 125),))
    assert format_variable_filename(resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-VariableRegular.ttf"))) == "Probe-VariableWidthRegularUpright"
    assert format_variable_filename(resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-VariableLight.ttf"))) == "Probe-VariableWidthLightUpright"


def test_roman_and_upright_both_mean_a_fixed_upright():
    for name in ("Probe-VariableRoman", "Probe-VariableUpright"):
        assert format_variable_filename(parse_variable_filename(name + ".ttf")) == "Probe-VariableUpright"


def test_the_old_static_aligned_width_after_the_hyphen_moves_into_the_family_part():
    s = parse_variable_filename("ReaderPro-CondensedVariable.ttf")
    assert s.width == "Condensed"
    assert format_variable_filename(s) == "ReaderProCondensed-Variable"


def test_a_weight_before_variable_is_still_invalid():
    s = parse_variable_filename("Probe-BoldVariable.ttf")
    assert not s.is_valid


def test_vf_and_var_are_read_but_written_as_variable():
    for name in ("Probe-VF", "Probe-Var"):
        s = parse_variable_filename(name + ".ttf")
        assert s is not None and format_variable_filename(s) == "Probe-Variable", name


# ---- the font's tables decide what the filename cannot -------------------------------------------------------

from tests.test_variable_traits import make  # noqa: E402

from FontCore.core_nameid_replacer_base import resolve_variable_slots_for_replacer  # noqa: E402

FOUR = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("opsz", 8, 14, 144), ("slnt", -12, 0, 0))


def _save(font, tmp_path, name):
    path = tmp_path / name
    font.save(path)
    return str(path)


def test_four_registered_axes_make_a_collection_family(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(axes=FOUR), tmp_path, "Probe-Variable.ttf"))
    assert format_variable_filename(slots) == "ProbeCollection-Variable"
    assert build_id16_from_variable_slots(slots) == "Probe Collection Variable"
    assert build_id17_from_variable_slots(slots) == "Upright Italic"


def test_the_tables_name_the_extra_axes_the_filename_left_out(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125)), style="Regular")
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert slots.axes == "Width"
    assert format_variable_filename(slots) == "Probe-VariableWidthUpright"
    assert build_id17_from_variable_slots(slots) == "Width Upright"


def test_a_free_slope_axis_writes_no_slope_word(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("slnt", -12, 0, 0)))
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-VariableItalic.ttf"))
    assert format_variable_filename(slots) == "Probe-Variable"
    assert build_id17_from_variable_slots(slots) == "Upright Italic"


def test_the_tables_overrule_a_wrong_axes_word_in_the_filename(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "Probe-VariableWidth.ttf"))
    assert slots.axes is None
    assert format_variable_filename(slots) == "Probe-VariableUpright"


def test_a_variable_font_with_no_marker_in_its_filename_is_still_variable(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125))), tmp_path, "Probe-Regular.ttf"))
    assert slots is not None and slots.axes == "Width"
    assert format_variable_filename(slots) == "Probe-VariableWidthUpright"


def test_a_static_font_named_variable_is_not_treated_as_variable(tmp_path):
    assert resolve_variable_slots_for_replacer(_save(make(axes=()), tmp_path, "Probe-Variable.ttf")) is None


def test_an_italic_file_gets_its_slope_from_the_tables_not_the_filename(tmp_path):
    font = make(style="Italic", italic_bits=True, stat_ital=(1, "Italic"))
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert slots.slope == "Italic" and not slots.upright and slots.slope_free is False
    assert format_variable_filename(slots) == "Probe-VariableItalic"


def test_the_designer_s_slope_word_survives_into_the_filename(tmp_path):
    font = make(style="Regular", italic_bits=True, instances=("Light Backslant", "Bold Backslant"))
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert format_variable_filename(slots) == "Probe-VariableBackslant"


def test_a_weight_less_font_gets_no_derived_weight_word(tmp_path):
    font = make(axes=(("wdth", 75, 100, 125),), weight_class=900)
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert format_variable_filename(slots) == "Probe-VariableWidthUpright"
    assert slots.weight is None


def test_a_weight_word_in_the_filename_is_kept_only_when_the_font_has_no_weight_axis(tmp_path):
    locked = make(axes=(("wdth", 75, 100, 125),))
    assert format_variable_filename(resolve_variable_slots_for_replacer(_save(locked, tmp_path, "Probe-VariableWidthBlack.ttf"))) == "Probe-VariableWidthBlackUpright"
    free = make()
    assert format_variable_filename(resolve_variable_slots_for_replacer(_save(free, tmp_path / "x.ttf" if False else tmp_path, "Probe-VariableBlack.ttf"))) == "Probe-VariableUpright"


def test_the_locked_design_stays_in_the_family_part(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("GRAD", -50, 0, 100)), style="Italic", italic_bits=True)
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "ProbeDisplayCondensed-Variable.ttf"))
    assert format_variable_filename(slots) == "ProbeDisplayCondensed-VariableCustomItalic"
    assert build_id16_from_variable_slots(slots) == "Probe Display Condensed Variable"


def test_a_missing_file_falls_back_to_the_filename_alone():
    slots = resolve_variable_slots_for_replacer("/nonexistent/Probe-VariableItalic.ttf")
    assert slots is not None and slots.slope == "Italic"


# ---- the family part of the filename is kept as written ---------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("BT_Avance-Variable", "BT_Avance-Variable"),
        ("00_Quatorze-Variable", "00_Quatorze-Variable"),
        ("OCR_010204-Variable", "OCR_010204-Variable"),
        ("FL_RareText-VariableUpright", "FL_RareText-VariableUpright"),
        ("FutterGrotesk_UT-VariableItalic", "FutterGrotesk_UT-VariableItalic"),
        ("Workhorse_ScriptStencilCondensed-Variable", "Workhorse_ScriptStencilCondensed-Variable"),
        # a width that sat after the hyphen moves into the family part, after the family as written
        ("BT_Avance-CondensedVariable", "BT_AvanceCondensed-Variable"),
        ("Probe Two-Variable", "ProbeTwo-Variable"),  # spaces cannot stay in a house-form stem
    ],
)
def test_the_family_part_keeps_its_underscores(name, expected):
    assert format_variable_filename(parse_variable_filename(name + ".ttf")) == expected


def test_underscores_survive_the_font_tables_too(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(axes=FOUR), tmp_path, "00_Quatorze-Variable.ttf"))
    assert format_variable_filename(slots) == "00_QuatorzeCollection-Variable"
    assert build_id16_from_variable_slots(slots) == "00 Quatorze Collection Variable"


def test_a_filename_with_no_marker_keeps_its_family_text_too(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "BT_Avance-Regular.ttf"))
    assert format_variable_filename(slots) == "BT_Avance-VariableUpright"


# ---- a leftover word after Variable is a design variant: it belongs in the family part ---------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("Probe-VariableAlt", "ProbeAlt-Variable"),
        ("Probe-VariableCut", "ProbeCut-Variable"),
        ("Probe-VariableCutItalic", "ProbeCut-VariableItalic"),
        ("ProbeDisplay-VariableAltUpright", "ProbeDisplayAlt-VariableUpright"),
        ("Probe-VariableWidthSwashItalic", "ProbeSwash-VariableWidthItalic"),
        ("ProbeAlt-Variable", "ProbeAlt-Variable"),  # already in the family part: unchanged
    ],
)
def test_a_variant_word_moves_into_the_family_part(name, expected):
    assert format_variable_filename(parse_variable_filename(name + ".ttf")) == expected


def test_the_variant_is_in_the_family_ids_not_the_style_ids():
    slots = parse_variable_filename("Probe-VariableCutItalic.ttf")
    assert build_id16_from_variable_slots(slots) == "Probe Cut Variable"
    assert build_id1_from_variable_slots(slots) == "Probe Cut Variable"
    assert build_id17_from_variable_slots(slots) == "Italic"
    assert build_id4_from_variable_slots(slots) == "Probe Cut Variable Italic"


@pytest.mark.parametrize("word", ["Rotalic", "Tiltalic", "Corsiva"])
def test_these_designer_words_are_slopes_not_variants(word):
    assert parse_variable_filename(f"Probe-Variable{word}.ttf").slope == word


def test_a_variant_word_survives_the_font_tables(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "Probe-VariableAlt.ttf"))
    assert format_variable_filename(slots) == "ProbeAlt-VariableUpright"
    assert build_id16_from_variable_slots(slots) == "Probe Alt Variable"
