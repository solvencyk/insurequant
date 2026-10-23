# -*- coding: utf-8 -*-
"""read-only: the two side-output files of the master_tables golden test (data/_derived/qoq_warn.json, pl_oci_vs_bs_aoci_warn.json): live vs the pre-load backup -- which rows were added / removed / changed"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"
for rel in ("data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"):
    a = json.loads((BK / rel).read_text(encoding="utf-8"))
    b = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    print("==", rel, "type", type(a).__name__, "top keys", list(a.keys())[:8] if isinstance(a, dict) else len(a))
    la = a if isinstance(a, list) else next((v for v in a.values() if isinstance(v, list)), None)
    lb = b if isinstance(b, list) else next((v for v in b.values() if isinstance(v, list)), None)
    if isinstance(a, dict):
        for k in a:
            if not isinstance(a[k], list) and a[k] != b.get(k):
                print("   scalar key changed:", k, a[k], "->", b.get(k))
    print("   rows", len(la), "->", len(lb))

    def key(r):
        return tuple(str(r.get(k)) for k in ("company", "code", "원보험사코드", "원수사명", "quarter", "공시분기", "item", "항목번호", "항목", "name") if k in r)

    da, db = {key(r): r for r in la}, {key(r): r for r in lb}
    add, rem = sorted(set(db) - set(da)), sorted(set(da) - set(db))
    chg = sorted(k for k in da if k in db and da[k] != db[k])
    print("   added", len(add), "removed", len(rem), "changed", len(chg))
    for k in add[:12]:
        print("      +", json.dumps(db[k], ensure_ascii=False)[:230])
    for k in rem[:12]:
        print("      -", json.dumps(da[k], ensure_ascii=False)[:230])
    for k in chg[:12]:
        print("      ~", json.dumps(da[k], ensure_ascii=False)[:150], "=>", json.dumps(db[k], ensure_ascii=False)[:150])
