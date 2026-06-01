#!/usr/bin/env python3
"""
Walk GSUB/GPOS FeatureParams for OpenType feature label nameIDs.

These nameIDs must not be overwritten by STAT/fvar table editing tools.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

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


__all__ = ["OTLabelRecord", "scan_ot_label_nameids"]
