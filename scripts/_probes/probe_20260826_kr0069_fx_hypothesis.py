#!/usr/bin/env python3
"""① 검증: 삼성생명 item3 10셀 차이 = '환율변동효과 등' 행의 CSM 열 가산분인가?

가설: 현재값 = 순금융손익 + 환율변동, 이전값(8a3b930^) = 순금융손익만.
검증법: 블록에서 '환율변동' 행만 제거한 사본으로 block_stages 를 돌려(다른 경로 전부 동일)
        waterfall_for_dir 을 재실행 → 그 결과가 이전 마스터값과 일치하는지 본다.
read-only. 파일 미기록.
"""
import sys, re, json, copy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from viz_build_csm_waterfall import row_value_start

PRE = Path(sys.argv[1])
QS = ["FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1"]
QMAP = {"FY2024_Q1": "2024.1Q", "FY2024_Q2": "2024.2Q", "FY2024_Q3": "2024.3Q",
        "FY2024_Q4": "2024.4Q", "FY2025_Q1": "2025.1Q"}

pre = {}
for r in json.loads(PRE.read_text(encoding="utf-8")):
    if r["원보험사코드"] == "KR0069":
        pre[(r["공시분기"], r["항목번호"])] = r["값"]
cur = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    if r["원보험사코드"] == "KR0069":
        cur[(r["공시분기"], r["항목번호"])] = r["값"]

_orig = B.block_stages

def _strip_fx(b):
    nb = dict(b)
    nb["rows"] = [r for r in (b.get("rows") or [])
                  if "환율변동" not in "".join(str(c) for c in r[:row_value_start(r)]
                                             if isinstance(c, str))]
    return nb

def patched(b):
    return _orig(_strip_fx(b))

print(f"{'분기':9s} {'item3 이전':>11s} {'item3 현재':>11s} {'fx제거 재현':>11s} {'판정':>6s}"
      f"   |  {'item4 이전':>11s} {'item4 현재':>11s} {'fx제거':>11s}")
for q in QS:
    rd = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))[0]
    qq = QMAP[q]
    B.block_stages = patched
    try:
        wf_nofx, _ = B.waterfall_for_dir(rd, "삼성생명")
    finally:
        B.block_stages = _orig
    v3 = (wf_nofx or {}).get(3)
    v4 = (wf_nofx or {}).get(4)
    ok = "일치" if v3 is not None and pre.get((qq, 3)) is not None and abs(v3 - pre[(qq, 3)]) < 0.05 else "불일치"
    print(f"{qq:9s} {pre.get((qq,3)):>11} {cur.get((qq,3)):>11} {v3:>11} {ok:>6s}"
          f"   |  {pre.get((qq,4)):>11} {cur.get((qq,4)):>11} {v4:>11}")

print()
print("현재 코드(환율 가산) 재현 검산:")
for q in QS:
    rd = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))[0]
    wf, src = B.waterfall_for_dir(rd, "삼성생명")
    qq = QMAP[q]
    same = all(abs((wf or {}).get(i, 0) - (cur.get((qq, i)) or 0)) < 0.05 for i in (1, 2, 3, 4, 5, 6))
    print(f"  {qq}  raw재추출={{{', '.join(f'{i}:{(wf or {}).get(i)}' for i in (1,2,3,4,5,6))}}}  "
          f"마스터일치={'YES' if same else 'NO'}  src={src}")
