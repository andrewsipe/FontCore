#!/usr/bin/env python3
"""
Walk GSUB/GPOS FeatureParams for OpenType feature label nameIDs.

These nameIDs must not be overwritten by STAT/fvar table editing tools.
Also inventories unlabeled stylistic sets for Names-panel add-label flows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fontTools.ttLib import TTFont

from FontCore.core_logging_config import get_logger

logger = get_logger(__name__)

_RE_STYLESET = re.compile(r"^ss\d{2}$")
_RE_CHARVAR = re.compile(r"^cv\d{2}$")


@dataclass
class OTLabelRecord:
    """A nameID referenced from GSUB/GPOS FeatureParams."""

    name_id: int
    string: str
    feature_tag: str
    table: str
    field: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name_id": self.name_id,
            "string": self.string,
            "feature_tag": self.feature_tag,
            "table": self.table,
            "field": self.field,
        }


@dataclass
class OTUnlabeledFeature:
    """An ss## feature that lacks a usable primary UI label."""

    feature_tag: str
    table: str
    suggested_string: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_tag": self.feature_tag,
            "table": self.table,
            "suggested_string": self.suggested_string,
        }


def scan_ot_label_nameids(font: TTFont) -> List[OTLabelRecord]:
    """
    Walk all GSUB and GPOS features. Return every nameID found in
    FeatureParams, with enough context to display to the user.
    """
    results: List[OTLabelRecord] = []
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        try:
            feature_list = font[table_tag].table.FeatureList
            if feature_list is None:
                continue
            for rec in feature_list.FeatureRecord:
                _extract_feature(rec, table_tag, font, results)
        except AttributeError:
            logger.debug("%s has no FeatureList", table_tag)
        except Exception as e:
            logger.warning("Error scanning %s for OT labels: %s", table_tag, e)
    return results


def scan_unlabeled_stylesets(font: TTFont) -> List[OTUnlabeledFeature]:
    """
    Return ss## features that have no primary UI name (UINameID / FeatureNameID).

    A tag is unlabeled only when *every* FeatureRecord for that tag lacks params.
    OpenType often repeats ss## once per script/langsys; the first record being
    unlabeled is not enough if a sibling already carries FeatureParams.

    Character variants (cv##) are intentionally omitted from add-label inventory.
    """
    results: List[OTUnlabeledFeature] = []
    grouped: dict[tuple[str, str], list] = {}
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        try:
            feature_list = font[table_tag].table.FeatureList
            if feature_list is None:
                continue
            for rec in feature_list.FeatureRecord:
                tag = rec.FeatureTag
                if not _RE_STYLESET.match(tag):
                    continue
                grouped.setdefault((table_tag, tag), []).append(rec)
        except AttributeError:
            logger.debug("%s has no FeatureList", table_tag)
        except Exception as e:
            logger.warning("Error scanning %s for unlabeled ss: %s", table_tag, e)
    for (table_tag, tag), records in grouped.items():
        if any(_styleset_has_primary_label(rec) for rec in records):
            continue
        results.append(OTUnlabeledFeature(feature_tag=tag, table=table_tag))
    results.sort(key=lambda r: (r.table, r.feature_tag))
    return results


def analyze_ot_features(font: TTFont, *, include_suggestions: bool = True) -> Dict[str, Any]:
    """Build the Names-panel OT feature inventory payload."""
    labels = [rec.to_dict() for rec in scan_ot_label_nameids(font)]
    unlabeled = scan_unlabeled_stylesets(font)
    if include_suggestions:
        suggest = None
        try:
            from FontCore.core_ot_label_suggest import suggest_styleset_label as suggest
        except ImportError:
            try:
                from vfcommit_lib.ot_label_suggest import suggest_styleset_label as suggest
            except ImportError:
                suggest = None
        if suggest is not None:
            for item in unlabeled:
                item.suggested_string = suggest(
                    font, table=item.table, feature_tag=item.feature_tag
                )
    return {
        "ok": True,
        "ot_feature_labels": labels,
        "ot_features_unlabeled": [u.to_dict() for u in unlabeled],
    }


def analyze_ot_features_from_path(
    source_path: str,
    *,
    include_suggestions: bool = True,
) -> Dict[str, Any]:
    try:
        # Inventory needs GSUB/GPOS FeatureList; avoid lazy holes on some fonts.
        font = TTFont(source_path, lazy=False)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "ot_feature_labels": [],
            "ot_features_unlabeled": [],
        }
    try:
        return analyze_ot_features(font, include_suggestions=include_suggestions)
    finally:
        try:
            font.close()
        except Exception:
            pass


def _styleset_has_primary_label(feature_record) -> bool:
    params = getattr(feature_record.Feature, "FeatureParams", None)
    if params is None:
        return False
    for field in ("UINameID", "FeatureNameID"):
        nid = getattr(params, field, None)
        if nid is not None and int(nid) > 0:
            return True
    return False


def _extract_feature(feature_record, table_tag: str, font: TTFont, out: List[OTLabelRecord]) -> None:
    tag = feature_record.FeatureTag
    params = getattr(feature_record.Feature, "FeatureParams", None)
    if params is None:
        return

    try:
        if _RE_STYLESET.match(tag):
            # OpenType: FeatureNameID (older) or UINameID (FeatureParamsStylisticSet)
            _collect(params, "FeatureNameID", tag, table_tag, font, out)
            _collect(params, "UINameID", tag, table_tag, font, out)

        elif _RE_CHARVAR.match(tag):
            _collect(params, "LabelNameID", tag, table_tag, font, out)
            _collect(params, "TooltipTextNameID", tag, table_tag, font, out)
            _collect(params, "SampleTextNameID", tag, table_tag, font, out)
            n = getattr(params, "NumNamedParameters", 0) or 0
            first = getattr(params, "FirstParamUILabelNameID", None)
            if first is not None and n > 0:
                for offset in range(n):
                    nid = first + offset
                    out.append(
                        OTLabelRecord(
                            name_id=nid,
                            string=_resolve(font, nid),
                            feature_tag=tag,
                            table=table_tag,
                            field=f"FirstParamUILabelNameID+{offset}",
                        )
                    )

        elif tag == "size":
            nid = getattr(params, "SubFamilyID", 0) or 0
            if nid > 0:
                _collect(params, "SubFamilyID", tag, table_tag, font, out)
    except Exception as e:
        logger.warning("Skipping malformed FeatureParams for %s/%s: %s", table_tag, tag, e)


def _collect(params, field: str, feature_tag: str, table_tag: str, font: TTFont, out: List[OTLabelRecord]) -> None:
    nid = getattr(params, field, None)
    if nid is None or nid == 0:
        return
    out.append(
        OTLabelRecord(
            name_id=int(nid),
            string=_resolve(font, int(nid)),
            feature_tag=feature_tag,
            table=table_tag,
            field=field,
        )
    )


def _resolve(font: TTFont, name_id: int) -> str:
    try:
        rec = font["name"].getName(name_id, 3, 1, 0x0409)
        if rec:
            return rec.toUnicode()
    except Exception:
        pass
    return ""


def iter_feature_records(font: TTFont, table: str, feature_tag: str):
    """Yield every FeatureRecord matching table + tag (one per script/langsys)."""
    if table not in font:
        return
    try:
        feature_list = font[table].table.FeatureList
        if feature_list is None:
            return
        for rec in feature_list.FeatureRecord:
            if rec.FeatureTag == feature_tag:
                yield rec
    except Exception:
        return


def find_feature_record(font: TTFont, table: str, feature_tag: str):
    """Return the first FeatureRecord matching table + tag, or None."""
    return next(iter_feature_records(font, table, feature_tag), None)


__all__ = [
    "OTLabelRecord",
    "OTUnlabeledFeature",
    "analyze_ot_features",
    "analyze_ot_features_from_path",
    "find_feature_record",
    "iter_feature_records",
    "scan_ot_label_nameids",
    "scan_unlabeled_stylesets",
]
