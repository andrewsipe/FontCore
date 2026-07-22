"""Silent, library-friendly name-table writers.

Site-agnostic primitives for stamping Windows English (3/1/0x409) name records
into a binary font (``fontTools.ttLib.TTFont``). Unlike the FontNameID CLI
replacers, these functions emit no console output and return structured results,
so they can be reused from any tool (e.g. FontExtractor2's finalize stage).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

from FontCore.core_ttx_table_io import (
    EID_UNICODE_BMP,
    LANG_EN_US_INT,
    PID_WIN,
    deduplicate_namerecords_binary,
)


def is_blank_name_value(text: Optional[str]) -> bool:
    """True if a name-table string is missing or whitespace-only."""
    if text is None:
        return True
    return str(text).strip() == ""


@dataclass
class UpsertResult:
    """Outcome of a single name-record upsert."""

    name_id: int
    changed: bool
    created: bool
    old_value: Optional[str]


def upsert_win_en_name_binary(
    font: TTFont,
    name_id: int,
    value: str,
    *,
    empty_fields_only: bool = False,
    pid: int = PID_WIN,
    eid: int = EID_UNICODE_BMP,
    lang: int = LANG_EN_US_INT,
) -> UpsertResult:
    """
    Create or update the Windows English record for *name_id* with *value*.

    - If a matching record exists and equals *value*, nothing changes.
    - If ``empty_fields_only`` and the existing value is non-blank, it is kept.
    - Otherwise the record is updated, or created when absent.

    Duplicate Windows/English records for *name_id* are collapsed when a write
    occurs. Returns an :class:`UpsertResult`; ``changed`` is accurate (False
    when the value already matched or was preserved).
    """
    if "name" not in font:
        return UpsertResult(name_id=name_id, changed=False, created=False, old_value=None)

    name_table = font["name"]

    target = None
    for record in name_table.names:
        if (
            record.nameID == name_id
            and record.platformID == pid
            and record.platEncID == eid
            and record.langID == lang
        ):
            target = record
            break

    if target is not None:
        try:
            old_value = (
                target.toUnicode()
                if hasattr(target, "toUnicode")
                else str(target.string)
            )
        except Exception:
            old_value = str(getattr(target, "string", ""))

        if old_value == value:
            return UpsertResult(
                name_id=name_id, changed=False, created=False, old_value=old_value
            )
        if empty_fields_only and not is_blank_name_value(old_value):
            return UpsertResult(
                name_id=name_id, changed=False, created=False, old_value=old_value
            )

        target.string = value
        deduplicate_namerecords_binary(name_table, name_id, pid, eid, lang)
        return UpsertResult(
            name_id=name_id, changed=True, created=False, old_value=old_value
        )

    new_record = NameRecord()
    new_record.nameID = name_id
    new_record.platformID = pid
    new_record.platEncID = eid
    new_record.langID = lang
    new_record.string = value
    name_table.names.append(new_record)
    deduplicate_namerecords_binary(name_table, name_id, pid, eid, lang)
    return UpsertResult(name_id=name_id, changed=True, created=True, old_value=None)


def apply_name_values_binary(
    font: TTFont,
    values: Dict[int, str],
    *,
    empty_fields_only: bool = False,
) -> List[UpsertResult]:
    """Apply multiple nameID -> value writes; returns one result per entry."""
    results: List[UpsertResult] = []
    for name_id in sorted(values):
        value = values[name_id]
        if value is None:
            continue
        results.append(
            upsert_win_en_name_binary(
                font,
                name_id,
                value,
                empty_fields_only=empty_fields_only,
            )
        )
    return results
