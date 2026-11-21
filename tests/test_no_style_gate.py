"""-fp gates in the replacer base: no hyphen means no style to read (skip with a message); a style with only
unknown words gets a note (Regular is not added next to a word that may already be the weight)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from FontCore.core_nameid_replacer_base import fp_enabled, no_style_skip_reason, unknown_weight_note


def args(fp):
    return SimpleNamespace(filename_parser=fp)


@pytest.mark.parametrize("fp, expected", [(None, False), (False, False), ("", True), (True, True), ("sample.otf", True)])
def test_fp_enabled(fp, expected):
    assert fp_enabled(args(fp)) is expected


def test_no_hyphen_is_skipped_with_a_message():
    msg = no_style_skip_reason("/fonts/Walkway Expand Bold.otf", args(""))
    assert msg and "hyphen" in msg and "filenametools regular" in msg


@pytest.mark.parametrize("path", ["/fonts/Probe-Bold.otf", "/fonts/Probe Sans-Regular.ttf"])
def test_a_hyphenated_name_is_not_skipped(path):
    assert no_style_skip_reason(path, args("")) is None


def test_a_hyphen_with_nothing_after_it_is_skipped():
    assert no_style_skip_reason("/fonts/Probe-.otf", args("")) is not None


def test_nothing_is_skipped_when_fp_is_off():
    assert no_style_skip_reason("/fonts/Walkway Expand Bold.otf", args(None)) is None
    assert no_style_skip_reason("/fonts/Walkway Expand Bold.otf", args(False)) is None


def test_unknown_weight_note_names_the_words():
    note = unknown_weight_note("/fonts/Kiwari-Air.otf", args(""))
    assert note and "Air" in note and "Regular was not added" in note
    assert unknown_weight_note("/fonts/Kiwari-Bold.otf", args("")) is None
    assert unknown_weight_note("/fonts/Kiwari-Italic.otf", args("")) is None
    assert unknown_weight_note("/fonts/Kiwari-Air.otf", args(None)) is None
