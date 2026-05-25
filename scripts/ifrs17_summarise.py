# -*- coding: utf-8 -*-
"""Pretty-print the batch_all summary into the categories used in the
report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY = REPO_ROOT / "data" / "ifrs17" / "extracted" / "_batch_all_summary.json"


def main():
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    poc5 = ["메리츠화재해상보험", "삼성화재해상보험", "DB손해보험",
            "한화생명", "삼성생명보험"]

    print("\n=== P1: 5-company PoC ===")
    for name in poc5:
        r = next((x for x in data if x.get("kics_name") == name), None)
        if not r:
            print(f"  {name:20s} (not in batch)")
            continue
        print(f"  {name:20s} status={r['status']:25s} "
              f"tables={r.get('csm_tables_found', '-')!s:>3} "
              f"forms={r.get('form_type_counts', {})}")

    print("\n=== P2: 37 K-ICS insurers — bucketed ===")
    by_status: dict[str, list[str]] = {}
    for r in data:
        by_status.setdefault(r["status"], []).append(r["kics_name"])
    for s in ["ok", "no_csm_table_found", "no_annual_filing",
              "no_corp_match", "exception"]:
        names = by_status.get(s, [])
        if not names:
            continue
        print(f"\n  [{s}]  ({len(names)})")
        for n in names:
            r = next(x for x in data if x.get("kics_name") == n)
            extra = ""
            if s == "ok":
                extra = (f"  tables={r.get('csm_tables_found')}  "
                         f"forms={r.get('form_type_counts')}")
            elif s != "no_corp_match":
                extra = f"  canonical={r.get('canonical', '-')!r}"
            print(f"    - {n}{extra}")

    ok = sum(1 for r in data if r["status"] == "ok")
    print(f"\n[headline] ok={ok}/{len(data)} = "
          f"{ok / len(data) * 100:.1f}%")


if __name__ == "__main__":
    main()
