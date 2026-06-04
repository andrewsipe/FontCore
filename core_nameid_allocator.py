#!/usr/bin/env python3
"""
NameID audit and allocation for variable-font STAT/fvar table editing.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from fontTools.ttLib import TTFont

from FontCore.core_logging_config import get_logger
from FontCore.core_name_policies import sanitize_postscript, strip_variable_tokens
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
    axis_name_ids: Dict[str, int] = field(default_factory=dict)
    axis_names: Dict[str, str] = field(default_factory=dict)
    instance_postscript_names: Dict[str, str] = field(default_factory=dict)
    instance_postscript_ids: Dict[str, int] = field(default_factory=dict)
    family_ps_prefix: str = ""
    elided_fallback_name: str = "Regular"
    elided_fallback_id: int = 0
    free_start: int = 256
    free_end: int = 255


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


def derive_family_ps_prefix(font: TTFont) -> str:
    """
    Prefix for fvar instance PostScript names (e.g. OnsiteVF from nameID 25).

    Prefers ID 25, then strips Variable tokens from ID 6, then typographic family.
    """
    n25 = font["name"].getDebugName(25)
    if n25 and n25.strip():
        return sanitize_postscript(n25.strip())

    n6 = font["name"].getDebugName(6)
    if n6 and n6.strip():
        base = strip_variable_tokens(n6) or n6
        for token in ("Variable", "VF"):
            if base.endswith(token):
                base = base[: -len(token)].rstrip("-_")
            if base.endswith(f"-{token}"):
                base = base[: -(len(token) + 1)].rstrip("-_")
        if base:
            return sanitize_postscript(base)

    for nid in (16, 1):
        raw = font["name"].getDebugName(nid)
        if raw and raw.strip():
            base = strip_variable_tokens(raw) or raw
            compact = sanitize_postscript(base)
            if compact:
                return compact

    return "Font"


def compose_postscript_instance_name(family_prefix: str, subfamily_name: str) -> str:
    """
    Build PostScript name for one fvar instance.

    Matches common VF patterns: FamilyPrefix-CondensedBold (no spaces in style).
    """
    prefix = sanitize_postscript(family_prefix.strip()) or "Font"
    style = sanitize_postscript(subfamily_name.strip())
    if not style or style.lower() == "regular":
        return f"{prefix}-Regular"
    return f"{prefix}-{style}"


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
    *,
    allocate_postscript_names: bool = True,
) -> NameIDPlan:
    """Produce nameID allocation plan without modifying the font."""
    used = audit_nameids(font, ot_labels)
    protected = dict(used)

    free_start = (max(protected.keys()) + 1) if protected else 256
    cursor = free_start

    # 1. Axis display names (reallocated fresh at 256+, decoupled from 2/6/17)
    axis_name_ids: Dict[str, int] = {}
    axis_names: Dict[str, str] = {}
    for axis_def in axis_defs:
        if axis_def.tag not in axis_name_ids:
            axis_name_ids[axis_def.tag] = cursor
            axis_names[axis_def.tag] = axis_def.display_name or axis_def.tag
            cursor += 1

    # 2. STAT axis value names
    axis_value_ids: Dict[Tuple[str, float], int] = {}
    for axis_def in axis_defs:
        for av_def in axis_def.values:
            key = (axis_def.tag, av_def.value)
            if key not in axis_value_ids:
                axis_value_ids[key] = cursor
                cursor += 1

    family_prefix = derive_family_ps_prefix(font) if allocate_postscript_names else ""
    instance_ids: Dict[str, int] = {}
    instance_postscript_names: Dict[str, str] = {}
    instance_postscript_ids: Dict[str, int] = {}
    ps_string_to_id: Dict[str, int] = {}

    for composed_name in enumerate_instance_names(axis_defs, elided_fallback_name):
        if composed_name not in instance_ids:
            instance_ids[composed_name] = cursor
            cursor += 1

        if not allocate_postscript_names:
            continue

        ps_name = compose_postscript_instance_name(family_prefix, composed_name)
        instance_postscript_names[composed_name] = ps_name
        if ps_name not in ps_string_to_id:
            ps_string_to_id[ps_name] = cursor
            cursor += 1
        instance_postscript_ids[composed_name] = ps_string_to_id[ps_name]

    # Elided fallback name: reuse the all-elided instance ID when present,
    # otherwise allocate a dedicated 256+ ID. Never falls back to ID 2.
    if elided_fallback_name in instance_ids:
        elided_fallback_id = instance_ids[elided_fallback_name]
    else:
        elided_fallback_id = cursor
        cursor += 1

    if cursor <= free_start:
        free_end = free_start - 1
    else:
        free_end = cursor - 1

    return NameIDPlan(
        protected=protected,
        axis_value_ids=axis_value_ids,
        instance_ids=instance_ids,
        axis_name_ids=axis_name_ids,
        axis_names=axis_names,
        instance_postscript_names=instance_postscript_names,
        instance_postscript_ids=instance_postscript_ids,
        family_ps_prefix=family_prefix,
        elided_fallback_name=elided_fallback_name,
        elided_fallback_id=elided_fallback_id,
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
        **{nid: f"axis name [{tag}]" for tag, nid in plan.axis_name_ids.items()},
    }
    for composed, nid in plan.instance_postscript_ids.items():
        ps = plan.instance_postscript_names.get(composed, "")
        all_planned[nid] = f"PS:{ps}"
    for nid, description in all_planned.items():
        if nid < 256:
            collisions.append(
                f"nameID {nid} planned for '{description}' is below 256 "
                "(variable naming must live at 256+)"
            )
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
    "compose_postscript_instance_name",
    "derive_family_ps_prefix",
    "enumerate_instance_names",
]
