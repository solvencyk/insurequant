# -*- coding: utf-8 -*-
"""Prove: after the 4 sheet syncs, every old row survives; only expected cells changed; others sheets identical."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
before = json.loads((D / "xlsx_before.json").read_text(encoding="utf-8"))
after = json.loads((D / "xlsx_after.json").read_text(encoding="utf-8"))
KEYCOLS = {  # number of leading identity columns (header order in each sheet)
    "손익분해PL": 7, "17BS": 9, "CSM워터폴": 7, "CSM상각": 6, "가정민감도": 10, "보험계약부채": 12, "신계약CSM배수": 5,
}
for name in before:
    b, a = before[name], after[name]
    if name in KEYCOLS:
        k = KEYCOLS[name]
        hb = json.loads(b["rows"][0]); ha = json.loads(a["rows"][0])
        assert hb == ha, (name, "header changed")
        def idx(rows):
            d = {}
            for r in rows[1:]:
                v = json.loads(r)
                key = tuple(str(x) for x in v[:k])
                assert key not in d, (name, "dup key", key)
                d[key] = v
            return d
        ib, ia = idx(b["rows"]), idx(a["rows"])
        removed = [x for x in ib if x not in ia]
        added = [x for x in ia if x not in ib]
        cells = 0
        edits_by_company = {}
        for key, v in ib.items():
            if key in ia and ia[key] != v:
                n = sum(1 for x, y in zip(v, ia[key]) if x != y)
                cells += n
                edits_by_company[key[0]] = edits_by_company.get(key[0], 0) + n
        add_by_company = {}
        for x in added:
            add_by_company[x[0]] = add_by_company.get(x[0], 0) + 1
        print(f"{name}: rows {b['n']-1} -> {a['n']-1} | removed {len(removed)} | added {len(added)} {add_by_company} | changed cells in kept rows {cells} {edits_by_company}")
        # changed cells that were not None before (value->value)
        vv = 0
        for key, v in ib.items():
            if key in ia and ia[key] != v:
                vv += sum(1 for x, y in zip(v, ia[key]) if x != y and x is not None)
        print(f"    of which value->value (old not blank): {vv}")
    else:
        same = b["sha"] == a["sha"]
        print(f"{name}: rows {b['n']} -> {a['n']} {'IDENTICAL' if same else 'DIFFERENT'}")
