#!/usr/bin/env python3
"""트리에 배선한 basis 수정이 census 와 같은 값을 내는지 확인 (monkeypatch 없음)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP
import build_csm_waterfall_master as B

EXP_PL = {"2023.4Q": 1367673, "2024.1Q": 350879, "2024.2Q": 708154, "2024.3Q": 1068763,
          "2025.2Q": 743661, "2026.2Q": 733660}
filings = BP.discover_filings()
print("=== PL (KR0069 원수 CSM상각, 백만원) ===")
ok = True
for q in sorted(filings["KR0069"], key=BP._quarter_sort_key):
    t1, t2 = BP.parse_filing(filings["KR0069"][q], True, code="KR0069", name="삼성생명", quarter=q)
    v = (t2 or {}).get(4)
    exp = EXP_PL.get(q)
    mark = ""
    if exp is not None:
        good = v is not None and abs(v - exp) < 5
        ok &= good
        mark = ("OK" if good else f"MISMATCH exp={exp}")
    print(f"  {q}  item4={None if v is None else round(v,2)}  {mark}")
print()
print("=== CSM (KR0069 2023.4Q) ===")
rd = sorted((ROOT / "data" / "dart" / "FY2023_Q4" / "raw").glob("KR0069_*"))[0]
wf, src = B.waterfall_for_dir(rd, "삼성생명")
print("  ", {i: (wf or {}).get(i) for i in (1, 2, 3, 4, 5, 6)}, src)
exp = {1: 107486.9, 2: 36281.5, 3: 4016.2, 4: -11634.2, 5: -13676.7, 6: 122473.7}
good = wf and all(abs(wf[i] - exp[i]) < 0.05 for i in exp)
print("   별도 census 와 일치:", "OK" if good else "MISMATCH")
print()
print("=== CSM (KR0094 신한라이프 2024.4Q — 특례 없이 72,241.1 나오나) ===")
rd = sorted((ROOT / "data" / "dart" / "FY2024_Q4" / "raw").glob("KR0094_*"))[0]
wf2, src2 = B.waterfall_for_dir(rd, "신한라이프생명보험")
print("  ", {i: (wf2 or {}).get(i) for i in (1, 2, 3, 4, 5, 6)}, src2)
print("   기말 72,241.1:", "OK" if wf2 and abs(wf2[6] - 72241.1) < 0.05 else "MISMATCH")
print()
print("전체:", "OK" if (ok and good) else "확인 필요")
