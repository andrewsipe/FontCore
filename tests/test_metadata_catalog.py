"""Tests for catalog metadata reader (FontCore)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from FontCore.core_metadata_catalog import (
    CatalogError,
    CatalogIndex,
    catalog_name_values,
    family_pascal_name,
    load_catalog,
    normalize_catalog_key,
    parse_requested_ids,
    resolve_catalog_path,
    validate_catalog_document,
)

FIXTURES = Path(__file__).resolve().parents[2] / "FontNameID" / "tests" / "fixtures" / "catalog"


def _fixture(name: str) -> Path:
    return (FIXTURES / name).resolve()


def test_load_catalog_valid():
    doc = load_catalog(_fixture("blk-algo.json"))
    assert doc["family"]["slug"] == "blk-algo"


def test_catalog_name_values_extracts_all_direct_ids():
    doc = load_catalog(_fixture("blk-algo.json"))
    values = catalog_name_values(doc, [8, 9, 10])
    assert values[8] == "Black[Foundry]"
    assert values[9] == "Michel Derre & FONTYOU"
    assert values[10].startswith("Algo FY")


def test_catalog_name_values_skips_missing_designer():
    doc = load_catalog(_fixture("blk-grtsk.json"))
    values = catalog_name_values(doc, [8, 9, 10])
    assert 8 in values
    assert 9 not in values
    assert 10 in values


def test_validate_rejects_missing_schema_version():
    with pytest.raises(CatalogError, match="schema_version"):
        validate_catalog_document({"family": {"slug": "x"}, "name_table": {"8": {}}})


def test_validate_rejects_empty_name_table():
    with pytest.raises(CatalogError, match="name_table"):
        validate_catalog_document(
            {"schema_version": 1, "family": {"slug": "x"}, "name_table": {}}
        )


def test_parse_requested_ids_order():
    assert parse_requested_ids("10,8,9") == [8, 9, 10]
    assert parse_requested_ids("0,7,8,9,10") == [8, 9, 10, 0, 7]


def test_parse_requested_ids_rejects_unsupported():
    with pytest.raises(CatalogError, match="Unsupported"):
        parse_requested_ids("1,8")


def test_resolve_catalog_path_metadata_parent(tmp_path: Path):
    lib = tmp_path / "metadata"
    site = lib / "typographer"
    site.mkdir(parents=True)
    catalog = site / "blk-algo.json"
    catalog.write_text(_fixture("blk-algo.json").read_text(encoding="utf-8"))

    resolved = resolve_catalog_path("blk-algo", library_root=lib)
    assert resolved == catalog


def test_resolve_catalog_path_typographer_dir(tmp_path: Path):
    """--library-dir may point at typographer/ directly."""
    site = tmp_path / "metadata" / "typographer"
    site.mkdir(parents=True)
    catalog = site / "blk-algo.json"
    catalog.write_text(_fixture("blk-algo.json").read_text(encoding="utf-8"))

    resolved = resolve_catalog_path("blk-algo", library_root=site)
    assert resolved == catalog


def test_resolve_catalog_path_explicit_file():
    path = _fixture("blk-algo.json")
    assert resolve_catalog_path(str(path)) == path


def test_load_catalog_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CatalogError, match="Invalid JSON"):
        load_catalog(bad)


def test_family_pascal_name():
    assert family_pascal_name("Alight Slab") == "AlightSlab"
    assert normalize_catalog_key("Alight Slab") == "alightslab"


def test_catalog_index_match_filename(tmp_path: Path):
    site = tmp_path / "typographer"
    site.mkdir(parents=True)
    for slug, name in (("drt-amica", "Amica"), ("drt-alight-slab", "Alight Slab")):
        doc = json.loads(_fixture("blk-algo.json").read_text(encoding="utf-8"))
        doc["family"]["slug"] = slug
        doc["family"]["name"] = name
        doc["family"]["typographer_id"] = slug.replace("-", ":", 1)
        (site / f"{slug}.json").write_text(json.dumps(doc), encoding="utf-8")

    index = CatalogIndex.load(site)
    assert index.match_filename("Amica-Bold.woff2").slug == "drt-amica"
    assert index.match_filename("AlightSlab-Regular.woff2").slug == "drt-alight-slab"
    assert index.match_filename("GelatoFresco-Regular.woff2") is None


def test_catalog_index_match_typographer_id(tmp_path: Path):
    site = tmp_path / "typographer"
    site.mkdir(parents=True)
    doc = json.loads(_fixture("blk-algo.json").read_text(encoding="utf-8"))
    doc["family"]["slug"] = "drt-amica"
    doc["family"]["name"] = "Amica"
    doc["family"]["typographer_id"] = "drt:amica"
    (site / "drt-amica.json").write_text(json.dumps(doc), encoding="utf-8")

    index = CatalogIndex.load(site)
    assert index.match_typographer_id("drt:amica").slug == "drt-amica"
    assert index.match_typographer_id("DRT:AMICA").slug == "drt-amica"
    assert index.match_typographer_id("drt:unknown") is None
    assert index.match_typographer_id("") is None


def test_catalog_index_assign_files(tmp_path: Path):
    site = tmp_path / "typographer"
    site.mkdir(parents=True)
    doc = json.loads(_fixture("blk-algo.json").read_text(encoding="utf-8"))
    doc["family"]["slug"] = "drt-amica"
    doc["family"]["name"] = "Amica"
    (site / "drt-amica.json").write_text(json.dumps(doc), encoding="utf-8")

    index = CatalogIndex.load(site)
    grouped, unmatched = index.assign_files(
        ["Amica-Bold.woff2", "Amica-Regular.woff2", "Unknown-Regular.woff2"]
    )
    assert grouped == {"drt-amica": ["Amica-Bold.woff2", "Amica-Regular.woff2"]}
    assert unmatched == ["Unknown-Regular.woff2"]


def test_catalog_index_slug_prefix_filter(tmp_path: Path):
    site = tmp_path / "typographer"
    site.mkdir(parents=True)
    for slug, name in (("drt-amica", "Amica"), ("blk-algo", "Algo")):
        doc = json.loads(_fixture("blk-algo.json").read_text(encoding="utf-8"))
        doc["family"]["slug"] = slug
        doc["family"]["name"] = name
        (site / f"{slug}.json").write_text(json.dumps(doc), encoding="utf-8")

    index = CatalogIndex.load(site, slug_prefix="drt")
    assert len(index) == 1
    assert index.match_filename("Amica-Bold.woff2").slug == "drt-amica"
    assert index.match_filename("Algo-Regular.woff2") is None
