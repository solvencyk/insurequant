import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from src.ifrs17.measurement_extractor import _score_table, _first_col_labels

xml_path = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명/xml/20230515002900.xml"
company_name = "미래에셋생명"

tables = list(_iter_tables_with_context(xml_path))
print(f"total tables in file: {len(tables)}")

scored = []
for t in tables:
    score, block_type, slice_label, slice_policy, reasons = _score_table(t, company_name)
    scored.append((score, block_type, slice_label, t))

scored.sort(key=lambda x: -x[0])
print("\nTop 15 by score:")
for score, block_type, slice_label, t in scored[:15]:
    labels = _first_col_labels(t.rows)
    print(f"\nscore={score} type={block_type} slice={slice_label} line={t.line_no}")
    print(f"  caption: {(t.caption or '')[:120]!r}")
    print(f"  row_labels[:8]: {labels[:8]}")

print("\n\nTables whose caption OR row-labels mention 보험계약마진 or 측정요소 or CSM-ish terms:")
for score, block_type, slice_label, t in scored:
    labels = _first_col_labels(t.rows)
    hay = (t.caption or "") + " " + " ".join(labels)
    if "보험계약마진" in hay or "측정요소" in hay or "이행현금흐름" in hay or "위험조정" in hay:
        print(f"\nscore={score} type={block_type} slice={slice_label} line={t.line_no}")
        print(f"  caption: {(t.caption or '')[:150]!r}")
        print(f"  row_labels: {labels}")
        print(f"  header: {t.header}")
