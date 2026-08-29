# -*- coding: utf-8 -*-
"""Inspect the exact _score_table() breakdown for KR0079 2023.1Q's roman-numeral
per-product CSM tables (i)사망 etc), to understand precisely why they score below
the min_score=5 threshold in extract_measurement_tables(). Read-only."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.measurement_extractor import _score_table, _iter_tables_with_context

rd = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명"
xml = list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml"))
print(f"xml files: {[x.name for x in xml]}")

lines = []
for x in xml:
    for t in _iter_tables_with_context(x):
        cap = t.caption or ""
        if "사망" in cap or "보험계약" in cap and ("i)" in cap or "I)" in cap):
            score, block_type, slice_label, slice_policy, reasons = _score_table(t, "미래에셋생명")
            if score < 2:
                continue
            lines.append(f"line={t.line_no} score={score} block_type={block_type} slice={slice_label}/{slice_policy}")
            lines.append(f"  caption: {cap!r}")
            lines.append(f"  reasons: {reasons}")
            hdr_flat = " | ".join(" ".join(str(c) for c in row) for row in (t.header or []))
            lines.append(f"  header: {hdr_flat[:250]}")
            lines.append("")

out = ROOT / "scripts/_probes/_out_20260830_kr0079_2023q1_score_detail.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out} ({len(lines)} lines)")
