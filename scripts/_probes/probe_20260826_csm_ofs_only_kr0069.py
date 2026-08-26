#!/usr/bin/env python3
"""KR0069 2023.4Q CSM 워터폴을 별도(_00760.xml) 블록만으로 재추출 — 기준 혼재 확인."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B

_orig = B.blocks_for_dir
def only(src_sub):
    def f(rd, name):
        return [b for b in _orig(rd, name) if src_sub in (b.get("_src") or "")]
    return f

m = {(r["공시분기"], r["항목번호"]): r["값"]
     for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
     if r["원보험사코드"] == "KR0069"}

for q in ["FY2023_Q4", "FY2024_Q4", "FY2025_Q4"]:
    rd = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))[0]
    qq = q.replace("FY", "").replace("_Q", ".") + "Q"
    print("=" * 100)
    print(f"### {qq}  {rd.name}")
    srcs = sorted({(b.get('_src') or '') for b in _orig(rd, '삼성생명')})
    print("  블록 출처:", srcs)
    for tag, sub in [("전체(현재)", None), ("별도 _00760만", "_00760"), ("본문만", None)]:
        if sub:
            B.blocks_for_dir = only(sub)
        elif tag == "본문만":
            B.blocks_for_dir = lambda rd, name: [b for b in _orig(rd, name)
                                                 if "_007" not in (b.get("_src") or "")]
        else:
            B.blocks_for_dir = _orig
        try:
            wf, src = B.waterfall_for_dir(rd, "삼성생명")
        finally:
            B.blocks_for_dir = _orig
        if not wf:
            print(f"  {tag:14s} -> None  ({src})"); continue
        print(f"  {tag:14s} " + " ".join(f"{i}={wf.get(i)}" for i in (1, 2, 3, 4, 5, 6)) + f"  {src}")
    print(f"  {'마스터':14s} " + " ".join(f"{i}={m.get((qq, i))}" for i in (1, 2, 3, 4, 5, 6)))
