# -*- coding: utf-8 -*-
"""Read-only: old (backup = pre-load state) -> new (live) table of every changed KR0003 cell, plus the on-screen effects in 억원.  Writes changes_old_new.txt."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = Path(__file__).resolve().parent
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte"
sys.stdout.reconfigure(encoding="utf-8")
CODE, Q = "KR0003", "2023.4Q"


def rows(p):
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads(Path(p).read_text(encoding="utf-8"))}


pl0, pl1 = rows(BK / "PL_breakdown.json"), rows(ROOT / "PL_breakdown.json")
c0, c1 = rows(BK / "CSM_waterfall.json"), rows(ROOT / "CSM_waterfall.json")
out = []
out.append("PL 누계(값) 변경 (백만원): 항목 | 이름 | 옛 | 새 | 변동")
for i in range(1, 33):
    a, b = pl0[(CODE, i, Q)], pl1[(CODE, i, Q)]
    if a["값"] != b["값"]:
        out.append(f"  {i:2d} {a['항목명']:<14s} {a['값']:>16,.6f} -> {b['값']:>16,.6f}  ({b['값'] - a['값']:+,.6f})")
out.append("")
out.append("PL 단일분기(값_당분기) 변경 (백만원): 옛 -> 새")
for i in range(1, 33):
    a, b = pl0[(CODE, i, Q)], pl1[(CODE, i, Q)]
    if a["값_당분기"] != b["값_당분기"]:
        out.append(f"  {i:2d} {a['항목명']:<14s} {a['값_당분기']!s:>20} -> {b['값_당분기']!s}")
out.append("")
out.append("CSM 누계(값) 변경 (억원): 항목 | 옛 | 새 | 변동")
for i in range(1, 7):
    a, b = c0[(CODE, i, Q)], c1[(CODE, i, Q)]
    if a["값"] != b["값"]:
        out.append(f"  {i} {a['항목명']:<14s} {a['값']:>10.1f} -> {b['값']:>10.1f}  ({b['값'] - a['값']:+.1f})")
out.append("CSM 단일분기(값_당분기) 변경 (억원): 옛 -> 새")
for i in range(1, 7):
    a, b = c0[(CODE, i, Q)], c1[(CODE, i, Q)]
    if a["값_당분기"] != b["값_당분기"]:
        out.append(f"  {i} {a['항목명']:<14s} {a['값_당분기']:>10.1f} -> {b['값_당분기']:>10.1f}  ({b['값_당분기'] - a['값_당분기']:+.1f})")
out.append("")
out.append("화면 효과 (억원 = 백만원/100), 누계 | 단일분기")
nm = {1: "보험손익", 17: "투자손익", 20: "영업이익", 24: "당기순이익", 25: "기타포괄손익", 31: "총포괄손익"}
for i, n in nm.items():
    a, b = pl0[(CODE, i, Q)], pl1[(CODE, i, Q)]
    d = b["값"] / 100 - a["값"] / 100
    sa = "blank" if a["값_당분기"] is None else f"{a['값_당분기'] / 100:,.2f}"
    sb = "blank" if b["값_당분기"] is None else f"{b['값_당분기'] / 100:,.2f}"
    out.append(f"  {n:<8s} 누계 {a['값'] / 100:>10,.2f} -> {b['값'] / 100:>10,.2f} ({d:+,.2f}) | 단일분기 {sa} -> {sb}")
for i, n in ((1, "기초 CSM"), (6, "기말 CSM"), (5, "CSM 상각")):
    a, b = c0[(CODE, i, Q)], c1[(CODE, i, Q)]
    out.append(f"  {n:<8s} {a['값']:>10,.1f} -> {b['값']:>10,.1f} ({b['값'] - a['값']:+,.1f})")
# the FY2023 block after the load
out.append("")
out.append("FY2023 블록 기초 CSM(항목 1) 분기별: " + ", ".join(f"{q} {c1[(CODE, 1, q)]['값']:.1f}" for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q")))
d = (c1[(CODE, 1, '2023.3Q')]['값'] - c1[(CODE, 1, '2023.4Q')]['값']) / c1[(CODE, 1, '2023.3Q')]['값'] * 100
out.append(f"  연내 기초 편차 (2023.3Q 대비 2023.4Q) = {d:.3f}% (임계 0.5%)")
out.append(f"FY 경계: 2023.4Q 기말 {c1[(CODE, 6, '2023.4Q')]['값']:.1f} vs 2024.1Q 기초 {c1[(CODE, 1, '2024.1Q')]['값']:.1f} (차이 {c1[(CODE, 6, '2023.4Q')]['값'] - c1[(CODE, 1, '2024.1Q')]['값']:+.1f}; 옛 {c0[(CODE, 6, '2023.4Q')]['값'] - c0[(CODE, 1, '2024.1Q')]['값']:+.1f})")
(OUT / "changes_old_new.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
