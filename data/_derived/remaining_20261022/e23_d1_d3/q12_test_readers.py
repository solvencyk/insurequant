# -*- coding: utf-8 -*-
"""e23 probe (read-only): run the new e23 PL4 / CSM / IR readers and print the results next to the e20 candidate / vector-source values."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as X  # noqa: E402
import e21_csm2 as C2  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
MEAS = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
vs = {}
with open(MEAS / "csm_vector_sources.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        vs[(r["code"], r["quarter"])] = r["vector_eok"]
which = sys.argv[1:] or ["kblife", "abl", "kdb", "hd", "lotte", "ir"]
SPEC = {"kblife": ("KR0099", ["2023.1Q", "2023.2Q", "2023.3Q"], X.pl4_kblife, X.csm_kblife),
        "abl": ("KR0070", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], X.pl4_abl, X.csm_abl),
        "kdb": ("KR0072", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], X.pl4_kdb, X.csm_kdb),
        "hd": ("KR0009", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], X.pl4_hd, X.csm_hd),
        "lotte": ("KR0003", ["2023.4Q"], None, C2.lotte_csm)}
for key in which:
    if key == "ir":
        for q in ("2023.1Q", "2023.2Q"):
            d = X.hd_ir_legs(q)
            print("IR", q, d["file"], d["header_cell"], repr(d["header_text"]), d["unit"])
            for k, v in d["cells"].items():
                print("    ", k, v)
            s = sum(d["cells"][k]["value_mn"] for k in ("일반", "장기", "자동차"))
            print("     legs sum", s, "vs 합계", d["cells"]["합계"]["value_mn"])
        continue
    code, qs, pl4, csm = SPEC[key]
    print("=" * 100)
    print(key, code)
    for q in qs:
        if pl4 is not None:
            try:
                r = pl4(q)
                print(f"  {q} PL4 {r['part']['printed']} L{r['part']['line']} unit {r['unit']} -> {r['part']['contribution_mn']} mn  (n_numeric {r['n_numeric']}) {r['src']}")
            except Exception as e:  # noqa: BLE001
                print(f"  {q} PL4 ERROR {type(e).__name__}: {str(e)[:300]}")
        try:
            v = csm(q)
            print(f"  {q} CSM exact {[round(x, 4) for x in v['vec_exact']]} vec2 {v['vec']} vec1 {v['vec1']}")
            print(f"        e20 vector {vs.get((code, q))} | group-row-5 {round(v['check_group_row_5']['contribution_eok'], 4) if isinstance(v.get('check_group_row_5'), dict) else v.get('check_group_row_5')} | {v['src']}")
            print("        cites: " + " ; ".join(f"i{i}:{c[0]['label'][:24]}|L{c[0]['line']}|{c[0]['printed']}" for i, c in sorted(v["cells"].items())))
        except Exception as e:  # noqa: BLE001
            print(f"  {q} CSM ERROR {type(e).__name__}: {str(e)[:400]}")
