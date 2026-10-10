# -*- coding: utf-8 -*-
"""Schema parity check of the staged reinsurer rows against the existing master rows (read only).

For each of the three masters: field order, value types per field, and the value domain of the categorical fields must be
consistent between the existing rows and the staged ones.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_reinsurer_csm_schema_check.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")

PAIRS = [
    ("CSM_amortization.json", "rows_amortization.json"),
    ("CSM_sensitivity.json", "rows_sensitivity.json"),
    ("CSM_waterfall.json", "rows_waterfall.json"),
]


def tname(v):
    return type(v).__name__


def main() -> int:
    ok = True
    for master, staged in PAIRS:
        ex = json.loads((ROOT / master).read_text(encoding="utf-8"))
        st = json.loads((STAGE / staged).read_text(encoding="utf-8"))
        ex_orders = Counter(tuple(r.keys()) for r in ex)
        st_orders = Counter(tuple(r.keys()) for r in st)
        print(f"== {master}: existing {len(ex)} rows, staged {len(st)} rows")
        print("   existing key orders:", {tuple(k): v for k, v in ex_orders.items()})
        print("   staged key orders  :", {tuple(k): v for k, v in st_orders.items()})
        if set(st_orders) - set(ex_orders):
            ok = False
            print("   !! staged key order not among existing key orders")
        # types per field
        types_ex, types_st = {}, {}
        for r in ex:
            for k, v in r.items():
                types_ex.setdefault(k, set()).add(tname(v))
        for r in st:
            for k, v in r.items():
                types_st.setdefault(k, set()).add(tname(v))
        for k in types_st:
            extra = types_st[k] - types_ex.get(k, set())
            if extra:
                # int vs float is normal for numbers; report anything else
                if not ({"int", "float"} >= (types_st[k] | types_ex.get(k, set())) and types_ex.get(k)):
                    ok = False
                print(f"   type note field {k}: existing {sorted(types_ex.get(k, []))} staged {sorted(types_st[k])}")
        # categorical domains
        for fld in ("원보험사코드", "공시분기", "항목번호", "경과차년", "순번", "위험구분", "충격수준", "기준일", "단위", "항목명", "구분"):
            if fld in (st[0] if st else {}):
                dom_st = Counter(r.get(fld) for r in st)
                dom_ex = Counter(r.get(fld) for r in ex)
                if len(dom_st) <= 14:
                    print(f"   {fld}: staged {dict(sorted(dom_st.items(), key=lambda kv: str(kv[0])))}")
                new_vals = set(dom_st) - set(dom_ex)
                if fld in ("항목번호", "경과차년", "순번", "위험구분", "충격수준", "단위", "항목명") and new_vals:
                    print(f"   NOTE {fld}: staged-only values (not used by existing rows): {sorted(map(str, new_vals))}")
        # nulls
        nulls = Counter(k for r in st for k, v in r.items() if v is None)
        print("   null fields in staged:", dict(nulls))
        nulls_ex = Counter(k for r in ex for k, v in r.items() if v is None)
        print("   null fields in existing:", dict(nulls_ex))
    print("PARITY OK" if ok else "PARITY ISSUES -- see notes above")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
