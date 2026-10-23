# -*- coding: utf-8 -*-
"""KR0099 evidence (read-only): old -> new of every changed PL / CSM cell (git HEAD vs working tree), incl. the single-quarter (값_당분기) cells; writes changes_old_new.txt"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
NAME = {1: "보험손익", 2: "생명장기 손익", 3: "원수손익(장기)", 4: "원수 CSM상각", 5: "원수 위험조정", 6: "원수 예실차", 7: "기타 원수", 8: "재보험손익(장기)", 9: "재보험 CSM상각",
        10: "재보험 위험조정", 11: "재보험 예실차", 12: "기타 재보험", 13: "자동차", 14: "일반(+해외)", 15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익",
        20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품",
        29: "FVOCI 지분증권", 30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CNAME = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}


def head(rel):
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


def live(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
lines = []
for rel, names, tag in (("PL_breakdown.json", NAME, "PL"), ("CSM_waterfall.json", CNAME, "CSM")):
    h = {key(r): r for r in head(rel)}
    l = {key(r): r for r in live(rel)}
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        lines.append(f"== {tag} KR0099 {q}")
        for i in sorted({k[1] for k in l if k[0] == "KR0099" and k[2] == q}):
            a, b = h[("KR0099", i, q)], l[("KR0099", i, q)]
            if a == b:
                continue
            f = lambda v: "blank" if v is None else (f"{v:,.1f}" if tag == "CSM" else f"{v:,.0f}")  # noqa: E731
            parts = []
            if a["값"] != b["값"]:
                parts.append(f"누계 {f(a['값'])} -> {f(b['값'])}")
            if a.get("값_당분기") != b.get("값_당분기"):
                parts.append(f"단일분기 {f(a.get('값_당분기'))} -> {f(b.get('값_당분기'))}")
            lines.append(f"  i{i:>2} {names[i]:<16} " + " | ".join(parts))
(OUT / "changes_old_new.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
