# -*- coding: utf-8 -*-
"""a08 (read-only): freeze the selection result of the CURRENT builder code for EVERY data/dart/extracted/*_csm.json
(all companies, all filings): which block `_pick_amort_block` picks (line_no, source) and the full result of
`extract_amort_schedule` (status, caption, unit, buckets, yearly, granularity ...).

    a08_selection_snapshot.py before     -> a08_selection_before.json   (run with the unmodified builder)
    a08_selection_snapshot.py after      -> a08_selection_after.json    (run with the fixed builder)
    a08_selection_snapshot.py diff       -> a08_selection_diff.json + console table (every file whose pick or result moved)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402


def snapshot() -> dict:
    out = {}
    for company, rcept, path, blocks in iter_files():
        cands = [b for b in blocks if eligible(b)]
        pk = V._pick_amort_block(cands)
        res = V.extract_amort_schedule(blocks, company)
        out[path.name] = {
            "company": company, "rcept": rcept, "n_blocks": len(blocks), "n_eligible": len(cands),
            "pick_line": None if pk is None else pk.get("line_no"),
            "pick_src": None if pk is None else pk.get("_source_xml"),
            "result": res,
        }
    return out


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode in ("before", "after"):
        snap = snapshot()
        (W / f"a08_selection_{mode}.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"{mode}: {len(snap)} files frozen")
        return 0
    if mode == "diff":
        b = json.loads((W / "a08_selection_before.json").read_text(encoding="utf-8"))
        a = json.loads((W / "a08_selection_after.json").read_text(encoding="utf-8"))
        assert b.keys() == a.keys(), "file set differs"
        diff = {}
        for k in b:
            if b[k] != a[k]:
                diff[k] = {"company": b[k]["company"], "rcept": b[k]["rcept"],
                           "pick_before": [b[k]["pick_line"], b[k]["pick_src"]], "pick_after": [a[k]["pick_line"], a[k]["pick_src"]],
                           "result_before": b[k]["result"], "result_after": a[k]["result"]}
        (W / "a08_selection_diff.json").write_text(json.dumps(diff, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"files {len(b)} | moved {len(diff)} | identical {len(b) - len(diff)}")
        for k, d in diff.items():
            rb, ra = d["result_before"] or {}, d["result_after"] or {}
            tb = (rb.get("buckets") or {}).get("total")
            ta = (ra.get("buckets") or {}).get("total")
            print(f"  {d['company']:<18s} {d['rcept']} pick {d['pick_before'][0]} -> {d['pick_after'][0]} | status {rb.get('status')}->{ra.get('status')} | total {tb} -> {ta} | y1 {(rb.get('yearly') or {}).get('y1')} -> {(ra.get('yearly') or {}).get('y1')}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
