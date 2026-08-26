#!/usr/bin/env python3
"""(a) KR0069 2026.2Q anchor 재추출  (b) ③ diag stale 주장 검증."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B

print("=== (a) KR0069 anchor 재추출 ===")
for q, anc in [("FY2026_Q2", 132178.7), ("FY2026_Q1", 132178.7), ("FY2025_Q4", 122473.7)]:
    dirs = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))
    if not dirs:
        print(f"  {q}: raw 없음"); continue
    wf, src = B.waterfall_for_dir(dirs[0], "삼성생명", anchor=anc)
    print(f"  {q} anchor={anc}: " + " ".join(f"{i}={(wf or {}).get(i)}" for i in (1,2,3,4,5,6)) + f"  src={src}")

print()
print("=== (b) diag(2026-08-17) vs 현재 코드 재추출 — 단위 리터럴 수정이 실렸나 ===")
diag = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"]
        for r in json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))}
master = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"]
          for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
for code, name, q in [("KR0029", "AIG손해보험", "FY2025_Q4"), ("KR0075", "동양생명보험", "FY2025_Q4"),
                      ("KR1098", "하나생명보험", "FY2025_Q4"), ("KR0051", "", "FY2025_Q4")]:
    dirs = sorted((ROOT / "data" / "dart" / q / "raw").glob(f"{code}_*"))
    qq = q.replace("FY", "").replace("_Q", ".") + "Q"
    if not dirs:
        print(f"  {code} {qq}: raw 없음  diag6={diag.get((code,qq,6))}  master6={master.get((code,qq,6))}")
        continue
    nm = dirs[0].name.split("_", 1)[1]
    wf, src = B.waterfall_for_dir(dirs[0], nm)
    print(f"  {code} {nm} {qq}: diag6={diag.get((code,qq,6))}  현재코드재추출6={(wf or {}).get(6)}  "
          f"master6={master.get((code,qq,6))}  src={src}")
