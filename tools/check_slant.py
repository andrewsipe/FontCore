#!/usr/bin/env python3
"""Compare each font's declared italic angle with the lean measured from its outlines. Read-only: no font is changed.

Usage:  python tools/check_slant.py PATH [PATH ...] [-r] [--all]
Only fonts whose declared angle disagrees with the outlines are listed unless --all is given.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fontTools.ttLib import TTFont  # noqa: E402

from FontCore.core_slant_measure import check_slant  # noqa: E402

EXTENSIONS = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}


def _files(paths, recursive):
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob("*") if recursive else p.glob("*")):
                if f.suffix.lower() in EXTENSIONS and not f.name.startswith("."):
                    yield f
        elif p.suffix.lower() in EXTENSIONS:
            yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--all", action="store_true", help="also list fonts whose angle is right")
    args = ap.parse_args()
    counts: dict[str, int] = {}
    for f in _files(args.paths, args.recursive):
        try:
            verdict = check_slant(TTFont(f, lazy=True, fontNumber=0))
        except Exception as exc:  # unreadable font: say so and go on
            print(f"{f.name}: could not read ({exc})")
            continue
        counts[verdict.verdict] = counts.get(verdict.verdict, 0) + 1
        if args.all or verdict.verdict not in ("ok", "unmeasurable"):
            measured = "?" if verdict.measured is None else f"{verdict.measured:g}"
            print(f"{verdict.verdict:26} declared {verdict.declared:>7.2f}  measured {measured:>7}  {f.name}")
    print("\n" + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
