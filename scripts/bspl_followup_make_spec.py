#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert a file of loadable BS cells in the Stage-B manual schema (cells[] with code/item/quarter/value_mn/unit/page/pdf/sha256/basis/...)
into the spec the applier consumes (bspl_followup_apply_bs_fix.py): every cell is an `add` (new key; existing keys are never touched here).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_make_spec.py <cells.json> <out_spec.json> [--method NAME]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
SCALE = {"원": "원 -> 백만원", "천원": "천원 -> 백만원", "백만원": "백만원 -> 백만원", "억원": "억원 -> 백만원"}


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    method = sys.argv[sys.argv.index("--method") + 1] if "--method" in sys.argv else "followup:stage_c"
    d = json.loads(src.read_text(encoding="utf-8"))
    idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))}
    cells, skipped = [], 0
    for c in d["cells"]:
        k3 = (c["code"], c["item"], c["quarter"])
        if k3 in idx:
            skipped += 1                    # already in the master (loaded by an earlier step): never touched
            continue
        cells.append({"key": f"{c['code']}|{c['item']}|{c['quarter']}", "item": c["item"], "quarter": c["quarter"], "action": "add", "old": None,
                      "new": round(c["value_mn"], 6), "line": c.get("rule"), "pdf": c.get("pdf"), "page": c.get("page"), "pdf_sha256": c.get("sha256"),
                      "basis": c["basis"], "method": f"{method}:{c.get('calib')}:{c.get('kind')}:{c.get('rule')}", "scale": SCALE.get(c.get("unit"), "원 -> 백만원")})
    dst.write_text(json.dumps({"cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{src.name}: {len(d['cells'])} cells -> {len(cells)} add-spec cells ({skipped} already in master) -> {dst.name}")


if __name__ == "__main__":
    main()
