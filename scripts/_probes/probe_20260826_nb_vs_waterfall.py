#!/usr/bin/env python3
"""NB_CSM_multiple.json 의 신계약CSM 이 CSM_waterfall.json 항목2 와 어긋난 셀 전수."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
wf = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    if r.get("항목번호") == 2:
        wf[(r["원보험사코드"], r["공시분기"])] = (r.get("값"), r.get("값_당분기"))
nb = json.loads((ROOT / "NB_CSM_multiple.json").read_text(encoding="utf-8"))
diff, missing = [], []
for r in nb:
    k = (r["원보험사코드"], r["공시분기"])
    if k not in wf:
        missing.append((k, r.get("신계약CSM_연누계")))
        continue
    a, b = wf[k]
    for fld, v in (("신계약CSM_연누계", a), ("신계약CSM_당분기", b)):
        cur = r.get(fld)
        if cur is None and v is None:
            continue
        if isinstance(cur, (int, float)) and isinstance(v, (int, float)) and abs(cur - v) < 0.05:
            continue
        diff.append((r["원수사명"], k[0], k[1], fld, cur, v))
print(f"NB 행 {len(nb)} · 워터폴에 없는 (code,q) {len(missing)} · 어긋난 셀 {len(diff)}")
for d in diff:
    print(f"  {d[0][:14]:14s} {d[2]:8s} {d[3]:14s} NB={d[4]} <- WF={d[5]}")
wfcq = {k for k in wf}
nbcq = {(r["원보험사코드"], r["공시분기"]) for r in nb}
only_wf = sorted(wfcq - nbcq)
print(f"\n워터폴엔 있고 NB 엔 없는 (code,q) {len(only_wf)}: {only_wf[:12]}")
