# -*- coding: utf-8 -*-
"""Sweep ALL company x quarter raw dirs (SONBO list) to enumerate which ones use:
  (P1) WIDE single-table product-segmented CSM format (find_product_segmented_csm_cols
       returns non-empty for some block) -- Bug A (item5 label) territory.
  (P2) per-product SEPARATE-BLOCK format with Roman-numeral captions (i)/ii)/iii)/iv)/v)
       matching >=2 of the _PROD_KW hard keywords among distinct CANDIDATE blocks in one
       dir -- Bug B (_PROD_KW 'prod' filter excludes trailing '기타') territory.
Read-only: only imports blocks_for_dir/block_stages/_ns/_PROD_KW-equivalent constants.
No main()/build_csm_waterfall_master.py execution.
"""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages, _ns, SONBO, META, quarter_from
from viz_build_csm_waterfall import find_product_segmented_csm_cols, _count_product_columns, STAGE_PATTERNS

_PROD_KW = ("사망", "건강", "연금", "저축", "종신", "보장", "상해")
_EXCLUDE_KW = ("재보험", "출재", "보유한재보험", "관계기업", "종속기업", "관계종속", "공동기업")

lines = []
p1_hits = []  # (kr, name, quarter, n_wide_blocks)
p2_hits = []  # (kr, name, quarter, prodkw_cand_captions)

for kr in SONBO:
    name, ticker, sb = META.get(kr, (kr, None, None))
    dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()),
                  key=lambda rd: (lambda m: (int(m.group(1)), int(m.group(2))) if m else (0, 0))(
                      re.search(r"FY(\d{4})_Q(\d)", str(rd))))
    for rd in dirs:
        q = quarter_from(rd)
        if not q:
            continue
        try:
            blocks = blocks_for_dir(rd, name)
        except Exception as e:
            lines.append(f"[ERROR] {kr} {q}: {e!r}")
            continue

        # P1: WIDE single-table product-segmented format
        n_wide = 0
        for b in blocks:
            hdr = b.get("header") or []
            rows = b.get("rows") or []
            try:
                cols = find_product_segmented_csm_cols(hdr, rows)
            except Exception:
                cols = []
            if cols:
                n_wide += 1
        if n_wide:
            p1_hits.append((kr, name, q, n_wide))

        # P2: per-product SEPARATE-BLOCK format (Roman-numeral captions hitting
        # >=2 distinct _PROD_KW hard keywords among block_stages()-viable cands,
        # mirroring pick_combined_agnostic's own cand-building gate)
        prodkw_caps = []
        for b in blocks:
            cap = b.get("caption") or ""
            header_txt = " ".join(" ".join(str(c) for c in row) for row in (b.get("header") or []))
            ctx = _ns(cap) + _ns(header_txt)
            if any(k in ctx for k in _EXCLUDE_KW):
                continue
            capn = _ns(cap)
            if not any(kw in capn for kw in _PROD_KW):
                continue
            st = block_stages(b)
            if st and st.get(1) is not None and st.get(6) is not None and (
                    st.get(2) is not None or st.get(5) is not None):
                prodkw_caps.append(cap)
        distinct_kw = sum(1 for kw in _PROD_KW if any(kw in _ns(c) for c in prodkw_caps))
        if distinct_kw >= 2:
            p2_hits.append((kr, name, q, prodkw_caps))

lines.append("=" * 70)
lines.append("P1: WIDE single-table product-segmented format (find_product_segmented_csm_cols hits)")
lines.append("=" * 70)
by_company = {}
for kr, name, q, n in p1_hits:
    by_company.setdefault((kr, name), []).append((q, n))
for (kr, name), qs in by_company.items():
    lines.append(f"  {kr} {name}: {', '.join(f'{q}(n={n})' for q, n in qs)}")

lines.append("")
lines.append("=" * 70)
lines.append("P2: per-product SEPARATE-BLOCK format (>=2 distinct _PROD_KW captions among cands)")
lines.append("=" * 70)
by_company2 = {}
for kr, name, q, caps in p2_hits:
    by_company2.setdefault((kr, name), []).append((q, caps))
for (kr, name), qs in by_company2.items():
    lines.append(f"  {kr} {name}:")
    for q, caps in qs:
        lines.append(f"    {q}: {caps}")

out_path = ROOT / "scripts/_probes/_out_20260830_sweep_product_format_universe.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}")
print(f"P1 companies: {len(by_company)} , P2 companies: {len(by_company2)}")
print(f"P1 total company-quarters: {len(p1_hits)} , P2 total company-quarters: {len(p2_hits)}")
