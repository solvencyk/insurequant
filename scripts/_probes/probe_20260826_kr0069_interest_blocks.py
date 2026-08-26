#!/usr/bin/env python3
"""KR0069 (삼성생명) item3(이자 부리)/item4 검산 — 상품라인 블록별 raw 값 덤프.

inbox/parser/20260826T0500Z ① 검증용. read-only (waterfall_for_dir / blocks_for_dir import).
"""
import sys, re, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from viz_build_csm_waterfall import row_value_start, parse_num, filter_current_period_rows

QS = ["FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1"]
NAME = "삼성생명"

def ns(s):
    return re.sub(r"\s", "", s) if isinstance(s, str) else ""

for q in QS:
    dirs = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))
    for rd in dirs:
        print("=" * 100)
        print(f"### {q}  {rd.name}")
        blocks = B.blocks_for_dir(rd, NAME)
        print(f"blocks={len(blocks)}")
        for i, b in enumerate(blocks):
            cap = (b.get("caption") or "")[:70]
            st = B.block_stages(b)
            hit = []
            for r in (b.get("rows") or []):
                lab = ns("".join(str(c) for c in r[:row_value_start(r)] if isinstance(c, str)))
                if "순보험금융손익" in lab or "환율변동" in lab or "보험금융손익" in lab:
                    data = r[row_value_start(r):]
                    nums = [parse_num(x) for x in data]
                    hit.append((lab[:34], [n for n in nums]))
            if not hit and not st:
                continue
            print(f"--- block[{i}] src={b.get('_src','')} basis={b.get('basis')} cap={cap!r}")
            if st:
                print(f"    stages: " + " ".join(f"{k}={st.get(k)}" for k in (1,2,3,5,6)))
            for lab, nums in hit:
                print(f"    row {lab!r}: {nums}")
        wf, src = B.waterfall_for_dir(rd, NAME)
        print(f">>> waterfall_for_dir: " + (" ".join(f"{k}={wf.get(k)}" for k in (1,2,3,4,5,6)) if wf else "None") + f"   src={src}")
