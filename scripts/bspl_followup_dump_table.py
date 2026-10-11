#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17): dump the Stage-A table rows of one (company, quarter) (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_dump_table.py KR1000 2023.3Q [kind] [--audit]

kind = sum_bs | equity | bs_full | sum_pl | pl_full (default: all).  Prints page, unit, basis and each row's raw label,
canonical label (views.canon) and aligned values.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, canon  # noqa: E402


def main():
    code, q = sys.argv[1], sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
    doc = B.load_tables(code, q)
    if doc is None:
        print("no tables")
        return
    print("pdf:", doc.get("pdf"), "audit_pdf:", doc.get("audit_pdf"), "pages:", doc.get("pages"))
    for t in doc["tables"]:
        if kind and t["kind"] != kind:
            continue
        print("=" * 110)
        print(f"kind={t['kind']} page={t['page']} npages={t.get('npages')} unit={t.get('unit')} basis={t.get('basis')} src={t.get('src')} titles={t.get('titles')}")
        fam = "pl" if t["kind"] in ("sum_pl", "pl_full") else "bs"
        va = view_all(t)
        # map rows (by id) -> aligned row from the view
        aligned = {}
        for c, rows in va.items():
            for r in rows:
                aligned[(r["page"], r["y"], r["label"])] = (c, r)
        for r in t["rows"]:
            key = (r["page"], r["y"], r["label"])
            cn = canon(r["label"], fam)
            if key in aligned:
                c, ar = aligned[key]
                vals = [("-" if d else ("?" if (ar.get("unsure") and ar["unsure"][i]) else v)) for i, (v, d) in enumerate(zip(ar["vals"], ar["dash"]))]
                print(f"  p{r['page']} y{r['y']:<7} {r['label'][:46]:<46} [{c}] {vals}")
            else:
                print(f"  p{r['page']} y{r['y']:<7} {r['label'][:46]:<46} [{cn}] raw={r['vals']} dash={r['dash']}")


if __name__ == "__main__":
    main()
