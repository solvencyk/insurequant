# -*- coding: utf-8 -*-
"""read-only: on-screen effects of the 현대해상 load in 억원 (1억 = 100백만): cumulative and single-quarter, before (backup) -> after (live)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"
OUT = Path(__file__).resolve().parent


def load(base, rel):
    return json.loads((base / rel).read_text(encoding="utf-8"))


pl0, pl1 = load(BK, "PL_breakdown.json"), load(ROOT, "PL_breakdown.json")
cs0, cs1 = load(BK, "CSM_waterfall.json"), load(ROOT, "CSM_waterfall.json")
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
P0, P1 = {key(r): r for r in pl0}, {key(r): r for r in pl1}
C0, C1 = {key(r): r for r in cs0}, {key(r): r for r in cs1}
f = lambda v: "blank" if v is None else f"{v / 100:,.2f}"  # noqa: E731
g = lambda v: "blank" if v is None else f"{v:,.2f}"  # noqa: E731
lines = []
NM = {1: "보험손익", 17: "투자손익", 24: "당기순이익", 25: "기타포괄손익", 31: "총포괄손익", 20: "영업이익", 4: "원수CSM상각(PL)"}
lines.append("PL (억원), 누계 before -> after | 단일분기 before -> after")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for it, nm in NM.items():
        a, b = P0.get(("KR0009", it, q)), P1.get(("KR0009", it, q))
        if a is None or b is None:
            continue
        if a["값"] == b["값"] and a.get("값_당분기") == b.get("값_당분기"):
            continue
        lines.append(f"  {q} {nm:8s}: 누계 {f(a['값']):>10s} -> {f(b['값']):>10s} ({'' if a['값'] is None or b['값'] is None else format((b['값'] - a['값']) / 100, '+,.2f')}) | 단일분기 {f(a.get('값_당분기')):>10s} -> {f(b.get('값_당분기')):>10s}")
lines.append("CSM (억원), 누계 before -> after | 단일분기 before -> after")
CN = {1: "기초", 2: "신계약", 3: "이자부리", 4: "가정조정", 5: "상각", 6: "기말"}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for it, nm in CN.items():
        a, b = C0.get(("KR0009", it, q)), C1.get(("KR0009", it, q))
        if a["값"] == b["값"] and a.get("값_당분기") == b.get("값_당분기"):
            continue
        lines.append(f"  {q} {nm:4s}: 누계 {g(a['값']):>10s} -> {g(b['값']):>10s} ({b['값'] - a['값']:+,.1f}) | 단일분기 {g(a.get('값_당분기')):>10s} -> {g(b.get('값_당분기')):>10s}")
# full old -> new list of PL cells for the answer table
lines.append("")
lines.append("PL cells changed (백만원): quarter item name old -> new")
NAME = {r["항목번호"]: r["항목명"] for r in pl1 if r["원보험사코드"] == "KR0009"}
for k in sorted((k for k in P1 if k[0] == "KR0009" and P0[k]["값"] != P1[k]["값"]), key=lambda k: (k[2], int(k[1]))):
    lines.append(f"  {k[2]} {k[1]:>2} {NAME.get(k[1], '')[:12]:12s}: {P0[k]['값']} -> {P1[k]['값']}")
(OUT / "d01_screen_effects.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[:60]))
