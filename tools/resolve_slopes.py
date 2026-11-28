#!/usr/bin/env python3
"""Decide Upright or Italic for every font in a folder, the way the font tools are meant to. Read-only: no font is changed.

Usage:  python tools/resolve_slopes.py PATH [PATH ...] [-r] [--all] [--csv FILE]
Lists the fonts a person should look at, and counts the fonts whose filename, flags or names disagree with the decision.
"""

from __future__ import annotations

import argparse
import collections
import csv
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from FontCore.core_slope_resolver import gather_evidence, resolve_slopes  # noqa: E402

EXTENSIONS = {".ttf", ".otf"}


def _files(paths, recursive):
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob("*") if recursive else p.glob("*")):
                if f.suffix.lower() in EXTENSIONS and not f.name.startswith("."):
                    yield str(f)
        elif p.suffix.lower() in EXTENSIONS:
            yield str(p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--all", action="store_true", help="list every font, not only the ones to look at")
    ap.add_argument("--csv", metavar="FILE", help="write every decision to FILE")
    ap.add_argument("-j", "--jobs", type=int, default=8)
    args = ap.parse_args()
    files = list(_files(args.paths, args.recursive))
    with Pool(args.jobs) as pool:
        evidence = pool.map(gather_evidence, files, chunksize=64)
    decisions = resolve_slopes(evidence)
    counts = collections.Counter((d.role, d.slope) for d in decisions)
    for (role, slope), n in sorted(counts.items()):
        print(f"{n:7}  {role:10} {slope}")
    review = [d for d in decisions if d.review]
    differs = [d for d in decisions if d.differs and not d.review and d.slope != "free"]
    print(f"\n{len(review)} to look at, {len(differs)} more whose filename, flags or names disagree with the decision\n")
    shown = decisions if args.all else review
    for d in sorted(shown, key=lambda d: d.path):
        print(f"{Path(d.path).name}\n    {d.slope} ({d.confidence}, {d.role}); " + "; ".join(d.reasons)
              + (f"  [differs: {', '.join(d.differs)}]" if d.differs else ""))
    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["file", "slope", "confidence", "role", "review", "differs", "partner", "reasons"])
            for d in sorted(decisions, key=lambda d: d.path):
                w.writerow([d.path, d.slope, d.confidence, d.role, d.review, ",".join(d.differs), d.partner or "", " | ".join(d.reasons)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
