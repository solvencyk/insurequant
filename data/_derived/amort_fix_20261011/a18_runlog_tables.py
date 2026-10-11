# -*- coding: utf-8 -*-
"""a18 (read-only): print the Markdown tables that go into the runlog (no hand transcription): the 21 FY2025 files whose pick moved."""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
diff = json.loads((W / "a08_selection_diff.json").read_text(encoding="utf-8"))
proof = {r["company"]: r for r in json.loads((W / "a10_final_proof.json").read_text(encoding="utf-8"))}
plan = json.loads((W / "amort_cells_fix_plan.json").read_text(encoding="utf-8"))


def short(src):
    s = str(src)
    return "본문" if s.endswith(f"{s.split('_')[0]}.xml") and "_0076" not in s else ("별도(_00760)" if "_00760" in s else ("연결(_00761)" if "_00761" in s else s))


print("| 회사 | 접수번호 | 원본 | 옛 선택 줄 | 새 선택 줄 | 옛 역할(원문) | 합계 옛 → 새 (억원) | 기말 CSM FY2025 / FY2024 | 정정 칸 |")
print("|---|---|---|---|---|---|---|---|---|")
for fn, d in sorted(diff.items(), key=lambda kv: (kv[1]["company"], kv[1]["rcept"])):
    if not d["rcept"].startswith("2026"):
        continue
    co = d["company"]
    p = proof.get(co) or {}
    onrole = (p.get("old") or [None, None])[1]
    nr = (p.get("new") or [None, None])[1]
    rb, ra = d["result_before"] or {}, d["result_after"] or {}
    tb, ta = (rb.get("buckets") or {}).get("total"), (ra.get("buckets") or {}).get("total")
    cells = next((e for c, e in plan.items() if c == co), None)
    nch = sum(1 for c in cells["cells"] if c["changed"]) if cells else "-"
    feed = "" if p.get("rcept") == d["rcept"] else " (패널 미사용 사본)"
    print(f"| {co}{feed} | {d['rcept']} | {short(d['pick_before'][1])} | {d['pick_before'][0]} | {d['pick_after'][0]} | {onrole} → {nr} | {tb:,.2f} → {ta:,.2f} | {p.get('close_FY')} / {p.get('close_FY-1')} | {nch} |")
