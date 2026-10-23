# -*- coding: utf-8 -*-
"""read-only: old -> new list of every cell the ABL D3 load changed (backup = pre-load state, repo = post-load state), with the filing line of the new print (plan parts) -> changes_old_new.txt,
plus the on-screen table (억원) for 보험손익 / 투자손익 / 당기순이익 / 기타포괄손익 / 총포괄손익 / CSM 기초·상각·기말 (cumulative and single quarter)."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0070_abl"
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / "e23_plan_abl_final.json").read_text(encoding="utf-8"))
NAME = {1: "보험손익", 2: "생명장기 손익", 3: "원수손익(장기)", 4: "원수 CSM상각", 8: "재보험손익(장기)", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익",
        22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품", 30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CNAME = {1: "기초", 2: "신계약", 3: "이자 부리", 4: "가정·경험 조정", 5: "상각", 6: "기말"}
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
h = {key(r): r for r in json.loads((BK / "PL_breakdown.json").read_text(encoding="utf-8"))}
l = {key(r): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
ch = {key(r): r for r in json.loads((BK / "CSM_waterfall.json").read_text(encoding="utf-8"))}
cl = {key(r): r for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
cells = {(c["quarter"], c["item"]): c for b in PLAN["buckets"] for c in b["cells"]}
f = lambda v, nd=6: "blank" if v is None else f"{v:,.{nd}f}"  # noqa: E731
out = ["PL 누계(값) 변경 (백만원): 분기 · 항목 · 옛 -> 새 · 차 · 새 값의 필링 줄(첫 부분)"]
n = 0
for (q, it), c in sorted(cells.items()):
    k = ("KR0070", it, q)
    o, nw = h[k]["값"], l[k]["값"]
    ln = c["parts"][0]["line"] if c["parts"] else None
    srcf = Path(c["xml_file"]).name
    out.append(f"  {q} i{it:>2} {NAME[it]:14s}: {f(o):>18s} -> {f(nw):>18s}  ({'' if o is None else format(nw - o, '+,.6f')})  {srcf} L{ln}{' [gold 교체]' if (q, it) == ('2023.1Q', 4) else ''}")
    n += 1
out.append(f"  ({n} cells)")
out.append("")
out.append("CSM 변경 (억원): 분기 · 항목 · 옛 -> 새")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for i in range(1, 7):
        k = ("KR0070", i, q)
        if ch[k]["값"] != cl[k]["값"]:
            out.append(f"  {q} {CNAME[i]:8s}: {ch[k]['값']:>9,.1f} -> {cl[k]['값']:>9,.1f} ({cl[k]['값'] - ch[k]['값']:+,.1f})" + ("  [gold 제거: 빌더 소스 값]" if (q, i) in (("2023.4Q", 1), ("2023.4Q", 4)) else ""))
out.append("")
out.append("화면 (억원 = 백만원/100): 누계 옛 -> 새 | 단일분기 옛 -> 새")
for it in (1, 17, 24, 25, 31):
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        k = ("KR0070", it, q)
        a, b = h[k], l[k]
        g = lambda v: "blank" if v is None else f"{v / 100:,.2f}"  # noqa: E731
        out.append(f"  {NAME[it]:8s} {q}: 누계 {g(a['값']):>9s} -> {g(b['값']):>9s} | 단일분기 {g(a['값_당분기']):>9s} -> {g(b['값_당분기']):>9s}")
for i in (6, 5, 1):
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        k = ("KR0070", i, q)
        out.append(f"  CSM {CNAME[i]:4s} {q}: 누계 {ch[k]['값']:>9,.1f} -> {cl[k]['값']:>9,.1f} | 단일분기 {ch[k]['값_당분기']:>9,.1f} -> {cl[k]['값_당분기']:>9,.1f}")
(HERE / "changes_old_new.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
