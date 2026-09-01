# -*- coding: utf-8 -*-
import sys, io, json
sys.path.insert(0, "scripts")
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fill_period_to_disclosure as F
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows, build_label_lookups
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero

fields = F._fields()
rows = json.loads(F.JSON_PATH.read_text(encoding="utf-8"))

tq = "2023.1Q"
bq = F._quarter_prior(tq)
print(f"tq={tq} bq={bq}")
baseline = F._baseline_for_company(rows, "KR0049", tq, bq, fields)
b_items = sorted({int(b["항목번호"]) for b in baseline if str(b["항목번호"]).isdigit()})
print(f"baseline items: {b_items}")
b25 = [b for b in baseline if str(b["항목번호"]) == "25"]
print(f"item25 in baseline: {b25}")

md_path = F.MD_INBOX / "FY2023_Q1" / "KR0049_악사손해보험.md"
print("md exists:", md_path.exists())
table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), tq)
print(f"table rows: {len(table) if table else 0}")
if table:
    for label, raw in table:
        if "비례성" in label or "대응" in label or "대용" in label:
            print(f"  ROW: label={label!r} raw={raw!r}")
    lookup, core = build_label_lookups(table)
    if b25:
        val = match_baseline_value_or_zero(b25[0]["항목명"], lookup, core, table)
        print(f"match_baseline_value_or_zero({b25[0]['항목명']!r}) = {val!r}")
