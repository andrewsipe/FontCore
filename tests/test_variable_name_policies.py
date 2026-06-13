"""Tests for variable-font filename parsing and NameID slot builders."""

from __future__ import annotations

import pytest

from FontCore.core_name_policies import (
    build_id1_from_variable_slots,
    build_id4_from_variable_slots,
    build_id16_from_variable_slots,
    build_id17_from_variable_slots,
    is_elidable_vf_slope,
)
from FontCore.core_variable_filename_parser import (
    VariableFilenameDialect,
    filename_has_variable_marker,
    format_variable_filename,
    parse_variable_filename,
    variable_slots_from_path,
)


@pytest.mark.parametrize(
    "filename,root,optical,width,slope,bespoke,dialect",
    [
        ("Roslindale-Variable.ttf", "Roslindale", None, None, None, None, "static_aligned"),
        ("RoslindaleText-Variable.ttf", "Roslindale", "Text", None, None, None, "static_aligned"),
        (
            "RoslindaleDisplayCondensed-Variable.ttf",
            "Roslindale",
            "Display",
            "Condensed",
            None,
            None,
            "legacy_width_family",
        ),
        (
            "ReaderProCondensed-Variable.ttf",
            "Reader Pro",
            None,
            "Condensed",
            None,
            None,
            "legacy_width_family",
        ),
        (
            "ReaderPro-CondensedVariable.ttf",
            "Reader Pro",
            None,
            "Condensed",
            None,
            None,
            "static_aligned",
        ),
        (
            "FL_RareText-VariableUpright.ttf",
            "FL Rare",
            "Text",
            None,
            "Upright",
            None,
            "static_aligned",
        ),
        ("FL_Rare-VariableCursive.ttf", "FL Rare", None, None, None, "Cursive", "static_aligned"),
        ("FL_Rare-VariableItalic.ttf", "FL Rare", None, None, "Italic", None, "static_aligned"),
        (
            "29LT_Baseet-VariableSlanted.ttf",
            "29 LT Baseet",
            None,
            None,
            "Slanted",
            None,
            "static_aligned",
        ),
    ],
)
def test_parse_variable_filename_fixtures(
    filename, root, optical, width, slope, bespoke, dialect
):
    slots = parse_variable_filename(filename)
    assert slots is not None
    assert slots.root_family == root
    assert slots.optical == optical
    assert slots.width == width
    assert slots.slope == slope
    assert slots.bespoke == bespoke
    assert slots.dialect == VariableFilenameDialect(dialect)
    assert slots.is_valid


@pytest.mark.parametrize(
    "filename,id1,id4,id16,id17",
    [
        (
            "Roslindale-Variable.ttf",
            "Roslindale",
            "Roslindale Variable",
            "Roslindale Variable",
            "Regular",
        ),
        (
            "RoslindaleText-Variable.ttf",
            "Roslindale Text",
            "Roslindale Text Variable",
            "Roslindale Variable",
            "Text",
        ),
        (
            "RoslindaleDisplayCondensed-Variable.ttf",
            "Roslindale Display Condensed",
            "Roslindale Display Condensed Variable",
            "Roslindale Variable",
            "Display Condensed",
        ),
        (
            "ReaderProCondensed-Variable.ttf",
            "Reader Pro Condensed",
            "Reader Pro Condensed Variable",
            "Reader Pro Variable",
            "Condensed",
        ),
        (
            "ReaderPro-CondensedVariable.ttf",
            "Reader Pro Condensed",
            "Reader Pro Condensed Variable",
            "Reader Pro Variable",
            "Condensed",
        ),
        (
            "FL_RareText-VariableUpright.ttf",
            "FL Rare Text",
            "FL Rare Text Variable",
            "FL Rare Variable",
            "Text",
        ),
        (
            "FL_Rare-VariableCursive.ttf",
            "FL Rare",
            "FL Rare Variable Cursive",
            "FL Rare Variable",
            "Cursive",
        ),
        (
            "FL_Rare-VariableItalic.ttf",
            "FL Rare",
            "FL Rare Variable Italic",
            "FL Rare Variable",
            "Italic",
        ),
        (
            "29LT_Baseet-VariableSlanted.ttf",
            "29 LT Baseet",
            "29 LT Baseet Variable Slanted",
            "29 LT Baseet Variable",
            "Slanted",
        ),
    ],
)
def test_build_ids_from_fixtures(filename, id1, id4, id16, id17):
    slots = parse_variable_filename(filename)
    assert slots is not None
    assert build_id1_from_variable_slots(slots) == id1
    assert build_id4_from_variable_slots(slots) == id4
    assert build_id16_from_variable_slots(slots) == id16
    assert build_id17_from_variable_slots(slots) == id17


def test_legacy_and_aligned_width_normalize_same_slots():
    legacy = parse_variable_filename("ReaderProCondensed-Variable.ttf")
    aligned = parse_variable_filename("ReaderPro-CondensedVariable.ttf")
    assert legacy is not None and aligned is not None
    assert legacy.root_family == aligned.root_family
    assert legacy.width == aligned.width
    assert legacy.optical == aligned.optical
    assert build_id4_from_variable_slots(legacy) == build_id4_from_variable_slots(aligned)


def test_upright_elided_from_id4_and_id17():
    slots = parse_variable_filename("FL_RareText-VariableUpright.ttf")
    assert slots is not None
    assert slots.slope == "Upright"
    assert is_elidable_vf_slope("Upright")
    assert "Upright" not in build_id4_from_variable_slots(slots)
    assert build_id17_from_variable_slots(slots) == "Text"


def test_augure_stereo_weight_grid_invalid():
    slots = parse_variable_filename("AugureStereo-BoldVariable.ttf")
    assert slots is not None
    assert not slots.is_valid
    assert slots.width is None
    assert any("invalid" in w for w in slots.warnings)


def test_inverted_vendor_pattern():
    slots = parse_variable_filename("BrisbaneVariable-Regular.ttf")
    assert slots is not None
    assert slots.dialect == VariableFilenameDialect.INVERTED
    assert slots.root_family == "Brisbane"
    assert any("inverted" in w.lower() for w in slots.warnings)


def test_non_variable_returns_none():
    assert parse_variable_filename("Helvetica-Bold.ttf") is None


@pytest.mark.parametrize(
    "stem,expected",
    [
        ("Roslindale-Variable", True),
        ("QualionNeue-VariableItalic", True),
        ("ReaderPro-CondensedVariable", True),
        ("Helvetica-Bold", False),
        ("QualionNeue-Regular", False),
    ],
)
def test_filename_has_variable_marker(stem, expected):
    assert filename_has_variable_marker(stem) is expected


@pytest.mark.parametrize(
    "filename,expected_stem",
    [
        ("ReaderProCondensed-Variable.ttf", "ReaderPro-CondensedVariable"),
        ("ReaderPro-CondensedVariable.ttf", "ReaderPro-CondensedVariable"),
        ("FL_Rare-VariableItalic.ttf", "FLRare-VariableItalic"),
        ("RoslindaleText-Variable.ttf", "RoslindaleText-Variable"),
    ],
)
def test_format_variable_filename(filename, expected_stem):
    slots = parse_variable_filename(filename)
    assert slots is not None
    assert format_variable_filename(slots) == expected_stem


def test_variable_slots_from_path():
    slots = variable_slots_from_path("/fonts/FL_Rare-VariableItalic.otf")
    assert slots is not None
    assert slots.root_family == "FL Rare"
    assert slots.slope == "Italic"


def test_extractor_footgun_no_double_variable_suffix():
    stem = "QualionNeue-VariableItalic"
    assert filename_has_variable_marker(stem)
    if not filename_has_variable_marker(stem):
        stem = f"{stem}-Variable"
    assert stem == "QualionNeue-VariableItalic"
