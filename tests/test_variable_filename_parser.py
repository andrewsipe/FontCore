

def test_a_term_inside_a_word_is_not_peeled_off_the_family():
    from FontCore.core_variable_filename_parser import parse_variable_filename

    teletext = parse_variable_filename("Teletext-VariableUpright")
    assert (teletext.root_family, teletext.optical) == ("Teletext", None)
    mix = parse_variable_filename("ABC_ArizonaMixCompressed-Variable")
    assert (mix.root_family, mix.width) == ("ABC Arizona Mix", "Compressed")
    assert parse_variable_filename("FooText-Variable").optical == "Text"


def test_a_period_stays_where_it_is_in_a_filename():
    from FontCore.core_filename_parts_parser import format_pascal_words

    assert format_pascal_words("Lto.UnicoreLab") == "Lto.Unicore Lab"
    assert format_pascal_words("No.1") == "No.1"
    assert format_pascal_words("Version1.2") == "Version 1.2"
