"""Root-cause isolation: is the label-value row misalignment (found in the 별도/OFS-tagged
table candidates for KR0079 2025.4Q, via the PRODUCTION path _iter_tables_by_basis which
physically cuts the main XML in half at the 연결/별도 ATOC boundary and re-parses each half as
an independent HTML fragment) an artifact of THAT SPLIT-AND-REPARSE workaround, or is it
present even when the SAME bytes are parsed as one whole document (no split)?

Method: parse the FULL, UNCUT main xml with _iter_tables_with_context directly (bypassing
_iter_tables_by_basis/_tag_basis entirely), locate the same 4 candidate tables by content
anchor, and check whether the LATER two (which the split path reports as line_no=65535,
shifted) come out AlIGNED when parsed in one pass. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _ofs_line_boundary  # noqa: E402

XML = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664/20260318001664.xml"

boundary = _ofs_line_boundary(XML)
print(f"_ofs_line_boundary({XML.name}) = {boundary}  (file has 127,045 lines; cap=65535)")

# Parse the WHOLE file in ONE pass (no split, no temp files) -- this is the "control" to
# compare against the production split-and-reparse path.
tables_unsplit = list(_iter_tables_with_context(XML))
print(f"\ntotal tables (single-pass, unsplit): {len(tables_unsplit)}")

cands = [t for t in tables_unsplit
         if "자산인 보험계약의 기초 장부금액" in "".join(r[0] if r else "" for r in t.rows)
         and any("발생한 보험금 및 기타 보험서비스비용" in "".join(r[:2]) for r in t.rows)]
print(f"candidate tables (unsplit, by content anchor): {len(cands)}")

for i, t in enumerate(cands):
    print(f"\n{'='*100}\nUNSPLIT candidate #{i}  line_no={t.line_no}")
    for r in t.rows:
        lab = r[0] if r else ""
        lab2 = r[1] if len(r) > 1 else ""
        if lab in ("자산인 보험계약의 기초 장부금액", "부채인 보험계약의 기초 장부금액", "보험수익") \
                or "발생한 보험금" in (lab2 or lab) or "보험취득현금흐름 상각" == lab \
                or "발생사고요소의 조정" == lab or lab in ("자산인 보험계약의 기말 장부금액", "부채인 보험계약의 기말 장부금액"):
            print(f"  [{lab!r}|{lab2!r}]: {r[2:] if lab2 else r[1:]}")
