"""Semantic compare: HEAD's PL_breakdown.json vs my pre-change backup."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)

head = json.loads(subprocess.run(
    ["git", "show", "HEAD:PL_breakdown.json"], capture_output=True, check=True).stdout.decode("utf-8"))
bak = json.loads(Path("PL_breakdown.json.bak_20260901_aia").read_text(encoding="utf-8"))


def cells(rows):
    return {(r["원보험사코드"], r["공시분기"], r["항목번호"]): (r["값"], r.get("값_당분기"))
            for r in rows}


h, b = cells(head), cells(bak)
print(f"HEAD rows={len(head)} cells={len(h)}")
print(f"BAK  rows={len(bak)} cells={len(b)}")
only_h = sorted(k for k in h if k not in b)
only_b = sorted(k for k in b if k not in h)
diff = sorted(k for k in h if k in b and h[k] != b[k])
print(f"only in HEAD: {len(only_h)}  only in BAK: {len(only_b)}  value diffs: {len(diff)}")
for k in only_h[:10]:
    print("   HEAD-only", k, h[k])
for k in only_b[:10]:
    print("   BAK-only ", k, b[k])
for k in diff[:20]:
    print("   diff", k, h[k], "->", b[k])
print("\nSEMANTICALLY IDENTICAL" if not (only_h or only_b or diff)
      else "\n*** CONTENT DIFFERS ***")
