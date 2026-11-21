"""Semi + Mono is one word (SemiMono), in the family part and in the style."""
from FontCore.core_filename_parts_parser import split_family_subfamily
from FontCore.core_font_style_dictionaries import join_style_compounds


def test_style_joins():
    assert join_style_compounds("Semi Mono Bold") == "SemiMono Bold"
    assert join_style_compounds("SemiMono Bold") == "SemiMono Bold"


def test_family_part_joins():
    assert split_family_subfamily("ABC_GaisyrSemiMono-Regular.ttf") == ("ABC Gaisyr SemiMono", "Regular")
    assert split_family_subfamily("Spot-SemiMonoBoldItalic.ttf") == ("Spot", "SemiMono Bold Italic")


def test_other_words_untouched():
    assert split_family_subfamily("Plain Mono-Regular.ttf")[0] == "Plain Mono"
