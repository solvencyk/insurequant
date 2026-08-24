# -*- coding: utf-8 -*-
"""읽기 전용(사본 생성): KR0097 2024.4Q 적용후 4셀을 parser 정정 **이전** 상태로 되돌린 마스터 사본을 만든다.
게이트를 이 사본으로 돌려 출력이 진짜 마스터와 다른지 본다 = '게이트가 이 셀을 보는가' 의 변이시험."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1])
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
STALE = {33: "942.86", 34: "896.15"}
DROP = {30, 35}
n = 0
keep = []
for r in recs:
    if r.get("원보험사코드") == "KR0097" and r.get("공시분기") == "2024.4Q":
        it = int(r["항목번호"])
        if it in STALE:
            r = dict(r); r["값_적용후"] = STALE[it]; n += 1
        elif it in DROP:
            r = dict(r); r.pop("값_적용후", None); n += 1
    keep.append(r)
out.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"mutated cells={n} -> {out}")
