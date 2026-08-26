#!/usr/bin/env python3
"""NB 배포본에 빠진 (회사,분기) 행을 워터폴 항목2 로 추가 — 빌더가 낼 모양 그대로.

월납월초(KIDI)가 디스크에 없으므로 분모·배수는 null (빌더 규약: "월납 없으면 배수=null,
회사 행은 유지" — 기존 KR1011 2023.4Q 선례와 동일한 모양).
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
DRY = "--dry-run" in sys.argv
TARGETS = [("KR0049", "2023.4Q"), ("KR0050", "2023.4Q"), ("KR0076", "2023.4Q"), ("KR1010", "2023.4Q")]

wf = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    if r.get("항목번호") == 2:
        wf[(r["원보험사코드"], r["공시분기"])] = r

P = ROOT / "NB_CSM_multiple.json"
rows = json.loads(P.read_text(encoding="utf-8"))
have = {(r["원보험사코드"], r["공시분기"]) for r in rows}
added = 0
for key in TARGETS:
    if key in have:
        print(f"  {key} 이미 있음 — 건너뜀"); continue
    src = wf.get(key)
    if src is None:
        print(f"  {key} 워터폴에 없음 — 건너뜀"); continue
    new = {"원보험사코드": src["원보험사코드"], "원수사명": src["원수사명"],
           "티커": src.get("티커"), "생손보여부": src.get("생손보여부"),
           "공시분기": src["공시분기"],
           "신계약CSM_연누계": src.get("값"), "월납월초보험료_연누계": None,
           "신계약CSM배수_연누계": None,
           "신계약CSM_당분기": src.get("값_당분기"), "월납월초보험료_당분기": None,
           "신계약CSM배수_당분기": None}
    idx = max([i for i, r in enumerate(rows) if r["원보험사코드"] == key[0]], default=None)
    if idx is None:
        rows.append(new)
    else:
        rows.insert(idx + 1, new)
    print(f"  + {new['원수사명']} {key[1]} 신계약CSM={new['신계약CSM_연누계']} (배수 null)")
    added += 1
print(f"\n{added}행 추가" + ("  (dry-run)" if DRY else ""))
if not DRY and added:
    P.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", P, "총", len(rows), "행")
