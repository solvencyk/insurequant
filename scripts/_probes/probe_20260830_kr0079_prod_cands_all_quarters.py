# -*- coding: utf-8 -*-
"""For every KR0079 quarter, reconstruct pick_combined_agnostic's OWN 'cands' list
(same filter: _EXCLUDE_KW on ctx=caption+header, then block_stages() gate requiring
opening+closing+(newbiz or amort)) and print each cand's (caption, stages) IN ORDER --
to confirm the '기타' trailing-adjacency pattern holds across all quarters, and to
measure the exact Bug-B impact (sum of 4 hard-kw blocks vs sum including a trailing
'기타'/그외 block) per quarter. Read-only.
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

kr = "KR0079"
name = META.get(kr, (kr, None, None))[0]
dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()),
              key=lambda rd: (lambda m: (int(m.group(1)), int(m.group(2))) if m else (0, 0))(
                  re.search(r"FY(\d{4})_Q(\d)", str(rd))))

lines = []
for rd in dirs:
    q = quarter_from(rd)
    blocks = blocks_for_dir(rd, name)
    cands = []
    for b in blocks:
        cap = b.get("caption") or ""
        if re.match(r"^\s*(전기|전분기|전반기)", cap):
            pass  # _is_prior_caption/_is_prior_header not reproduced here; informational only
        ctx = _ns(cap) + _ns(" ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
        # combined_net special-case (KB 순보험계약부채+재보험계약자산) doesn't apply to 미래에셋 --
        # use the plain original-exclusion branch only (mirrors the 'else' branch).
        if any(k in ctx for k in _EXCLUDE_KW):
            continue
        if any(isinstance(r, list) and r and isinstance(r[0], str) and "재보험" in r[0]
               for r in (b.get("rows") or [])):
            continue
        st = block_stages(b)
        if st and st.get(1) is not None and st.get(6) is not None and (
                st.get(2) is not None or st.get(5) is not None):
            cands.append((st, _ns(cap), cap))
    lines.append(f"===== {q} ({rd.name}) -- {len(cands)} cands =====")
    for st, capn, cap in cands:
        hard = [kw for kw in _PROD_KW if kw in capn]
        tag = f"HARD:{hard}" if hard else ("ETC" if ("기타" in capn or "그외" in capn or "그 외" in cap) else "")
        lines.append(f"  cap={cap!r:60s} {tag:20s} st={st}")
    lines.append("")

out_path = ROOT / "scripts/_probes/_out_20260830_kr0079_prod_cands_all_quarters.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}")
