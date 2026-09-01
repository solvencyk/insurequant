# -*- coding: utf-8 -*-
"""AIG(KR0029) items 29-35 (생명장기 subs) and 36-40 (시장 subs) 적용전/후 status,
across 2024.4Q/2025.1Q/2025.2Q/2025.3Q/2026.1Q -- needed to know whether mirroring
item17/19 값_적용후 will newly expose POST_TRANSITION_CHILD_MISSING at the next tier down
(_PARENT_CHILD_AFTER[17]=29-35, [19]=36-40). Read-only.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "kics_disclosure.json"

with DISC.open("r", encoding="utf-8") as f:
    records = json.load(f)

byq = {}
for r in records:
    if r.get("원보험사코드") != "KR0029":
        continue
    q = r.get("공시분기")
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    byq.setdefault(q, {})[it] = (r.get("값"), r.get("값_적용후", "<NOKEY>"))

for q in ["2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2026.1Q"]:
    m = byq.get(q, {})
    print(f"-- {q} --")
    for it in [17, 29, 30, 31, 32, 33, 34, 35, 19, 36, 37, 38, 39, 40]:
        if it in m:
            v, vp = m[it]
            print(f"  item{it}: 값={v}  값_적용후={vp}")
        else:
            print(f"  item{it}: <ABSENT ROW>")
