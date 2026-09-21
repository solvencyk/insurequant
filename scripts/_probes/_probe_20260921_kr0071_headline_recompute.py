"""Read-only probe: replay fill_post_transition_to_disclosure.py's internal
extraction for KR0071 (2025.2Q, 2025.4Q) and diff against the current master.

No writes anywhere. Imports the parser script as a module and calls its
private helpers directly instead of running --dry-run's aggregate-only log.
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

spec = importlib.util.spec_from_file_location(
    "fill_post_transition_to_disclosure", REPO / "scripts" / "fill_post_transition_to_disclosure.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

MASTER = REPO / "kics_disclosure.json"

CODE = "KR0071"
CASES = [("FY2025_Q2", "2025.2Q"), ("FY2025_Q4", "2025.4Q")]


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    index = {}
    for r in rows:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    out_report = []
    for period_label, quarter in CASES:
        md_path = REPO / "md_inbox" / period_label / f"{CODE}_흥국생명보험.md"
        text = md_path.read_text(encoding="utf-8")
        tables = mod._scan_tables_with_context(text)
        existing_values = {
            item_no: row.get("값")
            for (c, q, item_no), row in index.items()
            if c == CODE and q == quarter
        }
        post_map, provenance, dbg, unit_fixed_items = mod._extract_post_values(
            tables, CODE, existing_values
        )
        for line in dbg:
            print(line)
        for item_no in sorted(post_map):
            pre_v, post_v = post_map[item_no]
            row = index.get((CODE, quarter, item_no))
            current_post = row.get("값_적용후") if row else None
            entry = {
                "quarter": quarter,
                "item_no": item_no,
                "provenance": provenance.get(item_no),
                "recomputed_pre": pre_v,
                "recomputed_post": post_v,
                "master_current_post": current_post,
                "would_change": str(current_post) != str(post_v),
            }
            out_report.append(entry)
            if entry["would_change"]:
                print("DIFF:", entry)

    with open(
        REPO / "data" / "_derived" / "_probe_20260921_kr0071_headline_recompute.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(out_report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
