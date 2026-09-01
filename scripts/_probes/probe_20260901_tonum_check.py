"""Check to_num parenthesis/negative handling and the AIA unit cue in raw text."""
from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_net_income_breakdown import to_num  # noqa: E402

for s in ["1,418,594,818", "(1,454,939)", "(46,782,206,680)", "-", "", "326,267", "△1,234"]:
    print(f"  to_num({s!r}) = {to_num(s)!r}")

print()
print("=== unit cue near 포괄손익계산서 in each AIA filing ===")
for d in sorted(glob.glob("data/dart/FY*/raw/KR0080_*")):
    for x in sorted(glob.glob(d + "/*.xml")):
        raw = open(x, "rb").read().decode("utf-8", "replace")
        flat = re.sub(r"<[^>]+>", " ", raw)
        flat = re.sub(r"\s+", " ", flat)
        # locate the 포괄손익계산서 heading
        idxs = [m.start() for m in re.finditer(r"포\s*괄\s*손\s*익\s*계\s*산\s*서", flat)]
        print(f"  {Path(d).name[:48]:48s} {Path(x).name}  headings={len(idxs)}")
        for i in idxs[:3]:
            seg = flat[i:i + 300]
            um = re.search(r"\(\s*단위\s*[:：]\s*([^)]{1,12})\)", seg)
            print(f"      @{i}: unit_cue={um.group(1).strip() if um else None!r} :: {seg[:150]}")
