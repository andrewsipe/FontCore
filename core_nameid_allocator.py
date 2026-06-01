#!/usr/bin/env python3
"""
NameID audit and allocation for variable-font STAT/fvar table editing.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from fontTools.ttLib import TTFont

from FontCore.core_logging_config import get_logger
from FontCore.core_ot_label_scanner import OTLabelRecord

logger = get_logger(__name__)


@dataclass
class AxisValueDef:
    """A single user-defined named position on one axis."""

    value: float
    name: str
    elidable: bool
    stat_format: int = 1
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    linked_value: Optional[float] = None


@dataclass
class AxisDef:
    """All user-defined named values for one axis."""

    tag: str
    display_name: str
    min_value: float
    default_value: float
    max_value: float
    values: List[AxisValueDef]
    stat_format_override: int = 1


@dataclass
class NameIDPlan:
    """Complete nameID allocation plan (no font writes)."""

    protected: Dict[int, str]
    axis_value_ids: Dict[Tuple[str, float], int]
    instance_ids: Dict[str, int]
    free_start: int
    free_end: int


def audit_nameids(font: TTFont, ot_labels: List[OTLabelRecord]) -> Dict[int, str]:
    """Map each nameID >= 256 in use to a human-readable reference description."""
    used: Dict[int, str] = {}

    if "fvar" in font:
        for axis in font["fvar"].axes:
            nid = axis.axisNameID
            if nid >= 256:
                used[nid] = f"fvar axis [{axis.axisTag}] AxisNameID"

        for i, inst in enumerate(font["fvar"].instances):
            nid = inst.subfamilyNameID
            if nid >= 256:
                used[nid] = f"fvar instance subfamilyNameID (index {i})"
            ps_nid = getattr(inst, "postscriptNameID", 0xFFFF)
            if ps_nid not in (0xFFFF, 0, None) and ps_nid >= 256:
                used[ps_nid] = f"fvar instance postscriptNameID (index {i})"

    if "STAT" in font:
        stat = font["STAT"].table
        if hasattr(stat, "DesignAxisRecord") and stat.DesignAxisRecord:
            for ax in stat.DesignAxisRecord.Axis:
                nid = ax.AxisNameID
                if nid >= 256:
                    used[nid] = f"STAT DesignAxisRecord [{ax.AxisTag}] AxisNameID"
        if hasattr(stat, "AxisValueArray") and stat.AxisValueArray:
            for av in stat.AxisValueArray.AxisValue:
                nid = av.ValueNameID
                val = getattr(av, "Value", getattr(av, "NominalValue", "?"))
                ax_idx = getattr(av, "AxisIndex", "?")
                if nid >= 256:
                    used[nid] = f"STAT AxisValue [axis {ax_idx} = {val}] ValueNameID"
        efb = getattr(stat, "ElidedFallbackNameID", None)
        if efb and efb >= 256:
            used[efb] = "STAT ElidedFallbackNameID"

    for rec in ot_labels:
        if rec.name_id >= 256:
            suffix = f' ("{rec.string}")' if rec.string else ""
            used[rec.name_id] = f"{rec.table} {rec.feature_tag} {rec.field}{suffix}"

    all_name_ids = {nr.nameID for nr in font["name"].names if nr.nameID >= 256}
    for nid in all_name_ids:
        if nid not in used:
            string = font["name"].getDebugName(nid) or ""
            used[nid] = f'name table only (no table reference) "{string}"'

    return used


def compose_instance_name(
    axis_values: tuple,
    elided_fallback_name: str = "Regular",
) -> str:
    """Build subfamily string from one axis-value combination (product tuple)."""
    parts = [av.name for av in axis_values if not av.elidable]
    return " ".join(parts) if parts else elided_fallback_name


def enumerate_instance_names(
    axis_defs: List[AxisDef],
    elided_fallback_name: str = "Regular",
) -> List[str]:
    """Cartesian product of axis values into composed instance subfamily names."""
    if not axis_defs:
        return []

    value_lists = [ad.values for ad in axis_defs]
    names: List[str] = []
    seen: Set[str] = set()

    for combo in itertools.product(*value_lists):
        composed = compose_instance_name(combo, elided_fallback_name)
        if composed not in seen:
            seen.add(composed)
            names.append(composed)

    return names


def build_allocation_plan(
    font: TTFont,
    ot_labels: List[OTLabelRecord],
    axis_defs: List[AxisDef],
    elided_fallback_name: str = "Regular",
) -> NameIDPlan:
    """Produce nameID allocation plan without modifying the font."""
    used = audit_nameids(font, ot_labels)
    protected = dict(used)

    free_start = (max(protected.keys()) + 1) if protected else 256

    axis_value_ids: Dict[Tuple[str, float], int] = {}
    cursor = free_start

    for axis_def in axis_defs:
        for av_def in axis_def.values:
            key = (axis_def.tag, av_def.value)
            if key not in axis_value_ids:
                axis_value_ids[key] = cursor
                cursor += 1

    instance_ids: Dict[str, int] = {}
    for composed_name in enumerate_instance_names(axis_defs, elided_fallback_name):
        if composed_name not in instance_ids:
            instance_ids[composed_name] = cursor
            cursor += 1

    if cursor <= free_start:
        free_end = free_start - 1
    else:
        free_end = cursor - 1

    return NameIDPlan(
        protected=protected,
        axis_value_ids=axis_value_ids,
        instance_ids=instance_ids,
        free_start=free_start,
        free_end=free_end,
    )


def check_for_collisions(plan: NameIDPlan, font: TTFont) -> List[str]:
    """Verify planned nameIDs do not overlap protected IDs."""
    del font  # reserved for future font-aware checks
    collisions: List[str] = []
    all_planned: Dict[int, str] = {
        **{nid: name for name, nid in plan.instance_ids.items()},
        **{nid: f"{tag}={val}" for (tag, val), nid in plan.axis_value_ids.items()},
    }
    for nid, description in all_planned.items():
        if nid in plan.protected:
            collisions.append(
                f"nameID {nid} planned for '{description}' "
                f"but protected as: {plan.protected[nid]}"
            )
    return collisions


__all__ = [
    "AxisValueDef",
    "AxisDef",
    "NameIDPlan",
    "audit_nameids",
    "build_allocation_plan",
    "check_for_collisions",
    "compose_instance_name",
    "enumerate_instance_names",
]
