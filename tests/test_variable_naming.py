"""Variable-font filenames and IDs (DECISIONS.md, Area 5, third form).

Family{Optical}{Width}{Variant}{Weight}-{FreeExtras}Variable{Slope}: what is fixed is the family, what varies is the tail.
"""

from __future__ import annotations

import pytest

from FontCore.core_name_policies import (
    build_id1_from_variable_slots,
    build_id4_from_variable_slots,
    build_id16_from_variable_slots,
    build_id17_from_variable_slots,
)
from FontCore.core_variable_filename_parser import format_variable_filename, parse_variable_filename
from tests.test_variable_traits import make

# filename stem -> (ID1, ID16, ID17, ID4)   (ID2 follows the existing ID2 rule)
TABLE = [
    ("Probe-Variable", "Probe Variable", "Probe Variable", "Upright Italic", "Probe Variable Upright Italic"),
    ("Probe-VariableUpright", "Probe Variable", "Probe Variable", "Upright", "Probe Variable Upright"),
    ("Probe-VariableItalic", "Probe Variable", "Probe Variable", "Italic", "Probe Variable Italic"),
    ("Probe-VariableOblique", "Probe Variable Oblique", "Probe Variable", "Oblique", "Probe Variable Oblique"),
    ("Probe-VariableBackslant", "Probe Variable Backslant", "Probe Variable", "Backslant", "Probe Variable Backslant"),
    ("Probe-WidthVariable", "Probe Variable Width", "Probe Variable", "Width Upright Italic", "Probe Variable Width Upright Italic"),
    ("Probe-WidthVariableUpright", "Probe Variable Width", "Probe Variable", "Width Upright", "Probe Variable Width Upright"),
    ("Probe-WidthVariableItalic", "Probe Variable Width", "Probe Variable", "Width Italic", "Probe Variable Width Italic"),
    ("Probe-OpticalSizeVariableItalic", "Probe Variable Optical Size", "Probe Variable", "Optical Size Italic",
     "Probe Variable Optical Size Italic"),
    ("Probe-WidthOpticalSizeVariableUpright", "Probe Variable Width Optical Size", "Probe Variable",
     "Width Optical Size Upright", "Probe Variable Width Optical Size Upright"),
    ("Probe-CustomVariable", "Probe Variable Custom", "Probe Variable", "Custom Upright Italic", "Probe Variable Custom Upright Italic"),
    ("Probe-CustomVariableUpright", "Probe Variable Custom", "Probe Variable", "Custom Upright", "Probe Variable Custom Upright"),
    ("Probe-WidthCustomVariableItalic", "Probe Variable Width Custom", "Probe Variable", "Width Custom Italic",
     "Probe Variable Width Custom Italic"),
    ("ProbeDisplayCondensed-Variable", "Probe Display Condensed Variable", "Probe Display Condensed Variable", "Upright Italic",
     "Probe Display Condensed Variable Upright Italic"),
    ("ProbeDisplayCondensed-VariableItalic", "Probe Display Condensed Variable", "Probe Display Condensed Variable", "Italic",
     "Probe Display Condensed Variable Italic"),
    ("ProbeCollection-Variable", "Probe Collection Variable", "Probe Collection Variable", "Upright Italic",
     "Probe Collection Variable Upright Italic"),
    ("AugureStereoLight-WidthVariable", "Augure Stereo Light Variable Width", "Augure Stereo Light Variable", "Width Upright Italic",
     "Augure Stereo Light Variable Width Upright Italic"),
    ("AugureStereoLight-WidthVariableUpright", "Augure Stereo Light Variable Width", "Augure Stereo Light Variable", "Width Upright",
     "Augure Stereo Light Variable Width Upright"),
    ("RobotoFlex-CustomVariable", "Roboto Flex Variable Custom", "Roboto Flex Variable", "Custom Upright Italic",
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
    assert format_variable_filename(parse_variable_filename(stem + ".ttf")) == stem


def test_the_slots():
    s = parse_variable_filename("ProbeDisplayCondensed-WidthCustomVariableItalic.ttf")
    assert (s.root_family, s.optical, s.width, s.axes, s.slope) == ("Probe", "Display", "Condensed", "WidthCustom", "Italic")
    s = parse_variable_filename("Probe-WidthVariableUpright.ttf")
    assert (s.axes, s.upright, s.slope_free) == ("Width", True, False)


def test_a_bare_variable_is_a_free_slope_and_a_slope_word_or_upright_is_a_fixed_one():
    assert parse_variable_filename("Probe-Variable.ttf").slope_free is True
    assert parse_variable_filename("Probe-VariableUpright.ttf").upright is True
    s = parse_variable_filename("Probe-VariableItalic.ttf")
    assert s.slope == "Italic" and s.slope_free is False


def test_the_designer_s_slope_spelling_is_kept():
    for word in ("Slant", "Slanted", "Backslant", "Backslanted", "Reclined", "Oblique", "Reverse", "Cursive", "Rotalic", "Tiltalic", "Corsiva"):
        assert parse_variable_filename(f"Probe-Variable{word}.ttf").slope == word


# ---- older forms are read and rewritten ------------------------------------------------------------------------

@pytest.mark.parametrize(
    "old, new",
    [
        ("Probe-VariableWidth", "Probe-WidthVariable"),
        ("Probe-VariableWidthItalic", "Probe-WidthVariableItalic"),
        ("Probe-VariableOpticalSizeUpright", "Probe-OpticalSizeVariableUpright"),
        ("Probe-VariableCustomUpright", "Probe-CustomVariableUpright"),
        ("Probe-VariableBlack", "ProbeBlack-Variable"),
        ("Probe-VariableBlackItalic", "ProbeBlack-VariableItalic"),
        ("Probe-VariableSlope", "Probe-Variable"),
        ("Probe-Variable3AxisItalic", "Probe-VariableItalic"),
        ("Probe-Variable2Axis", "Probe-Variable"),
        ("Probe-Variable4Axes", "Probe-Variable"),
        ("Probe-VariableRegular", "ProbeRegular-Variable"),
        ("Probe-VariableNormal", "Probe-Variable"),
        ("Probe-VariableRoman", "Probe-VariableUpright"),
        ("ReaderPro-CondensedVariable", "ReaderProCondensed-Variable"),
        ("Probe-VF", "Probe-Variable"),
        ("Probe-Var", "Probe-Variable"),
    ],
)
def test_older_forms_are_rewritten_to_the_third_form(old, new):
    assert format_variable_filename(parse_variable_filename(old + ".ttf")) == new


def test_a_weight_before_variable_is_still_invalid():
    assert not parse_variable_filename("Probe-BoldVariable.ttf").is_valid


# ---- the family part is kept as written; variants belong to it -------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("BT_Avance-Variable", "BT_Avance-Variable"),
        ("00_Quatorze-Variable", "00_Quatorze-Variable"),
        ("OCR_010204-Variable", "OCR_010204-Variable"),
        ("FutterGrotesk_UT-VariableItalic", "FutterGrotesk_UT-VariableItalic"),
        ("BT_Avance-CondensedVariable", "BT_AvanceCondensed-Variable"),
        ("Probe Two-Variable", "ProbeTwo-Variable"),
        ("Probe-VariableAlt", "ProbeAlt-Variable"),
        ("Probe-VariableCutItalic", "ProbeCut-VariableItalic"),
        ("ProbeDisplay-VariableAltUpright", "ProbeDisplayAlt-VariableUpright"),
        ("Probe-VariableWidthSwashItalic", "ProbeSwash-WidthVariableItalic"),
        ("ProbeAlt-Variable", "ProbeAlt-Variable"),
    ],
)
def test_the_family_part_keeps_its_text_and_takes_variants(name, expected):
    assert format_variable_filename(parse_variable_filename(name + ".ttf")) == expected


def test_the_variant_is_in_the_family_ids_not_the_style_ids():
    slots = parse_variable_filename("Probe-VariableCutItalic.ttf")
    assert build_id16_from_variable_slots(slots) == "Probe Cut Variable"
    assert build_id1_from_variable_slots(slots) == "Probe Cut Variable"
    assert build_id17_from_variable_slots(slots) == "Italic"
    assert build_id4_from_variable_slots(slots) == "Probe Cut Variable Italic"


# ---- the font's tables decide what the filename cannot -------------------------------------------------------

FOUR = (("wght", 100, 400, 900), ("wdth", 75, 100, 125), ("opsz", 8, 14, 144), ("slnt", -12, 0, 0))
WIDTH_ONLY = (("wdth", 75, 100, 125),)


def resolve(font, tmp_path, name):
    from FontCore.core_nameid_replacer_base import resolve_variable_slots_for_replacer

    path = tmp_path / name
    font.save(path)
    return resolve_variable_slots_for_replacer(str(path))


def stem(slots):
    return format_variable_filename(slots)


def test_four_registered_axes_make_a_collection_family(tmp_path):
    slots = resolve(make(axes=FOUR), tmp_path, "Probe-Variable.ttf")
    assert stem(slots) == "ProbeCollection-Variable"
    assert build_id16_from_variable_slots(slots) == "Probe Collection Variable"
    assert build_id17_from_variable_slots(slots) == "Upright Italic"


def test_the_tables_name_the_free_extras_the_filename_left_out(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125)))
    slots = resolve(font, tmp_path, "Probe-Variable.ttf")
    assert stem(slots) == "Probe-WidthVariableUpright"
    assert build_id17_from_variable_slots(slots) == "Width Upright"


def test_a_free_slope_axis_writes_no_slope_word(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("slnt", -12, 0, 0)))
    slots = resolve(font, tmp_path, "Probe-VariableItalic.ttf")
    assert stem(slots) == "Probe-Variable"
    assert build_id17_from_variable_slots(slots) == "Upright Italic"


def test_the_tables_overrule_a_wrong_axes_word_in_the_filename(tmp_path):
    assert stem(resolve(make(), tmp_path, "Probe-WidthVariable.ttf")) == "Probe-VariableUpright"


def test_a_variable_font_with_no_marker_in_its_filename_is_still_variable(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125)))
    assert stem(resolve(font, tmp_path, "Probe-Regular.ttf")) == "Probe-WidthVariableUpright"


def test_a_static_font_named_variable_is_not_treated_as_variable(tmp_path):
    assert resolve(make(axes=()), tmp_path, "Probe-Variable.ttf") is None


def test_a_font_with_no_free_axes_is_named_as_a_static_font(tmp_path):
    assert resolve(make(axes=(("wght", 400, 400, 400),)), tmp_path, "Probe-Regular.ttf") is None


def test_an_italic_file_gets_its_slope_from_the_tables_not_the_filename(tmp_path):
    font = make(style="Italic", italic_bits=True, stat_ital=(1, "Italic"))
    slots = resolve(font, tmp_path, "Probe-Variable.ttf")
    assert slots.slope == "Italic" and not slots.upright and slots.slope_free is False
    assert stem(slots) == "Probe-VariableItalic"


def test_the_designer_s_slope_word_survives_into_the_filename(tmp_path):
    font = make(style="Regular", italic_bits=True, instances=("Light Backslant", "Bold Backslant"))
    assert stem(resolve(font, tmp_path, "Probe-Variable.ttf")) == "Probe-VariableBackslant"


# ---- fonts with no weight axis: only a weight the filename states is written, in the family ---------------------

def test_a_weight_the_filename_states_goes_in_the_family(tmp_path):
    font = make(axes=(("wdth", 75, 100, 125), ("slnt", -12, 0, 0)))
    slots = resolve(font, tmp_path, "AugureStereo-VariableLight.ttf")
    assert stem(slots) == "AugureStereoLight-WidthVariable"
    assert build_id16_from_variable_slots(slots) == "Augure Stereo Light Variable"
    assert build_id17_from_variable_slots(slots) == "Width Upright Italic"


def test_a_locked_regular_the_filename_states_is_written(tmp_path):
    font = make(axes=WIDTH_ONLY)
    slots = resolve(font, tmp_path, "AugureStereo-VariableRegular.ttf")
    assert stem(slots) == "AugureStereoRegular-WidthVariableUpright"
    assert build_id16_from_variable_slots(slots) == "Augure Stereo Regular Variable"
    free = resolve(make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125))), tmp_path, "AugureStereo-Variable.ttf")
    assert stem(free) == "AugureStereo-WidthVariableUpright"  # a free weight stays unmarked: the two differ


def test_a_weight_in_a_plain_filename_counts_when_the_font_has_no_weight_axis(tmp_path):
    font = make(axes=(("GRAD", -50, 0, 100),), style="Italic", italic_bits=True)
    assert stem(resolve(font, tmp_path, "Lacano-Regular.ttf")) == "LacanoRegular-CustomVariableItalic"


def test_a_weight_in_a_plain_filename_is_ignored_when_the_font_has_a_free_weight_axis(tmp_path):
    assert stem(resolve(make(), tmp_path, "Lacano-Regular.ttf")) == "Lacano-VariableUpright"


def test_a_weight_less_font_with_no_weight_in_its_filename_gets_none_and_no_placeholder(tmp_path):
    # Danfo: custom axis only, ID17 says Regular, usWeightClass says 100, and the font looks Black: none of that is used
    font = make(axes=(("DCAY", 0, 0, 900),), style="Regular", id17="Regular", weight_class=100)
    slots = resolve(font, tmp_path, "Danfo-Variable.ttf")
    assert stem(slots) == "Danfo-CustomVariableUpright"
    assert build_id16_from_variable_slots(slots) == "Danfo Variable"


def test_a_slope_only_font_with_no_weight_word_is_plain_variable(tmp_path):
    font = make(axes=(("slnt", -12, 0, 0),), style="Regular")
    assert stem(resolve(font, tmp_path, "Probe-Variable.ttf")) == "Probe-Variable"


def test_a_weight_word_in_the_filename_is_used_when_the_font_has_no_weight_axis(tmp_path):
    font = make(axes=WIDTH_ONLY, style="Regular")
    assert stem(resolve(font, tmp_path, "Probe-VariableWidthBlack.ttf")) == "ProbeBlack-WidthVariableUpright"


def test_a_locked_weight_already_in_the_family_is_not_written_twice(tmp_path):
    assert stem(resolve(make(axes=WIDTH_ONLY), tmp_path, "AugureStereoLight-Variable.ttf")) == "AugureStereoLight-WidthVariableUpright"


def test_a_weight_word_in_the_filename_is_dropped_when_the_font_has_a_free_weight_axis(tmp_path):
    slots = resolve(make(), tmp_path, "Probe-VariableBlack.ttf")
    assert stem(slots) == "Probe-VariableUpright"
    assert any("weight" in w for w in slots.warnings)


def test_the_locked_design_stays_in_the_family_part(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("GRAD", -50, 0, 100)), style="Italic", italic_bits=True)
    slots = resolve(font, tmp_path, "ProbeDisplayCondensed-Variable.ttf")
    assert stem(slots) == "ProbeDisplayCondensed-CustomVariableItalic"
    assert build_id16_from_variable_slots(slots) == "Probe Display Condensed Variable"


def test_underscores_survive_the_font_tables_too(tmp_path):
    slots = resolve(make(axes=FOUR), tmp_path, "00_Quatorze-Variable.ttf")
    assert stem(slots) == "00_QuatorzeCollection-Variable"
    assert build_id16_from_variable_slots(slots) == "00 Quatorze Collection Variable"


def test_a_filename_with_no_marker_keeps_its_family_text_too(tmp_path):
    assert stem(resolve(make(), tmp_path, "BT_Avance-Regular.ttf")) == "BT_Avance-VariableUpright"


def test_a_variant_word_survives_the_font_tables(tmp_path):
    slots = resolve(make(), tmp_path, "Probe-VariableAlt.ttf")
    assert stem(slots) == "ProbeAlt-VariableUpright"
    assert build_id16_from_variable_slots(slots) == "Probe Alt Variable"


def test_a_missing_file_falls_back_to_the_filename_alone():
    from FontCore.core_nameid_replacer_base import resolve_variable_slots_for_replacer

    slots = resolve_variable_slots_for_replacer("/nonexistent/Probe-VariableItalic.ttf")
    assert slots is not None and slots.slope == "Italic"


# ---- copy suffixes are not design variants -----------------------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("Probe-Variable copy", "Probe-Variable"),
        ("Probe-Variable Copy 2", "Probe-Variable"),
        ("Probe-VariableItalic (2)", "Probe-VariableItalic"),
        ("Probe-Variable~001", "Probe-Variable"),
        ("Probe-Variable-copy", "Probe-Variable"),
        ("ProbeCopy-Variable", "ProbeCopy-Variable"),  # a family that really is called Copy is untouched
    ],
)
def test_copy_suffixes_are_dropped_not_made_a_variant(name, expected):
    assert format_variable_filename(parse_variable_filename(name + ".ttf")) == expected
