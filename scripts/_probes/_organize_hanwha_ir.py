# -*- coding: utf-8 -*-
"""Move downloaded Hanwha Life / Hanwha GI IR files from staging into
data/ir/FY{YYYY}_Q{N}/<KR_dir>/<original_filename>.

Staging filenames are prefixed FY{YYYY}_Q{N}_<kind>_<original>. We strip that
prefix and place the original-named file under the right quarter dir.
Only quarters in the requested range FY2023.1Q .. FY2026.1Q are moved.
"""
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/ir").resolve()
JOBS = [
    ("decks/hanwha_life", "KR0068_한화생명", r"FY(\d{4})_Q(\d)_(deck|factsheet)_(.+)"),
    ("decks/hanwha_gi", "KR0002_한화손해보험", r"FY(\d{4})_Q(\d)_(.+)"),
]


def in_range(y, q):
    if y < 2023 or y > 2026:
        return False
    if y == 2026 and q > 1:
        return False
    return True


def main():
    moved = 0
    for stage_rel, kr_dir, pat in JOBS:
        stage = ROOT / stage_rel
        rx = re.compile(pat)
        for f in sorted(stage.glob("*")):
            if f.name.startswith("_") or f.suffix == ".json":
                continue
            m = rx.match(f.name)
            if not m:
                continue
            y, q = int(m.group(1)), int(m.group(2))
            if not in_range(y, q):
                continue
            orig = m.group(m.lastindex)  # last capture = original filename
            dest_dir = ROOT / f"FY{y}_Q{q}" / kr_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / orig
            shutil.copy2(f, dest)
            moved += 1
            print(f"  {dest.relative_to(ROOT.parent.parent)}  ({dest.stat().st_size} B)")
    print(f"\n{moved} files placed under data/ir/FY*/")


if __name__ == "__main__":
    main()
