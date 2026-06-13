"""Tests for idempotent preserve_low_nameids_in_fvar_stat helpers."""

from __future__ import annotations

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from FontCore.core_ttx_table_io import (
    _collect_used_name_ids_ttx,
    create_private_namerecord_ttx,
    find_existing_private_name_id_ttx,
    preserve_low_nameids_in_fvar_stat_ttx,
)


def _minimal_vf_ttx_root() -> ET.Element:
    root = ET.Element("ttFont")
    name = ET.SubElement(root, "name")
    ET.SubElement(
        name,
        "namerecord",
        nameID="17",
        platformID="3",
        platEncID="1",
        langID="0x409",
    ).text = "Bold"
    ET.SubElement(
        name,
        "namerecord",
        nameID="256",
        platformID="3",
        platEncID="1",
        langID="0x409",
    ).text = "Bold"
    fvar = ET.SubElement(root, "fvar")
    inst = ET.SubElement(fvar, "NamedInstance")
    inst.set("subfamilyNameID", "17")
    return root


def test_find_existing_private_name_id_ttx_reuses_match():
    root = _minimal_vf_ttx_root()
    name_table = root.find(".//name")
    assert find_existing_private_name_id_ttx(name_table, "Bold") == 256
    assert find_existing_private_name_id_ttx(name_table, "Light") is None


def test_preserve_low_nameids_idempotent_ttx():
    root = _minimal_vf_ttx_root()
    name_table = root.find(".//name")
    assert name_table is not None

    first = preserve_low_nameids_in_fvar_stat_ttx(root, name_table, threshold=17)
    assert first > 0
    used_after_first = _collect_used_name_ids_ttx(name_table)
    assert 256 in used_after_first

    second = preserve_low_nameids_in_fvar_stat_ttx(root, name_table, threshold=17)
    assert second == 0
    assert len(_collect_used_name_ids_ttx(name_table)) == len(used_after_first)


def test_preserve_creates_then_reuses_private_id():
    root = _minimal_vf_ttx_root()
    name_table = root.find(".//name")
    assert name_table is not None
    for nr in list(name_table.findall("namerecord")):
        if nr.get("nameID") == "256":
            name_table.remove(nr)

    preserve_low_nameids_in_fvar_stat_ttx(root, name_table, threshold=17)
    created = find_existing_private_name_id_ttx(name_table, "Bold")
    assert created is not None
    assert created >= 256

    before_count = len(name_table.findall("namerecord"))
    preserve_low_nameids_in_fvar_stat_ttx(root, name_table, threshold=17)
    assert len(name_table.findall("namerecord")) == before_count
