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
