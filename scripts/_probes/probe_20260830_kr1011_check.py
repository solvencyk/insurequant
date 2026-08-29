# -*- coding: utf-8 -*-
"""Check whether KR1011 (IBK연금보험) 2025.4Q genuinely hits pick_combined_agnostic's
'seg'/_PROD_KW prod-list path (Bug B shape) or is a false positive of the P2 sweep
heuristic (a single caption mentioning both '연금' and '저축' words without being a
Roman-numeral per-product-block group). Read-only.
"""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages, _ns, META, quarter_from

_EXCLUDE_KW = ("재보험", "출재", "보유한재보험", "관계기업", "종속기업", "관계종속", "공동기업")
_PROD_KW = ("사망", "건강", "연금", "저축", "종신", "보장", "상해")

kr = "KR1011"
name = META.get(kr, (kr, None, None))[0]
print("name:", name)
dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()))
for rd in dirs:
    q = quarter_from(rd)
    if q != "2025.4Q":
        continue
    blocks = blocks_for_dir(rd, name)
    print(f"{q} ({rd.name}) -- {len(blocks)} blocks")
    for i, b in enumerate(blocks):
        cap = b.get("caption") or ""
        ctx = _ns(cap) + _ns(" ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
        if any(k in ctx for k in _EXCLUDE_KW):
            continue
        capn = _ns(cap)
        if not any(kw in capn for kw in _PROD_KW):
            continue
        st = block_stages(b)
        print(f"  block {i} cap={cap!r}")
        print(f"    st={st}")
