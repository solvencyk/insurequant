#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), steps 1+2: list the Stage-B notes that say a printed total disagrees with the master in
EVERY unit scale (`total-mismatch`), plus every `identity_fail`.  Such a table produced no observation at all in the first run, so the
master cell it disagrees with was never compared (KR1000 2023.2Q is the example).  Read-only.

Output: data/_derived/bspl_followup_20261011/total_mismatch_notes.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "total_mismatch_notes.json"


def main():
    res = {"total_mismatch": [], "identity_fail": [], "other_notes": []}
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for n in d.get("notes", []):
            if "total-mismatch" in n or "peer-mismatch" in n:
                res["total_mismatch"].append({"code": d["code"], "note": n})
            else:
                res["other_notes"].append({"code": d["code"], "note": n})
        for k, v in (d.get("identity_fail") or {}).items():
            res["identity_fail"].append({"code": d["code"], "key": k, "detail": v})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"total-mismatch notes: {len(res['total_mismatch'])}; identity fails: {len(res['identity_fail'])}; other notes: {len(res['other_notes'])}")
    for r in res["total_mismatch"]:
        print(f"  {r['code']} {r['note']}")
    for r in res["identity_fail"]:
        print(f"  IDFAIL {r['code']} {r['key']} {r['detail']}")


if __name__ == "__main__":
    main()
