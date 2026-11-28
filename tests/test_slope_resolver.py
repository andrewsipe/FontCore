from FontCore.core_slope_resolver import FontEvidence, family_key, filename_slope, resolve_slopes


def ev(name, **kw):
    path = f"/fonts/{name}"
    kw.setdefault("glyphs", 500)
    kw.setdefault("filename", filename_slope(path))
    return FontEvidence(path=path, key=family_key(path), **kw)


def by_name(decisions):
    return {d.path.split("/")[-1]: d for d in decisions}


def test_the_key_ignores_slope_words_and_rename_suffixes():
    assert family_key("/f/Foo-VariableItalic.ttf") == family_key("/f/Foo-VariableUpright.ttf") == family_key("/f/Foo-VariableUpright~001.ttf")
    assert family_key("/f/Foo-BoldItalic.otf") == family_key("/f/Foo-Bold.otf")
    assert family_key("/f/Foo-Italic.otf") == family_key("/f/Foo-Regular.otf")
    assert family_key("/f/Foo-Bold.otf") != family_key("/f/Foo-Regular.otf")


def test_a_family_name_that_only_looks_like_a_slope_word_is_not_one():
    assert filename_slope("/f/PonentItalienne-Regular.otf") is None
    assert filename_slope("/f/Foo-VariableItalic.ttf") == "italic"


def test_a_lone_font_is_upright_even_when_its_names_say_italic():
    d = by_name(resolve_slopes([ev("Littlebit-CustomVariableUpright.ttf", names_italic=True, bits_italic=True, lean=6.5)]))
    x = d["Littlebit-CustomVariableUpright.ttf"]
    assert x.slope == "upright" and x.role == "lone" and x.review
    assert set(x.differs) == {"bits", "names"}


def test_a_lone_font_keeps_italic_when_stat_says_so():
    assert resolve_slopes([ev("Only-VariableItalic.ttf", stat="italic", lean=9)])[0].slope == "italic"


def test_a_lone_font_keeps_italic_when_filename_flags_names_and_lean_all_agree():
    d = resolve_slopes([ev("Only-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=9)])[0]
    assert d.slope == "italic" and d.confidence == "medium"


def test_a_pair_is_split_by_which_leans_more_in_either_direction():
    d = by_name(resolve_slopes([ev("Foo-VariableUpright.ttf", lean=0.2), ev("Foo-VariableItalic.ttf", lean=12)]))
    assert d["Foo-VariableItalic.ttf"].slope == "italic" and d["Foo-VariableUpright.ttf"].slope == "upright"
    assert d["Foo-VariableItalic.ttf"].confidence == "high"
    back = by_name(resolve_slopes([ev("Bar-VariableUpright.ttf", lean=0.0), ev("Bar-VariableSlanted.ttf", lean=11)]))
    assert back["Bar-VariableSlanted.ttf"].slope == "italic"


def test_swapped_filenames_are_caught_by_the_outlines():
    d = by_name(resolve_slopes([
        ev("Foo-VariableItalic.ttf", lean=0.0, names_italic=True, bits_italic=True),
        ev("Foo-VariableUpright.ttf", lean=12.0),
    ]))
    assert d["Foo-VariableUpright.ttf"].slope == "italic"
    assert d["Foo-VariableItalic.ttf"].slope == "upright"
    assert d["Foo-VariableUpright.ttf"].review  # the filename disagrees with the outlines: look at it


def test_stat_beats_the_lean_and_a_conflict_is_flagged():
    d = by_name(resolve_slopes([ev("Foo-VariableItalic.ttf", stat="italic", lean=1.0, filename=None), ev("Foo-VariableUpright.ttf", stat="upright", lean=9.0, filename=None)]))
    assert d["Foo-VariableItalic.ttf"].slope == "italic" and d["Foo-VariableItalic.ttf"].review


def test_a_pair_that_cannot_be_separated_stays_upright_and_is_flagged():
    d = resolve_slopes([ev("Foo-VariableItalic.ttf", lean=0.5, filename=None), ev("Foo-VariableUpright.ttf", lean=1.0, filename=None)])
    assert all(x.slope == "upright" and x.review for x in d)


def test_the_filename_words_decide_a_pair_the_lean_cannot_separate():
    d = by_name(resolve_slopes([ev("Foo-VariableItalic.ttf", lean=0.0), ev("Foo-VariableUpright.ttf", lean=0.0)]))
    assert d["Foo-VariableItalic.ttf"].slope == "italic" and d["Foo-VariableItalic.ttf"].confidence == "medium"


def test_three_files_with_one_name_are_a_group_for_a_person():
    d = resolve_slopes([ev("Foo-VariableItalic.ttf", lean=9), ev("Foo-VariableUpright.ttf", lean=0), ev("Foo-VariableSlanted.ttf", lean=15)])
    assert all(x.role == "group" and x.slope == "upright" and x.review for x in d)


def test_different_glyph_sets_are_not_called_a_pair():
    d = resolve_slopes([ev("Foo-VariableItalic.ttf", lean=9, glyphs=200), ev("Foo-VariableUpright.ttf", lean=0, glyphs=800)])
    assert all(x.slope == "upright" and x.review for x in d)


def test_a_free_slope_axis_and_an_unreadable_font_take_no_part():
    d = by_name(resolve_slopes([ev("Foo-VariableUpright.ttf", free_slope=True), ev("Bad-Regular.ttf", error="boom")]))
    assert d["Foo-VariableUpright.ttf"].slope == "free"
    assert d["Bad-Regular.ttf"].slope == "unknown" and d["Bad-Regular.ttf"].review


def test_two_slanted_files_with_one_name_are_not_an_upright_and_an_italic():
    d = resolve_slopes([ev("Vast-VariableItalic.ttf", lean=16.0), ev("Vast-VariableOblique.ttf", lean=16.0)])
    assert all(x.slope == "italic" and x.review for x in d)


def test_a_lone_stat_italic_with_an_upright_filename_and_upright_outlines_is_flagged_not_trusted():
    d = resolve_slopes([ev("NaraCursive-VariableUpright.ttf", stat="italic", lean=0.0, names_italic=True, bits_italic=True)])[0]
    assert d.slope == "upright" and d.review
