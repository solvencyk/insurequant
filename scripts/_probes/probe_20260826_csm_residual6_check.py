#!/usr/bin/env python3
"""수정 전·후 둘 다 마스터와 다른 6버킷: gold 로 덮이는지 / 화면에 나가는지 확인."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
uni = {}
for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    uni.setdefault(r["원보험사코드"], r["원수사명"])
rev = {}
for c, n in uni.items():
    rev.setdefault(n, c)
gold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
G = {(e["원보험사코드"], e["공시분기"], e["항목번호"]): e for e in gold["set"]}
mas = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"]
       for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
diag = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"]
        for r in json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))}
base = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
new = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
NAME = {1: "기초", 2: "신계약", 3: "이자", 4: "가정조정", 5: "상각", 6: "기말"}
TARGET = ["DB손해보험|2025.2Q", "DB손해보험|2025.3Q", "KB손해보험|2024.3Q",
          "삼성생명보험|2023.1Q", "미래에셋생명보험|2025.3Q", "농협생명보험|2023.1Q"]
for t in TARGET:
    nm, q = t.split("|")
    code = rev.get(nm)
    print("=" * 96)
    print(f"### {nm} ({code}) {q}")
    k = f"{code}|{q}"
    wb = (base.get(k) or {}).get("wf") or {}
    wn = (new.get(k) or {}).get("wf") or {}
    for i in range(1, 7):
        vb, vn = wb.get(str(i), wb.get(i)), wn.get(str(i), wn.get(i))
        mv, dv = mas.get((code, q, i)), diag.get((code, q, i))
        g = G.get((code, q, i))
        gtxt = "" if not g else f"GOLD={g['값']} why={'있음' if (g.get('why') or g.get('note')) else '공란'}"
        star = "" if (isinstance(vb, float) and isinstance(vn, float) and abs(vb - vn) < 0.05) else " <-- 변경"
        f = lambda v: "-" if v is None else f"{v:,.1f}"
        print(f"  {NAME[i]:5s} 전={f(vb):>11s} 후={f(vn):>11s} diag={f(dv):>11s} 마스터={f(mv):>11s} {gtxt}{star}")
