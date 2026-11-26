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
    ("Probe-Variable", "Probe Variable", "Probe Variable", "Upright", "Probe Variable Upright"),
    ("Probe-VariableItalic", "Probe Variable", "Probe Variable", "Italic", "Probe Variable Italic"),
    ("Probe-VariableOblique", "Probe Variable Oblique", "Probe Variable", "Oblique", "Probe Variable Oblique"),
    ("Probe-VariableWidth", "Probe Variable Width", "Probe Variable", "Width Upright", "Probe Variable Width Upright"),
    ("Probe-VariableOpticalSizeItalic", "Probe Variable Optical Size", "Probe Variable", "Optical Size Italic",
     "Probe Variable Optical Size Italic"),
    ("Probe-VariableSlope", "Probe Variable Slope", "Probe Variable", "Slope", "Probe Variable Slope"),
    ("Probe-Variable2Axis", "Probe Variable 2 Axis", "Probe Variable", "2 Axis", "Probe Variable 2 Axis"),
    ("Probe-Variable3AxisItalic", "Probe Variable 3 Axis", "Probe Variable", "3 Axis Italic", "Probe Variable 3 Axis Italic"),
    ("Probe-Variable4Axis", "Probe Variable 4 Axis", "Probe Variable", "4 Axis", "Probe Variable 4 Axis"),
    ("Probe-VariableBlack", "Probe Variable Black", "Probe Variable", "Black Upright", "Probe Variable Black Upright"),
    ("Probe-VariableBlackItalic", "Probe Variable Black", "Probe Variable", "Black Italic", "Probe Variable Black Italic"),
    ("Probe-VariableWidthRegular", "Probe Variable Width Regular", "Probe Variable", "Width Regular Upright",
     "Probe Variable Width Regular Upright"),
    ("ProbeDisplayCondensed-Variable", "Probe Display Condensed Variable", "Probe Display Condensed Variable", "Upright",
     "Probe Display Condensed Variable Upright"),
    ("ProbeDisplayCondensed-Variable3AxisItalic", "Probe Display Condensed Variable 3 Axis",
     "Probe Display Condensed Variable", "3 Axis Italic", "Probe Display Condensed Variable 3 Axis Italic"),
    ("RobotoFlex-Variable13Axis", "Roboto Flex Variable 13 Axis", "Roboto Flex Variable", "13 Axis",
     "Roboto Flex Variable 13 Axis"),
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
    s = parse_variable_filename("ProbeDisplayCondensed-Variable3AxisItalic.ttf")
    assert (s.root_family, s.optical, s.width, s.axes, s.weight, s.slope) == ("Probe", "Display", "Condensed", "3Axis", None, "Italic")
    s = parse_variable_filename("Probe-VariableWidthRegular.ttf")
    assert (s.axes, s.weight, s.slope) == ("Width", "Regular", None)


def test_regular_roman_and_upright_after_variable_with_no_axes_are_the_old_pairing_markers_and_vanish():
    for name in ("Probe-VariableRegular", "Probe-VariableRoman", "Probe-VariableUpright", "Probe-VariableNormal"):
        s = parse_variable_filename(name + ".ttf")
        assert s.weight is None and s.slope is None, name
        assert format_variable_filename(s) == "Probe-Variable"


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


def test_the_tables_name_the_axes_the_filename_left_out(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(axes=FOUR), tmp_path, "Probe-Variable.ttf"))
    assert slots.axes == "4Axis" and slots.upright is False
    assert build_id17_from_variable_slots(slots) == "4 Axis"
    assert build_id1_from_variable_slots(slots) == "Probe Variable 4 Axis"


def test_the_tables_overrule_a_wrong_axis_count_in_the_filename(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "Probe-Variable4Axis.ttf"))
    assert slots.axes is None
    assert format_variable_filename(slots) == "Probe-Variable"


def test_a_variable_font_with_no_marker_in_its_filename_is_still_variable(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125))), tmp_path, "Probe-Regular.ttf"))
    assert slots is not None and slots.axes == "Width"
    assert format_variable_filename(slots) == "Probe-VariableWidth"


def test_a_static_font_named_variable_is_not_treated_as_variable(tmp_path):
    assert resolve_variable_slots_for_replacer(_save(make(axes=()), tmp_path, "Probe-Variable.ttf")) is None


def test_an_italic_file_gets_its_slope_from_the_tables_not_the_filename(tmp_path):
    font = make(style="Italic", italic_bits=True, stat_ital=(1, "Italic"))
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert slots.slope == "Italic" and slots.upright is False
    assert format_variable_filename(slots) == "Probe-VariableItalic"


def test_a_locked_weight_without_a_weight_axis_comes_from_the_weight_class(tmp_path):
    font = make(axes=(("wdth", 75, 100, 125),), weight_class=900)
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "Probe-Variable.ttf"))
    assert format_variable_filename(slots) == "Probe-VariableWidthBlack"
    assert any("usWeightClass" in w for w in slots.warnings)


def test_the_locked_design_stays_in_the_family_part(tmp_path):
    font = make(axes=(("wght", 100, 400, 900), ("GRAD", -50, 0, 100), ("XTRA", 0, 0, 10)), style="Italic", italic_bits=True)
    slots = resolve_variable_slots_for_replacer(_save(font, tmp_path, "ProbeDisplayCondensed-Variable.ttf"))
    assert format_variable_filename(slots) == "ProbeDisplayCondensed-Variable3AxisItalic"
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
        ("FL_RareText-VariableUpright", "FL_RareText-Variable"),
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
    assert format_variable_filename(slots) == "00_Quatorze-Variable4Axis"
    assert build_id16_from_variable_slots(slots) == "00 Quatorze Variable"


def test_a_filename_with_no_marker_keeps_its_family_text_too(tmp_path):
    slots = resolve_variable_slots_for_replacer(_save(make(), tmp_path, "BT_Avance-Regular.ttf"))
    assert format_variable_filename(slots) == "BT_Avance-Variable"
