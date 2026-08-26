#!/usr/bin/env python3
"""CSM basis 수정 전/후 diff + 마스터 대조."""
import sys, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
base = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
new = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
uni = {r["원보험사코드"]: r["원수사명"] for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))}
mas = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    mas[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]

NAME = {1: "기초", 2: "신계약", 3: "이자", 4: "가정조정", 5: "상각", 6: "기말"}
chg, nulled, gained = [], [], []
for k in sorted(set(base) | set(new)):
    b, n = base.get(k, {}), new.get(k, {})
    wb, wn = b.get("wf"), n.get("wf")
    if wb and not wn:
        nulled.append(k); continue
    if wn and not wb:
        gained.append(k); continue
    if not wb or not wn:
        continue
    for i in range(1, 7):
        vb, vn = wb.get(str(i), wb.get(i)), wn.get(str(i), wn.get(i))
        if vb is None and vn is None:
            continue
        if isinstance(vb, (int, float)) and isinstance(vn, (int, float)) and abs(vb - vn) < 0.05:
            continue
        if vb != vn:
            chg.append((k, i, vb, vn))

print(f"버킷 {len(base)}  값변경 셀 {len(chg)}  새로 None {len(nulled)}  새로 생김 {len(gained)}")
cq = sorted({k for k, *_ in chg})
print(f"영향 company-quarter {len(cq)}  회사 {len({k.split('|')[0] for k in cq})}")
print("항목별:", dict(sorted(Counter(i for _, i, _, _ in chg).items())))
if nulled:
    print("커버리지 손실:", nulled[:20])
print()
print(f"{'회사':16s} {'분기':8s} {'항목':>8s} {'전':>12s} {'후':>12s} {'마스터':>12s} {'마스터일치':>8s}")
for k in cq:
    code, q = k.split("|")
    for kk, i, vb, vn in chg:
        if kk != k:
            continue
        mv = mas.get((code, q, i))
        eq = "" if mv is None else ("전=마스터" if abs((vb or 0) - mv) < 0.05 else
                                    ("후=마스터" if abs((vn or 0) - mv) < 0.05 else "둘다≠"))
        f = lambda v: "-" if v is None else f"{v:,.1f}"
        print(f"{uni.get(code,code)[:16]:16s} {q:8s} {NAME[i]:>8s} {f(vb):>12s} {f(vn):>12s} {f(mv):>12s} {eq:>8s}")
