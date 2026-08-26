#!/usr/bin/env python3
"""KR0069 2023.4Q gold 2셀만 갱신 — 셀단위, 나머지 275건 무접촉."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
P = ROOT / "data/_gold/user_csm_cells.json"
d = json.loads(P.read_text(encoding="utf-8"))
WHY = ("2026-08-26 갱신(inbox/parser/20260826T0500Z ② 후속): 이 셀들이 있던 이유는 misparse 가 "
       "아니라 연결/별도 오선택이었다. 본문 XML 에 연결·별도 주석이 다 들어 있는데 blocks_for_dir 에 "
       "basis 필터가 없어 문서 순서상 앞선 연결이 뽑혔다(파일단위 확증: 1,384,276=_00761 만, "
       "1,367,673=_00760 만). 필터 배선 후 raw 가 별도 기말 122,473.7 을 직접 낸다 — owner 값 "
       "122,474.0 과 0.3 차(반올림). item6 은 owner 값을 유지하고, item4 는 그 값에 닫히는 "
       "잔차 -11,633.9 로 고친다(옛 -11,454.0 은 연결 상각 -13,842.8 을 흡수하던 값이라, 상각이 "
       "별도 -13,676.7 로 바뀐 지금은 항등식을 +179.9 벌린다).")
n = 0
for e in d["set"]:
    if e["원보험사코드"] == "KR0069" and e["공시분기"] == "2023.4Q":
        if e["항목번호"] == 4:
            assert e["값"] == -11454.0, e
            e["값"] = -11633.9
            n += 1
        elif e["항목번호"] == 6:
            assert e["값"] == 122474.0, e
            n += 1
        e["why"] = WHY
assert n == 2, n
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("gold 2셀 갱신 완료, set 총", len(d["set"]))
