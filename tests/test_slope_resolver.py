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


def test_in_a_group_of_three_the_upright_is_the_baseline_and_each_other_file_is_italic_if_it_leans_more():
    d = by_name(resolve_slopes([ev("Foo-VariableItalic.ttf", lean=9), ev("Foo-VariableUpright.ttf", lean=0), ev("Foo-VariableSlanted.ttf", lean=15)]))
    assert d["Foo-VariableUpright.ttf"].slope == "upright" and not d["Foo-VariableUpright.ttf"].review
    assert d["Foo-VariableItalic.ttf"].slope == "italic" and d["Foo-VariableSlanted.ttf"].slope == "italic"
    assert not any(x.review for x in d.values())


def test_a_cursive_that_leans_like_the_upright_is_an_upright_alternate_and_one_that_leans_is_an_italic_alternate():
    d = by_name(resolve_slopes([ev("Nara-VariableUpright.ttf", lean=0), ev("Nara-VariableItalic.ttf", lean=12), ev("Nara-VariableCursive.ttf", lean=0.4)]))
    assert d["Nara-VariableCursive.ttf"].slope == "upright" and not d["Nara-VariableCursive.ttf"].review
    d = by_name(resolve_slopes([ev("Control-VariableUpright.ttf", lean=0), ev("Control-VariableItalic.ttf", lean=12), ev("Control-VariableCursive.ttf", lean=20)]))
    assert d["Control-VariableCursive.ttf"].slope == "italic" and d["Control-VariableItalic.ttf"].slope == "italic"


def test_a_group_with_no_single_upright_or_an_unmeasurable_member_is_left_for_a_person():
    d = resolve_slopes([ev("Foo-VariableItalic.ttf", lean=9), ev("Foo-VariableOblique.ttf", lean=9), ev("Foo-VariableSlanted.ttf", lean=9)])
    assert all(x.review and x.slope == "upright" for x in d)
    d = resolve_slopes([ev("Foo-VariableUpright.ttf", lean=0), ev("Foo-VariableItalic.ttf", lean=None), ev("Foo-VariableOblique.ttf", lean=9)])
    assert all(x.review for x in d)


def test_a_group_member_named_italic_that_does_not_lean_is_flagged():
    d = by_name(resolve_slopes([ev("Foo-VariableUpright.ttf", lean=0), ev("Foo-VariableItalic.ttf", lean=0.5), ev("Foo-VariableOblique.ttf", lean=9)]))
    assert d["Foo-VariableItalic.ttf"].review


def test_different_glyph_sets_lower_the_confidence_but_do_not_block_a_clear_pair():
    d = by_name(resolve_slopes([ev("Foo-VariableItalic.ttf", lean=9, glyphs=900), ev("Foo-VariableUpright.ttf", lean=0, glyphs=1460)]))
    assert d["Foo-VariableItalic.ttf"].slope == "italic" and d["Foo-VariableItalic.ttf"].confidence == "medium"
    assert not d["Foo-VariableItalic.ttf"].review


def test_a_free_slope_axis_and_an_unreadable_font_take_no_part():
    d = by_name(resolve_slopes([ev("Foo-VariableUpright.ttf", free_slope=True), ev("Bad-Regular.ttf", error="boom")]))
    assert d["Foo-VariableUpright.ttf"].slope == "free"
    assert d["Bad-Regular.ttf"].slope == "unknown" and d["Bad-Regular.ttf"].review


def test_two_slanted_files_with_different_slope_words_are_both_italic():
    d = resolve_slopes([ev("Vast-VariableItalic.ttf", lean=16.0), ev("Vast-VariableOblique.ttf", lean=16.0)])
    assert all(x.slope == "italic" and not x.review for x in d)


def test_two_slanted_files_with_the_same_word_are_a_duplicate_for_a_person():
    d = resolve_slopes([ev("Vast-VariableItalic.ttf", lean=16.0), ev("Vast-VariableItalic~001.ttf", lean=16.0)])
    assert all(x.slope == "italic" and x.review for x in d)


def test_a_lone_stat_italic_with_an_upright_filename_and_upright_outlines_is_upright():
    d = resolve_slopes([ev("NaraCursive-VariableUpright.ttf", stat="italic", lean=0.0, names_italic=True, bits_italic=True)])[0]
    assert d.slope == "upright" and not d.review and d.confidence == "medium"


def test_a_lone_italic_named_font_is_overruled_when_it_leans_less_than_an_italic_would():
    flat = resolve_slopes([ev("A-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=0.0, stat="upright")])[0]
    assert flat.slope == "upright" and not flat.review
    shallow = resolve_slopes([ev("C-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=2.0)])[0]
    assert shallow.slope == "upright" and not shallow.review  # a script or a pattern, not an italic
    unmeasured = resolve_slopes([ev("B-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=None)])[0]
    assert unmeasured.review
    # an upright-named font that leans clearly, with italic flags, is not decided: could be a swapped Italic
    leaning = resolve_slopes([ev("D-VariableUpright.ttf", names_italic=True, bits_italic=True, lean=6.5)])[0]
    assert leaning.review


def test_a_lone_cursive_or_corsiva_that_leans_with_italic_flags_is_an_italic_alternate():
    d = resolve_slopes([ev("FL_Rare-VariableCursive.ttf", names_italic=True, bits_italic=True, lean=15.5)])[0]
    assert d.slope == "italic" and not d.review
    d = resolve_slopes([ev("AL_Sigla-VariableCorsiva.ttf", names_italic=True, lean=15.0)])[0]
    assert d.slope == "italic"


def test_a_pair_with_a_corsiva_is_split_by_the_lean():
    d = by_name(resolve_slopes([ev("AL_Sigla-VariableUpright.ttf", lean=0), ev("AL_Sigla-VariableCorsiva.ttf", lean=15)]))
    assert d["AL_Sigla-VariableCorsiva.ttf"].slope == "italic" and d["AL_Sigla-VariableUpright.ttf"].slope == "upright"


def test_your_overrides_file_settles_a_font_the_outlines_cannot(tmp_path, monkeypatch):
    from FontCore.core_slope_resolver import load_overrides

    f = tmp_path / "slope_overrides.txt"
    f.write_text("# bitmap fonts\nLittlebit*   upright\nBad line\nSomething-* sideways\n")
    monkeypatch.setenv("FONTCORE_SLOPE_OVERRIDES", str(f))
    assert load_overrides() == [("Littlebit*", "upright")]
    d = resolve_slopes([ev("LittlebitDotty-CustomVariableUpright.ttf", names_italic=True, bits_italic=True, lean=6.5)])[0]
    assert d.slope == "upright" and not d.review and d.confidence == "high"
    assert "overrides" in d.reasons[0] and set(d.differs) == {"bits", "names"}
    assert resolve_slopes([ev("Other-VariableUpright.ttf", lean=0)])[0].reasons != d.reasons


# ---- the decision settles the slope word in a variable filename ---------------------------------------------

def _saved(tmp_path, name, **kw):
    from tests.test_variable_traits import make

    font = make(**kw)
    path = tmp_path / name
    font.save(path)
    return str(path)


def test_an_upright_decision_beats_stale_italic_flags_in_the_filename_slots(tmp_path):
    from FontCore.core_variable_filename_parser import format_variable_filename, resolve_variable_slots

    path = _saved(tmp_path, "Foo-VariableItalic.ttf", style="Italic", italic_bits=True, id17="Italic")
    assert "Italic" in format_variable_filename(resolve_variable_slots(path))  # the flags alone say italic
    slots = resolve_variable_slots(path, slope_decision="upright")
    assert slots.upright and not slots.slope
    assert "Italic" not in format_variable_filename(slots)


def test_an_italic_decision_names_a_font_whose_flags_say_nothing(tmp_path):
    from FontCore.core_variable_filename_parser import format_variable_filename, resolve_variable_slots

    path = _saved(tmp_path, "Foo-VariableUpright.ttf")
    assert "Italic" not in format_variable_filename(resolve_variable_slots(path))
    assert "Italic" in format_variable_filename(resolve_variable_slots(path, slope_decision="italic"))


def test_a_designers_oblique_word_survives_an_italic_decision(tmp_path):
    from FontCore.core_variable_filename_parser import format_variable_filename, resolve_variable_slots

    path = _saved(tmp_path, "Foo-VariableOblique.ttf")
    assert "Oblique" in format_variable_filename(resolve_variable_slots(path, slope_decision="italic"))


def test_no_decision_changes_nothing(tmp_path):
    from FontCore.core_variable_filename_parser import resolve_variable_slots

    path = _saved(tmp_path, "Foo-VariableItalic.ttf", style="Italic", italic_bits=True, id17="Italic")
    assert resolve_variable_slots(path) == resolve_variable_slots(path, slope_decision=None)


def test_a_temporary_name_does_not_hide_the_real_filename():
    assert family_key("/f/tmp_0001.ttf", name="Foo-VariableItalic.ttf") == family_key("/f/Foo-VariableUpright.ttf")
    assert filename_slope("/f/tmp_0001.ttf", name="Foo-VariableItalic.ttf") == "italic"


def test_gather_evidence_reads_a_real_font_and_judges_it_by_the_given_name(tmp_path):
    from FontCore.core_slope_resolver import gather_evidence

    path = _saved(tmp_path, "tmp_0001.ttf", style="Italic", italic_bits=True, id17="Italic")
    e = gather_evidence(path, "Foo-VariableItalic.ttf")
    assert e.error is None
    assert e.filename == "italic" and e.bits_italic and e.names_italic
    assert e.key == family_key(str(tmp_path / "Foo-VariableUpright.ttf"), (("wght", 100, 900),))
    plain = gather_evidence(path)
    assert plain.error is None and plain.filename is None


def test_an_upright_decision_keeps_a_cursive_word_so_it_cannot_clash_with_the_real_upright(tmp_path):
    from FontCore.core_variable_filename_parser import format_variable_filename, resolve_variable_slots

    path = _saved(tmp_path, "Nara-VariableCursive.ttf")
    assert format_variable_filename(resolve_variable_slots(path, slope_decision="upright")).endswith("Cursive")
    assert format_variable_filename(resolve_variable_slots(path, slope_decision="italic")).endswith("Cursive")


def test_an_alternate_with_italic_flags_names_and_lean_is_italic_even_when_stat_says_upright():
    alt = resolve_slopes([ev("FL_Rare-VariableCursive.ttf", stat="upright", names_italic=True, bits_italic=True, lean=15.5)])[0]
    assert alt.slope == "italic" and not alt.review


def test_a_plain_italic_with_only_part_of_the_evidence_against_stat_is_left_for_a_person():
    plain = resolve_slopes([ev("Foo-VariableItalic.ttf", stat="upright", names_italic=True, lean=15.5)])[0]
    assert plain.review


def test_a_stored_right_lean_the_outlines_do_not_show_is_flagged_not_overruled():
    d = resolve_slopes([ev("DarkLondon-CustomVariableItalic.ttf", names_italic=True, bits_italic=True, lean=1.6, declared=-14.4)])[0]
    assert d.review and d.slope == "upright"
    assert "stores an angle" in " ".join(d.reasons)
    near = resolve_slopes([ev("ManuForma-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=2.4, declared=-5.09)])[0]
    assert near.review


def test_a_small_or_backslanted_stored_angle_does_not_hold_back_a_flat_italic_named_font():
    for declared in (-3.3, 0.0, 3.1, 24.0):
        d = resolve_slopes([ev("Foo-VariableItalic.ttf", names_italic=True, bits_italic=True, lean=0.8, declared=declared, stat="upright")])[0]
        assert d.slope == "upright" and not d.review, declared


def test_an_override_matches_the_real_filename_when_the_file_sits_under_a_temporary_name(tmp_path, monkeypatch):
    f = tmp_path / "slope_overrides.txt"
    f.write_text("Littlebit*  upright\n")
    monkeypatch.setenv("FONTCORE_SLOPE_OVERRIDES", str(f))
    e = FontEvidence(path="/fonts/_tmp_0001.ttf", key=family_key("/fonts/_tmp_0001.ttf", (), "LittlebitDotty-CustomVariableItalic.ttf"),
                     filename="italic", names_italic=True, bits_italic=True, lean=6.5, name="LittlebitDotty-CustomVariableItalic.ttf")
    assert resolve_slopes([e])[0].slope == "upright"


def test_gather_evidence_records_the_name_it_was_given(tmp_path):
    from FontCore.core_slope_resolver import gather_evidence

    path = _saved(tmp_path, "tmp_0001.ttf")
    assert gather_evidence(path, "Foo-VariableItalic.ttf").name == "Foo-VariableItalic.ttf"
    assert gather_evidence(path).name == "tmp_0001.ttf"
