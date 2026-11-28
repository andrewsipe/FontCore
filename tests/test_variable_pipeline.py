"""What the NameID replacers need from the variable engine: the house stem for ID6/ID3, the RIBBI subfamily for ID2,
and no static weight-word note on a variable font."""

from __future__ import annotations

from types import SimpleNamespace

from fontTools.ttLib import TTFont

from FontCore.core_nameid_replacer_base import (
    unknown_weight_note,
    variable_house_stem,
    variable_id2_subfamily,
)
from tests.test_variable_traits import make

ARGS = SimpleNamespace(filename_parser=True)


def save(font, tmp_path, name):
    path = tmp_path / name
    font.save(path)
    return str(path)


def test_the_house_stem_is_what_the_tables_and_the_filename_make(tmp_path):
    path = save(make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125))), tmp_path, "Probe-Variable.ttf")
    assert variable_house_stem(path) == "Probe-WidthVariableUpright"


def test_there_is_no_house_stem_for_a_static_font(tmp_path):
    assert variable_house_stem(save(make(axes=()), tmp_path, "Probe-Regular.ttf")) is None


def test_a_variable_font_gets_no_static_weight_word_note(tmp_path):
    path = save(make(), tmp_path, "Probe-VariableCut.ttf")
    assert unknown_weight_note(path, ARGS) is None


def test_id2_follows_the_tables_not_the_filename_for_an_italic_variable_font(tmp_path):
    font = make(style="Italic", italic_bits=True, stat_ital=(1, "Italic"))
    path = save(font, tmp_path, "Probe-Variable.ttf")  # the filename says nothing about italic
    assert variable_id2_subfamily(TTFont(path), path, "Regular") == "Italic"


def test_id2_is_regular_for_an_upright_variable_font_even_if_the_filename_says_italic(tmp_path):
    # the tables outvote the one filename cue: STAT and the bits say upright
    path = save(make(stat_ital=(0, "Roman")), tmp_path, "Probe-VariableItalic.ttf")
    assert variable_id2_subfamily(TTFont(path), path, "Italic") == "Regular"


def test_id2_keeps_bold_from_the_detected_subfamily(tmp_path):
    font = make(style="Italic", italic_bits=True)
    path = save(font, tmp_path, "Probe-VariableBoldItalic.ttf")
    assert variable_id2_subfamily(TTFont(path), path, "Bold Italic") == "Bold Italic"
    assert variable_id2_subfamily(TTFont(path), path, "Bold") == "Bold Italic"


def test_a_free_slope_axis_is_a_regular_id2(tmp_path):
    path = save(make(axes=(("wght", 100, 400, 900), ("slnt", -12, 0, 0))), tmp_path, "Probe-Variable.ttf")
    assert variable_id2_subfamily(TTFont(path), path, "Regular") == "Regular"


def test_a_static_font_keeps_the_detected_subfamily(tmp_path):
    path = save(make(axes=()), tmp_path, "Probe-Italic.ttf")
    assert variable_id2_subfamily(TTFont(path), path, "Italic") == "Italic"


def test_the_fvar_table_decides_whether_a_font_is_variable_even_without_stat(tmp_path):
    from FontCore.core_variable_font_detection import is_variable_font, is_variable_font_binary

    font = make()  # fvar, no STAT
    assert "STAT" not in font
    assert is_variable_font(font) and is_variable_font_binary(font)
    assert not is_variable_font_binary(font, strict=True)  # the spec-compliance question stays available


def test_the_resolver_can_be_given_the_original_filename_when_the_file_sits_under_a_temp_name(tmp_path):
    from FontCore.core_variable_filename_parser import format_variable_filename, resolve_variable_slots

    path = save(make(axes=(("wght", 100, 400, 900), ("wdth", 75, 100, 125))), tmp_path, "_tmp_0123456789ab.ttf")
    slots = resolve_variable_slots(path, name="BT_Avance-Variable.ttf")
    assert format_variable_filename(slots) == "BT_Avance-WidthVariableUpright"


# ---- the run's family-wide slope decision -------------------------------------------------------------------

def test_an_upright_decision_makes_id2_regular_and_the_stem_upright_whatever_the_stale_flags_say(tmp_path):
    from FontCore.core_nameid_replacer_base import set_slope_decisions

    path = save(make(style="Italic", italic_bits=True, id17="Italic"), tmp_path, "Probe-VariableUpright.ttf")
    try:
        assert variable_id2_subfamily(TTFont(path), path, "Italic") in ("Italic", "Regular")  # before: whatever the tables say
        set_slope_decisions({path: "upright"})
        assert variable_id2_subfamily(TTFont(path), path, "Italic") == "Regular"
        assert variable_house_stem(path) == "Probe-VariableUpright"
    finally:
        set_slope_decisions({})


def test_an_italic_decision_makes_id2_italic_for_a_font_whose_tables_say_nothing(tmp_path):
    from FontCore.core_nameid_replacer_base import set_slope_decisions

    path = save(make(), tmp_path, "Probe-VariableItalic.ttf")
    try:
        set_slope_decisions({path: "italic"})
        assert variable_id2_subfamily(TTFont(path), path, "Regular") == "Italic"
        assert "Italic" in variable_house_stem(path)
    finally:
        set_slope_decisions({})


def test_a_free_slope_axis_ignores_a_decision(tmp_path):
    from FontCore.core_nameid_replacer_base import set_slope_decisions

    path = save(make(axes=(("wght", 100, 400, 900), ("slnt", -12, 0, 0))), tmp_path, "Probe-Variable.ttf")
    try:
        set_slope_decisions({path: "italic"})
        assert variable_id2_subfamily(TTFont(path), path, "Regular") == "Regular"
    finally:
        set_slope_decisions({})


def test_resolve_run_slope_decisions_pairs_real_fonts_and_never_raises(tmp_path):
    from FontCore.core_nameid_replacer_base import resolve_run_slope_decisions

    it = save(make(style="Italic", italic_bits=True, stat_ital=(1, "Italic")), tmp_path, "Foo-VariableItalic.ttf")
    up2 = save(make(stat_ital=(0, "Roman")), tmp_path, "Foo-VariableUpright.ttf")
    decided, pairs, left = resolve_run_slope_decisions([up2, it])
    assert pairs == 1 and decided[it] == "italic" and decided[up2] == "upright"
    assert resolve_run_slope_decisions([str(tmp_path / "missing.ttf")]) == ({}, 0, 1)  # unreadable: flagged, no decision
    assert resolve_run_slope_decisions(["notes.txt"]) == ({}, 0, 0)  # not a font file: ignored
