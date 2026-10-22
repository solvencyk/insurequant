#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 14: provenance blocks of the 11 target companies that the emitter does NOT reproduce, before (backup state) and after (live state) the apply.
Expectation: after-set is a subset of the before-set (pre-existing), and no block of an adopted (company, quarter) is in it."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_apply as A  # noqa: E402  (module import only; main() is not run)

sys.stdout.reconfigure(encoding="utf-8")
BK = A.BACKUP
ROOT = A.ROOT


def nonrepro(rows, gold, prov, tag):
    sub = [r for r in rows if r["원보험사코드"] in A.CODES]
    emit = A.run_emitter(sub, gold, tag)
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in prov["cells"] if c["company_code"] in A.CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit["cells"] if c["company_code"] in A.CODES}
    return {k for k in lk if lk[k] != ek.get(k)}, len(lk)


before_rows = json.loads((BK / "PL_breakdown.json").read_text(encoding="utf-8"))
before_gold = json.loads((BK / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
before_prov = json.loads((BK / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
after_rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
after_gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
after_prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
nb, nb_all = nonrepro(before_rows, before_gold, before_prov, "nr_before")
na, na_all = nonrepro(after_rows, after_gold, after_prov, "nr_after")
adopted = set(A.ADOPTED)
print(f"before: {len(nb)}/{nb_all} blocks not reproduced; after: {len(na)}/{na_all}")
print("after subset of before:", na <= nb, "| new non-reproduced after:", sorted(na - nb))
print("non-reproduced after that belong to an adopted (company, quarter):", sorted(k for k in na if (k[0], k[1]) in adopted))
print("fixed by the apply (before only):", sorted(nb - na))
print("after list:", sorted(na))
