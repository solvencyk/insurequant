"""probe_transition_kr1107.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Is Pacific Life Re (KR1107) a transition-measure non-applier?  Prints
 (1) the sidecar data/_derived/kics_transition_applicability.json records for KR1107 (every quarter),
 (2) whether KR1107 is in the FSS 붙임-1 registry _TRANSITION_KIND of scripts/extract_transition_applicability.py (and what that registry contains for reinsurers).
"""
import io
import json
import re
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

side = json.loads((REPO / "data" / "_derived" / "kics_transition_applicability.json").read_text(encoding="utf-8"))
print("sidecar top-level keys:", list(side)[:10] if isinstance(side, dict) else type(side))
recs = side.get("records", side) if isinstance(side, dict) else side
n = 0
if isinstance(recs, dict):
    for k, v in recs.items():
        if "KR1107" in k:
            n += 1
            print(" ", k, json.dumps(v, ensure_ascii=False)[:400])
elif isinstance(recs, list):
    for v in recs:
        if isinstance(v, dict) and v.get("code") == "KR1107" or (isinstance(v, dict) and v.get("원보험사코드") == "KR1107"):
            n += 1
            print(" ", json.dumps(v, ensure_ascii=False)[:400])
print("KR1107 sidecar records:", n)

src = (REPO / "scripts" / "extract_transition_applicability.py").read_text(encoding="utf-8")
m = re.search(r"_TRANSITION_KIND\s*[:=].*?\n\}", src, re.S)
print("\n_TRANSITION_KIND block found:", bool(m))
if m:
    blk = m.group(0)
    print("  chars:", len(blk), "| contains KR1107:", "KR1107" in blk, "| contains KR11xx codes:", sorted(set(re.findall(r"KR11\d\d", blk))))
    for ln in blk.splitlines():
        if "KR11" in ln:
            print("  ", ln.strip()[:200])
