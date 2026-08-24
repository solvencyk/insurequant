"""Read-only: independently re-verify the KR0097 2024.4Q raw claims from the
2026-08-24 reaudit report before trusting them. Dumps p281 (item17 table),
p296 (life-8 subrisk before-only table), p326 (initial-amount / phase-in
table), and a scan of p340-355 for any after-column marker, to a UTF-8 file
(console is cp949 and mangles Korean).

Usage: python probe_20260824b_kr0097_raw_verify.py <out_txt_path>
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
pdf_path = ROOT / "data/disclosure/FY2024_Q4/raw/KR0097_하나생명보험.pdf"
out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch_kr0097_verify.txt"

doc = fitz.open(pdf_path)
lines = []
lines.append(f"file={pdf_path.name} pages={doc.page_count}")
texts = [doc[i].get_text() for i in range(doc.page_count)]
total = sum(len(t) for t in texts)
lines.append(f"total_chars={total} avg={total / max(1, doc.page_count):.0f}/p")

for pno in (281, 296, 326):
    lines.append("=" * 100)
    lines.append(f"--- page {pno} (1-base), chars={len(texts[pno - 1])} ---")
    lines.append(texts[pno - 1])

# keyword scan across the whole doc for the two markers the report cites as absent
markers = ["지급여력비율의 경과조치 적용에 관한 사항", "장수위험ㆍ사업비위험ㆍ해지위험 및 대재해위험 경과조치",
           "장수위험ㆍ사업비위험", "장수위험", "적용 후", "경과조치"]
lines.append("=" * 100)
lines.append("marker scan (flattened, no-space substring match):")
for kw in markers:
    flat = kw.replace(" ", "").replace("ㆍ", "")
    hits = [i + 1 for i, t in enumerate(texts) if flat in t.replace(" ", "").replace("ㆍ", "")]
    lines.append(f"  '{kw}': {len(hits)} pages -> {hits[:40]}")

# grep for the two suspect stale values and their candidate correct replacements
grep_targets = ["94,286", "89,615", "942.86", "896.15", "137,771", "1,377.71", "71,473", "714.73",
                 "200,189,811", "200189811", "2,001.9", "2001.9"]
lines.append("=" * 100)
lines.append("value grep across whole doc:")
for g in grep_targets:
    hits = [i + 1 for i, t in enumerate(texts) if g in t]
    lines.append(f"  '{g}': {len(hits)} pages -> {hits[:40]}")

# dump pages around 340-355 to visually confirm no after-column subrisk table
lines.append("=" * 100)
lines.append("pages 340-355 dump (search zone for a possible after-column table):")
for pno in range(340, 356):
    if pno - 1 >= doc.page_count:
        break
    t = texts[pno - 1]
    lines.append(f"--- page {pno}, chars={len(t)} ---")
    lines.append(t[:1500])

doc.close()
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")
