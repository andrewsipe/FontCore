#!/usr/bin/env python3
"""Survey the variable fonts in a folder: one table row per font. Read-only; writes only the CSV you name.

Collected per font:
  fvar   axes (free = min < max; locked-in-fvar = min == max) and the instance COUNT (no instance names)
  STAT   design axes with their names (friendly or just the tag?); STAT axes that are not in fvar (assumed locked),
         with the value and label each locked axis carries
  name   IDs 1, 2, 4, 6, 16, 17
  OS/2   usWeightClass, usWidthClass, fsSelection (hex and bits);  head.macStyle
  angle  post.italicAngle and, for CFF/CFF2, the TopDict ItalicAngle
The words Variable, VF, VAR, GX, GF and Flex are stripped from names and the filename: they add noise for this
survey. ``markers`` says which were stripped.

Usage:  python survey_variable_fonts.py FOLDER OUT.csv [--jobs N]
The CSV holds library names: keep it out of git.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from multiprocessing import Pool

from fontTools.ttLib import TTFont

# ---- marker stripping ----------------------------------------------------------------------------------------

_MARKER_WORDS = ("Variable", "VF", "VAR", "Var", "GX", "GF", "Flex")
_WHOLE = re.compile(r"(?i)variable")
_TOKEN_EDGE = re.compile(r"^(?:VF|VAR|Var|GX|GF|Flex)(?=[A-Z0-9]|$)|(?<=[a-z0-9])(?:VF|VAR|Var|GX|GF|Flex)$")


def strip_markers(text: str) -> tuple[str, str]:
    """(text without the marker words, the markers that were removed, joined by '+')."""
    found: list[str] = []

    def drop_variable(m):
        found.append("Variable")
        return ""

    text = _WHOLE.sub(drop_variable, text or "")
    out = []
    for token in re.split(r"([ _\-]+)", text):
        if re.fullmatch(r"[ _\-]+", token or ""):
            out.append(token)
            continue
        while True:
            m = _TOKEN_EDGE.search(token)
            if not m:
                break
            found.append(m.group(0))
            token = token[: m.start()] + token[m.end():]
        out.append(token)
    cleaned = re.sub(r"\s{2,}", " ", "".join(out)).strip(" -_")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned, "+".join(found)


# ---- table readers -------------------------------------------------------------------------------------------

def name(font, nid: int) -> str:
    try:
        return font["name"].getDebugName(nid) or ""
    except Exception:
        return ""


def friendly(tag: str, label: str) -> bool:
    """A STAT axis name is friendly when it is not just the tag (case aside) and is more than 4 characters or has spaces."""
    if not label or label.lower() == tag.lower():
        return False
    return len(label) > 4 or " " in label or label[:1].isupper() and label[1:].islower()


def stat_info(font):
    """(axes [(tag, label, ordering)], values {tag: [(value, label)]}, error)"""
    if "STAT" not in font:
        return [], {}, "no_STAT"
    try:
        stat = font["STAT"].table
        axes = []
        for rec in (stat.DesignAxisRecord.Axis if stat.DesignAxisRecord else []):
            axes.append((rec.AxisTag, name(font, rec.AxisNameID), rec.AxisOrdering))
        values: dict = {}
        for av in (stat.AxisValueArray.AxisValue if stat.AxisValueArray else []):
            label = name(font, av.ValueNameID)
            if av.Format in (1, 3):
                pairs = [(av.AxisIndex, av.Value)]
            elif av.Format == 2:
                pairs = [(av.AxisIndex, av.NominalValue)]
            elif av.Format == 4:
                pairs = [(r.AxisIndex, r.Value) for r in av.AxisValueRecord]
            else:
                pairs = []
            for idx, val in pairs:
                if idx < len(axes):
                    values.setdefault(axes[idx][0], []).append((val, label))
        return axes, values, ""
    except Exception as exc:  # noqa: BLE001
        return [], {}, f"STAT_error:{type(exc).__name__}"


def num(x) -> str:
    x = float(x)
    return str(int(x)) if x == int(x) else f"{x:g}"


def survey(path: str):
    try:
        font = TTFont(path, lazy=True, fontNumber=0, recalcTimestamp=False)
        if "fvar" not in font:
            return ("static", None)
        row: dict = {}
        fvar = font["fvar"]
        free, locked, every = [], [], []
        for ax in fvar.axes:
            every.append(ax.axisTag)
            if ax.minValue < ax.maxValue:
                free.append(f"{ax.axisTag}:{num(ax.minValue)}-{num(ax.defaultValue)}-{num(ax.maxValue)}")
            else:
                locked.append(f"{ax.axisTag}={num(ax.defaultValue)}")
        free_tags = [f.split(":")[0] for f in free]
        row["fvar_axes"] = len(every)
        row["free_axes"] = " ".join(free)
        row["n_free"] = len(free)
        row["fvar_locked"] = " ".join(locked)
        row["instances"] = len(fvar.instances)

        axes, values, stat_err = stat_info(font)
        row["stat_error"] = stat_err
        row["stat_axes"] = " ".join(f"{t}:{lbl}" for t, lbl, _ in axes)
        row["stat_friendly"] = f"{sum(friendly(t, l) for t, l, _ in axes)}/{len(axes)}" if axes else ""
        only = [t for t, _, _ in axes if t not in every]
        row["n_stat_only"] = len(only)
        parts = []
        for tag in only:
            vals = values.get(tag, [])
            shown = ", ".join(f"{num(v)}({l})" if l else num(v) for v, l in vals[:4])
            parts.append(f"{tag}={shown}" + (f" +{len(vals) - 4}" if len(vals) > 4 else ""))
        row["stat_locked"] = "; ".join(parts)
        row["fvar_not_in_stat"] = " ".join(t for t in every if axes and t not in [a[0] for a in axes])  # fvar axes STAT lacks

        for nid in (1, 2, 4, 6, 16, 17):
            row[f"id{nid}"], _ = strip_markers(name(font, nid))
        os2 = font["OS/2"] if "OS/2" in font else None
        sel = os2.fsSelection if os2 else 0
        row["usWeightClass"] = os2.usWeightClass if os2 else ""
        row["usWidthClass"] = os2.usWidthClass if os2 else ""
        row["fsSelection"] = f"0x{sel:04x}"
        row["fsSel_flags"] = "".join(c for c, bit in (("I", 0), ("B", 5), ("R", 6), ("O", 9)) if sel & (1 << bit))
        row["macStyle"] = font["head"].macStyle if "head" in font else ""
        row["post_italicAngle"] = round(font["post"].italicAngle, 2) if "post" in font else ""
        cff_angle = ""
        for tag in ("CFF ", "CFF2"):
            if tag in font:
                try:
                    top = font[tag].cff.topDictIndex[0]
                    cff_angle = getattr(top, "ItalicAngle", 0) or 0
                except Exception:
                    cff_angle = "err"
        row["cff_italicAngle"] = cff_angle
        row["outlines"] = "CFF2" if "CFF2" in font else ("CFF" if "CFF " in font else "glyf")
        base = os.path.splitext(os.path.basename(path))[0]
        row["file_stem"], row["markers"] = strip_markers(base)
        row["ext"] = os.path.splitext(path)[1].lower().lstrip(".")
        font.close()
        return ("variable", row)
    except Exception as exc:  # noqa: BLE001
        return ("error", f"{type(exc).__name__}: {exc}"[:120])


COLUMNS = [
    "file_stem", "ext", "outlines", "markers",
    "fvar_axes", "n_free", "free_axes", "fvar_locked", "instances",
    "stat_axes", "stat_friendly", "n_stat_only", "stat_locked", "fvar_not_in_stat", "stat_error",
    "id1", "id2", "id4", "id6", "id16", "id17",
    "usWeightClass", "usWidthClass", "fsSelection", "fsSel_flags", "macStyle", "post_italicAngle", "cff_italicAngle",
]


def walk(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".")]
        for f in sorted(fn):
            if not f.startswith(".") and f.lower().endswith((".ttf", ".otf")):
                yield os.path.join(dp, f)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)
    counts = {"static": 0, "variable": 0, "error": 0}
    errors: dict = {}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh, Pool(args.jobs) as pool:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for i, (kind, row) in enumerate(pool.imap(survey, walk(args.folder), chunksize=100), 1):
            counts[kind] += 1
            if kind == "variable":
                writer.writerow(row)
            elif kind == "error":
                errors[row] = errors.get(row, 0) + 1
            if i % 25000 == 0:
                print(f"  {i} files, {counts['variable']} variable", file=sys.stderr, flush=True)
    print(f"{counts['variable']} variable fonts of {sum(counts.values())} files ({counts['error']} unreadable) -> {args.out}")
    for msg, n in sorted(errors.items(), key=lambda kv: -kv[1])[:5]:
        print(f"  {n}  {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
