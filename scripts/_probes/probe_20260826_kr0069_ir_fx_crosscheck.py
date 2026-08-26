#!/usr/bin/env python3
"""FX 규약 외부 확증: FY2025_Q4 / FY2026_Q2 raw 재추출을 IR 팩트시트와 대조.
환율 가산(현재 코드) vs 환율 제외 중 어느 쪽이 IR 이자부리와 맞는가."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from viz_build_csm_waterfall import row_value_start

_orig = B.block_stages
def _strip_fx(b):
    nb = dict(b)
    nb["rows"] = [r for r in (b.get("rows") or [])
                  if "환율변동" not in "".join(str(c) for c in r[:row_value_start(r)] if isinstance(c, str))]
    return nb

for q, irf in [("FY2025_Q4", "data/ir/FY2025_Q4/parsed/KR0069.json"),
               ("FY2026_Q2", "data/ir/FY2026_Q2/parsed/KR0069.json"),
               ("FY2026_Q1", None)]:
    dirs = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))
    if not dirs:
        print(f"{q}: raw 없음"); continue
    rd = dirs[0]
    wf_fx, _ = B.waterfall_for_dir(rd, "삼성생명")
    B.block_stages = lambda b: _orig(_strip_fx(b))
    try:
        wf_no, _ = B.waterfall_for_dir(rd, "삼성생명")
    finally:
        B.block_stages = _orig
    ir = json.load(open(ROOT / irf, encoding="utf-8"))["csm_waterfall"]["interest"] if irf else None
    print(f"{q}: raw(환율가산)={(wf_fx or {}).get(3)}  raw(환율제외)={(wf_no or {}).get(3)}  IR이자부리={round(ir,2) if ir else None}")
