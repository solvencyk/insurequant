# -*- coding: utf-8 -*-
"""행 귀속 검사기 캘리브레이션 — 참 케이스 / 음성 대조군을 게이트 함수로 직접 돌린다."""
import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
spec = importlib.util.spec_from_file_location("vkd", ROOT / "scripts" / "validate_kics_disclosure.py")
vkd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vkd)

Q3_75 = "data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf"
CASES = [
 (1, "data/disclosure/FY2025_Q4/raw/KR0032_NH농협손해보험.pdf", [46], "해약환급금", "447,254"),
 (1, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "해약환급금", "1,543,723"),
 (1, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "보완자본 한도 적용 전", "1,210,705"),
 (1, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "보완자본 한도", "1,210,705"),
 (1, Q3_75, [15, 16], "보완자본 한도 적용 전", "31,614"),
 (1, Q3_75, [15, 16], "보완자본", "33,067"),
 (1, "data/disclosure/FY2024_Q3/raw/KR0032_NH농협손해보험_amended.pdf", [12, 13], "해약환급금", "886,613"),
 (1, "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", [16, 17], "기본자본", "△165,099"),
 (1, "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", [16, 17], "지급여력금액", "△165,099"),
 (1, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "기본자본", "8,034"),
 (1, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "지급여력금액", "25,846"),
 (1, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "보완자본 한도", "9,385"),
 # --- 음성 대조군 (거짓 귀속 주장은 반증돼야 한다) ---
 (0, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "해약환급금", "1,210,705"),
 (0, "data/disclosure/FY2025_Q4/raw/KR0032_NH농협손해보험.pdf", [46], "보완자본 한도", "447,254"),
 (0, Q3_75, [15, 16], "보완자본 한도", "33,067"),
 (0, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "보완자본", "8,034"),
 (0, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "지급여력금액", "8,034"),
 (0, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "기본자본", "25,846"),
 (0, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "해약환급금", "9,385"),
]
bad = 0
for exp, pdf, pg, row, val in CASES:
    hit, d = vkd._row_anchor_check(ROOT / pdf, pg, row, val)
    ok = (hit == bool(exp))
    bad += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} 기대{'O' if exp else 'X'} 실제{'O' if hit else 'X'} "
          f"minΔ={d if d is None else round(d,2)}  '{row}' <- {val:>12s}  {Path(pdf).name[:24]}")
print(f"\n캘리브레이션 {len(CASES) - bad}/{len(CASES)} (band={vkd._ROW_ANCHOR_BAND})")
sys.exit(1 if bad else 0)
