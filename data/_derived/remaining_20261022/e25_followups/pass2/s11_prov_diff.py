# -*- coding: utf-8 -*-
"""READ-ONLY: show how the 3 provenance blocks flagged by p2_apply --verify differ between the live sidecar and the sandbox emitter output (live rows + live gold)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import p2_apply as A
live_rows = A.load_json(A.F["PL"])
gold = A.load_json(A.F["GOLD"])
sub = [r for r in live_rows if r["원보험사코드"] in A.CODES]
emit = A.run_emitter(sub, gold, "peek")
live_prov = A.load_json(A.F["PROV"])
lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"]}
ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit["cells"]}
for k in [("KR0009", "2023.1Q", "income_statement"), ("KR0009", "2023.2Q", "income_statement"), ("KR0032", "2023.2Q", "income_statement")]:
    print(k)
    a, b = lk[k], ek[k]
    for kk in sorted(set(a) | set(b)):
        if a.get(kk) != b.get(kk):
            print("   ", kk, "SIDECAR:", json.dumps(a.get(kk), ensure_ascii=False)[:300], "| EMITTER:", json.dumps(b.get(kk), ensure_ascii=False)[:300])
