# -*- coding: utf-8 -*-
"""pass3 s06 (read-only): exact ABL numbers for the answer: live master after the load, closure of derived 7 / 12 against the other note rows, subtotal checks of the cumulative and 3-month columns"""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
abl = json.load(open(f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass3/kr0070_abl/r10_abl_cur_read.json", encoding="utf-8"))
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
n_ok = n_all = 0
for q in ("2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"):
    rec = abl[q]
    v = {i: live[(q, i)]["값"] for i in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12)}
    d7 = v[7] - rec["closure7"]["value"]
    d12 = v[12] - rec["closure12"]["value"]
    ident3 = v[3] - (v[4] + v[5] + v[6] + v[7])
    ident8 = v[8] - (v[9] + v[10] + v[11] + v[12])
    print(q, "7 =", v[7], "other rows", rec["closure7"]["value"], "diff %+.3f" % d7, "| 12 =", v[12], "other rows", rec["closure12"]["value"], "diff %+.3f" % d12, "| ident 3: %.6f 8: %.6f" % (ident3, ident8))
    for key in ("subtotal_check_cur_cum", "subtotal_check_cur_3m"):
        if key in rec:
            for name, (s, t, n) in rec[key].items():
                n_all += 1
                ok = abs(s - t) <= 1.5
                n_ok += ok
                print("   ", key, name, s, t, "OK" if ok else "DIFF")
    print("    note 3:", rec["i3_note"], "master 3:", v[3], "| note 8:", rec["i8_note"], "master 8:", v[8])
print("subtotal checks", n_ok, "/", n_all)
