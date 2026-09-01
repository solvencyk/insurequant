# -*- coding: utf-8 -*-
"""Full-dataset simulation of match_baseline_value_or_zero(item_name, ...) for every
(company, quarter, item 1-46) using each company's own historical item-name (from the
LIVE master, read-only) against extract_kics_detail_rows(md, quarter) built from that
company's md_inbox file for that quarter.

Run once BEFORE editing kics_disclosure_parser.py (writes _g1_sim_old.json) and once
AFTER (writes _g1_sim_new.json), then diff. Never writes kics_disclosure.json.
"""
from __future__ import annotations
import json, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import build_label_lookups, extract_kics_detail_rows

TAG = sys.argv[1] if len(sys.argv) > 1 else "old"
OUT = REPO / "scripts" / "_probes" / f"_g1_sim_{TAG}.json"

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

# item_name per (code, item_no): prefer the most frequent label used by that company
from collections import Counter
name_by_code_item: dict[tuple[str, int], str] = {}
counters: dict[tuple[str, int], Counter] = {}
for r in rows:
    it = r.get("항목번호")
    if it is None or not str(it).isdigit():
        continue
    it = int(it)
    if it > 46:
        continue
    key = (r["원보험사코드"], it)
    counters.setdefault(key, Counter())[r["항목명"]] += 1
for key, c in counters.items():
    name_by_code_item[key] = c.most_common(1)[0][0]

md_inbox = REPO / "md_inbox"
results = {}
n_files = 0
for period_dir in sorted(md_inbox.glob("FY*_Q?")):
    y, q = period_dir.name[2:6], period_dir.name[-1]
    tq = f"{y}.{q}Q"
    for md_path in sorted(period_dir.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        n_files += 1
        try:
            table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), tq)
        except Exception as e:
            results[f"{code}|{tq}|ERROR"] = str(e)
            continue
        if not table:
            continue
        lookup, core = build_label_lookups(table)
        for it in range(1, 47):
            item_name = name_by_code_item.get((code, it))
            if item_name is None:
                continue
            val = match_baseline_value_or_zero(item_name, lookup, core, table)
            if val is not None:
                results[f"{code}|{tq}|{it}"] = val

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"[{TAG}] files={n_files} result_keys={len(results)} -> {OUT}")
