"""One collector: the same rules whichever function a tool calls (DECISIONS.md, area 3)."""

import os
from pathlib import Path

import pytest

from FontCore.core_file_collector import (
    BINARY_EXTENSIONS,
    RECOGNISED_UNSUPPORTED_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    collect_font_files,
    collect_font_files_with_progress,
    iter_font_files,
)


@pytest.fixture
def tree(tmp_path):
    def touch(rel, data=b"x"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    touch("top.ttf")
    touch("UPPER.OTF")
    touch("w.woff")
    touch("w2.woff2")
    touch("sub/deep.otf")
    touch("sub/deeper/deepest.ttf")
    touch("t.ttx")
    touch("._appledouble.ttf")
    touch("__MACOSX/._junk.otf")
    touch("__MACOSX/real-looking.otf")
    touch(".hidden/h.ttf")
    touch("_archive/old.ttf")
    touch("a.ttc")
    touch("b.dfont")
    touch("c.eot")
    touch("notes.ttf.bak")
    touch("readme.txt")
    os.symlink(tmp_path / "top.ttf", tmp_path / "link.ttf")
    return tmp_path


def rel(root, files):
    return sorted(str(Path(f).relative_to(root.resolve())) for f in files)


FUNCS = [
    pytest.param(lambda paths, **kw: list(iter_font_files(paths, **kw)), id="iter"),
    pytest.param(lambda paths, **kw: collect_font_files(paths, **kw), id="collect"),
    pytest.param(lambda paths, **kw: collect_font_files_with_progress(paths, **kw), id="progress"),
]


@pytest.mark.parametrize("fn", FUNCS)
def test_not_recursive_by_default(fn, tree):
    got = rel(tree, fn([tree]))
    assert "sub/deep.otf" not in got and "top.ttf" in got and "UPPER.OTF" in got


@pytest.mark.parametrize("fn", FUNCS)
def test_recursive_finds_every_depth_and_the_same_set(fn, tree):
    got = rel(tree, fn([tree], recursive=True))
    assert "sub/deeper/deepest.ttf" in got and "_archive/old.ttf" in got  # no folder is skipped by name


@pytest.mark.parametrize("fn", FUNCS)
def test_junk_and_hidden_items_are_skipped(fn, tree):
    got = rel(tree, fn([tree], recursive=True))
    assert not [g for g in got if g.startswith((".", "__MACOSX", "._")) or "/._" in g or "/." in g]


@pytest.mark.parametrize("fn", FUNCS)
def test_include_hidden_brings_them_back(fn, tree):
    got = rel(tree, fn([tree], recursive=True, include_hidden=True))
    assert ".hidden/h.ttf" in got and "._appledouble.ttf" in got and "__MACOSX/._junk.otf" in got


@pytest.mark.parametrize("fn", FUNCS)
def test_each_real_file_once_even_through_a_symlink_or_a_repeated_input(fn, tree):
    got = fn([tree, tree], recursive=True)
    assert len(got) == len(set(got))
    assert rel(tree, got).count("top.ttf") == 1  # the link and its target are one file


@pytest.mark.parametrize("fn", FUNCS)
def test_ttx_only_when_asked(fn, tree):
    assert "t.ttx" not in rel(tree, fn([tree]))
    assert "t.ttx" in rel(tree, fn([tree], allowed_extensions=SUPPORTED_EXTENSIONS))


def test_the_extension_sets():
    assert BINARY_EXTENSIONS == {".ttf", ".otf", ".woff", ".woff2"}
    assert SUPPORTED_EXTENSIONS == BINARY_EXTENSIONS | {".ttx"}
    assert {".ttc", ".dfont", ".eot"} <= RECOGNISED_UNSUPPORTED_EXTENSIONS


@pytest.mark.parametrize("fn", FUNCS[:2])
def test_a_missing_path_is_reported(fn, tree):
    missing = []
    fn([tree / "nope", tree / "top.ttf"], on_missing=missing.append)
    assert [Path(m).name for m in missing] == ["nope"]


@pytest.mark.parametrize("fn", FUNCS[:2])
def test_recognised_but_unsupported_files_are_counted_not_returned(fn, tree):
    skipped = []
    got = fn([tree], on_unsupported=skipped.append)
    assert sorted(Path(s).name for s in skipped) == ["a.ttc", "b.dfont", "c.eot"]
    assert not [g for g in got if g.endswith((".ttc", ".dfont", ".eot"))]


def test_a_file_named_directly_is_honoured_even_if_hidden(tree):
    got = collect_font_files([tree / ".hidden" / "h.ttf"])
    assert rel(tree, got) == [".hidden/h.ttf"]


def test_a_named_folder_is_searched_even_if_its_own_name_is_hidden_or_generated(tree):
    assert rel(tree / "_archive", collect_font_files([tree / "_archive"])) == ["old.ttf"]
    assert rel(tree / ".hidden", collect_font_files([tree / ".hidden"])) == ["h.ttf"]
