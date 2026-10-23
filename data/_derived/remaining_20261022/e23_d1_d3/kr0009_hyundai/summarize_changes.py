# -*- coding: utf-8 -*-
"""read-only: old -> new list of every cell the 현대해상 D3 load changed (backup = pre-load state, repo = post-load state), with the filing line / IR cell of the new print (plan parts) -> changes_old_new.txt,
plus the on-screen table (억원) for 보험손익 / 투자손익 / 당기순이익 / 기타포괄손익 / 총포괄손익 / CSM 기초·상각·기말 (cumulative and single quarter)."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / "e23_plan_hd_final.json").read_text(encoding="utf-8"))
NAME = {1: "보험손익", 2: "생명장기 손익(장기 LOB)", 4: "원수 CSM상각", 13: "자동차 손익(LOB)", 14: "일반 손익(LOB)", 15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익",
        20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품", 29: "FVOCI 지분증권",
        30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CNAME = {1: "기초", 2: "신계약", 3: "이자 부리", 4: "가정·경험 조정", 5: "상각", 6: "기말"}
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
h = {key(r): r for r in json.loads((BK / "PL_breakdown.json").read_text(encoding="utf-8"))}
l = {key(r): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
ch = {key(r): r for r in json.loads((BK / "CSM_waterfall.json").read_text(encoding="utf-8"))}
cl = {key(r): r for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
cells = {(c["quarter"], c["item"]): c for b in PLAN["buckets"] for c in b["cells"]}
f = lambda v, nd=6: "blank" if v is None else f"{v:,.{nd}f}"  # noqa: E731
out = ["PL 누계(값) 변경 (백만원): 분기 · 항목 · 옛 -> 새 · 차 · 새 값의 원천(필링 줄 또는 IR 셀)"]
n = 0
for (q, it), c in sorted(cells.items()):
    k = ("KR0009", it, q)
    o, nw = h[k]["값"], l[k]["값"]
    p = c["parts"][0] if c["parts"] else None
    if p and p.get("cell"):
        src = f"IR {Path(p['xlsx']).parent.parent.parent.name} 시트 '(3) UW Income' 셀 {p['cell']}"
    elif p:
        src = f"{Path(c['xml_file']).name} L{p['line']}"
    else:
        src = "(기본값 0.0: 보험영업 구간에 기타영업수익 행 없음)"
    out.append(f"  {q} i{it:>2} {NAME[it]:16s}: {f(o):>18s} -> {f(nw):>18s}  ({'' if o is None else format(nw - o, '+,.6f')})  {src}")
    n += 1
out.append(f"  ({n} cells)")
out.append("")
out.append("제외한 후보 (계획 58칸 중 1칸): 2023.4Q i16 기타사업비용 — 마스터(owner gold, 원장 박제 있음) 38,491.0 vs 최신 비교열 38,490.968273 (L51752): 반올림 차이뿐이라 제외(티켓 규칙).")
out.append("")
out.append("값_당분기 변경 (PL): " + str(sum(1 for k in l if k[0] == "KR0009" and h[k].get("값_당분기") != l[k].get("값_당분기"))) + "칸")
out.append("CSM 변경 (억원): 분기 · 항목 · 옛 -> 새")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for i in range(1, 7):
        k = ("KR0009", i, q)
        if ch[k]["값"] != cl[k]["값"]:
            tag = ""
            if (q, i) in (("2023.3Q", 1), ("2023.3Q", 4), ("2023.4Q", 1)):
                tag = "  [owner gold 제거: 승인값 = 빌더 소스 값]"
            elif (q, i) == ("2023.4Q", 4):
                tag = "  [owner gold 교체]"
            out.append(f"  {q} {CNAME[i]:8s}: {ch[k]['값']:>9,.1f} -> {cl[k]['값']:>9,.1f} ({cl[k]['값'] - ch[k]['값']:+,.1f}){tag}")
out.append("")
out.append("화면 (억원 = 백만원/100): 누계 옛 -> 새 | 단일분기 옛 -> 새")
for it in (1, 17, 24, 25, 31):
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        k = ("KR0009", it, q)
        a, b = h[k], l[k]
        g = lambda v: "blank" if v is None else f"{v / 100:,.2f}"  # noqa: E731
        out.append(f"  {NAME[it]:8s} {q}: 누계 {g(a['값']):>9s} -> {g(b['값']):>9s} | 단일분기 {g(a['값_당분기']):>9s} -> {g(b['값_당분기']):>9s}")
for i in (6, 5, 1):
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        k = ("KR0009", i, q)
        out.append(f"  CSM {CNAME[i]:4s} {q}: 누계 {ch[k]['값']:>9,.1f} -> {cl[k]['값']:>9,.1f} | 단일분기 {ch[k]['값_당분기']:>9,.1f} -> {cl[k]['값_당분기']:>9,.1f}")
(HERE / "changes_old_new.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
