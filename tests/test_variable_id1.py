"""`Variable` stays in ID1 (house convention, DECISIONS.md C4). From Area 5, ID16 carries the locked design and ID4 names the slope."""

from __future__ import annotations

import pytest

from FontCore.core_name_policies import build_id1, build_id4, build_id16, keep_one_variable_token
from FontCore.core_variable_filename_parser import parse_variable_filename


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Font Variable Black", "Font Variable Black"),
        ("Font VariableItalic", "Font Variable"),
        ("Font Variable Italic", "Font Variable"),
        ("Font VariableUpright", "Font Variable"),
        ("Font Variable Roman", "Font Variable"),
        ("Font Black", "Font Black"),
        ("", None),
    ],
)
def test_keep_one_variable_token(text, expected):
    assert keep_one_variable_token(text) == expected


def test_legacy_id1_keeps_variable():
    assert build_id1("Probe", None, None, None, is_variable=True) == "Probe Variable"
    assert build_id1("Probe Variable", None, None, None, is_variable=True) == "Probe Variable"


def test_legacy_id1_from_filename_override():
    kw = dict(is_variable=True)
    assert build_id1("Font", None, None, None, variable_family_override="Font Variable Black", **kw) == "Font Variable Black"
    assert build_id1("Font", None, None, None, variable_family_override="Font VariableItalic", **kw) == "Font Variable"
    assert build_id1("Font", None, None, None, variable_family_override="Font Black", **kw) == "Font Black Variable"


@pytest.mark.parametrize(
    "filename, id1, id4, id16",
    [
        ("Probe-Variable.ttf", "Probe Variable", "Probe Variable Upright", "Probe Variable"),
        ("Probe-VariableItalic.ttf", "Probe Variable", "Probe Variable Italic", "Probe Variable"),
        ("ProbeDisplay-Variable.ttf", "Probe Display Variable", "Probe Display Variable Upright", "Probe Display Variable"),
        ("Probe-CondensedVariable.ttf", "Probe Condensed Variable", "Probe Condensed Variable Upright", "Probe Condensed Variable"),
    ],
)
def test_slots_id1_has_variable_and_id4_names_the_upright(filename, id1, id4, id16):
    slots = parse_variable_filename(filename)
    assert slots is not None
    assert build_id1("", None, None, None, variable_slots=slots) == id1
    assert build_id4("", None, None, None, variable_slots=slots) == id4
    assert build_id16("", variable_slots=slots) == id16
