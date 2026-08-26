#!/usr/bin/env python3
"""교보생명 2023.3Q gold item4 재계산 — 경계 정정으로 item2/3/6 이 움직여 항등식이 벌어졌다."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
m = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    if r["원보험사코드"] == "KR0073" and r["공시분기"] == "2023.3Q":
        m[r["항목번호"]] = r["값"]
resid = round(m[6] - (m[1] + m[2] + m[3] + m[5]), 2)
print("재계산 item4 =", resid, " (현재", m[4], ")")
WHY = ("2026-08-26 갱신(inbox/parser/20260826T0730Z §3, 목차 오검출 경계 정정): 별도 경계가 "
       "문서 목차의 '4. 재무제표' 를 물고 있어 이 필링의 모든 표가 OFS 로 태깅돼 basis 필터가 "
       "무효였다. '연결 제목과 별도 제목 사이에 <TABLE> 1개 이상' 조건을 넣자 이 분기 산출이 "
       "item2 10,292.2→10,255.1 · item3 5,773.1→5,755.0 · item6 64,694.3→63,948.4 로 바뀌었다. "
       "owner 가 고정한 item1(46,967.3, FY2023 year-start 통일)과 raw 재확정한 item5(-3,217.86)를 "
       "유지한 채 닫히도록 item4 를 잔차로 재계산한다(옛 4,879.56 은 정정 전 item2/3/6 에 맞춰 "
       "튜닝된 값이라 지금은 항등식을 +690.7 벌린다). 주의: 이 정정이 교보생명 FY2023 기초 분열"
       "(1Q/2Q 46,378.1 vs 3Q/4Q 46,967.3)과 3Q 기말>4Q 기말 역전을 닫지는 못한다 — 별건 미결.")
P = ROOT / "data/_gold/user_csm_cells.json"
d = json.loads(P.read_text(encoding="utf-8"))
keep, n_drop, n_set = [], 0, 0
for e in d["set"]:
    if e["원보험사코드"] == "KR0073" and e["공시분기"] == "2023.3Q" and e["항목번호"] == 4:
        if e["값"] == 4917.2:            # 2026-06-16 판, 뒤 엔트리에 덮여 죽은 중복
            n_drop += 1
            continue
        e["값"] = resid
        e["why"] = WHY
        n_set += 1
    keep.append(e)
assert n_set == 1 and n_drop == 1, (n_set, n_drop)
d["set"] = keep
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"item4 갱신 1건 · 죽은 중복 삭제 1건 · set {len(keep)}")
