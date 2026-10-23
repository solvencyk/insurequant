# -*- coding: utf-8 -*-
"""scratch probe of kr0070_verify.py statement reader (read-only)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kr0070_verify as V  # noqa

sys.stdout.reconfigure(encoding="utf-8")
for key in ["N1", "N2", "N3", "N4", "O3", "O4", "A25"]:
    try:
        S = V.Stmt(key)
    except Exception as e:  # noqa
        print(key, "ERR", e)
        continue
    print("==", key, S.rel, "unit", S.unit, S.unit_line, "table", S.tab[0] + 1, S.tab[1] + 1)
    print("   periods", {k: (v["start"], v["end"]) for k, v in S.periods.items()})
    print("   paths", S.paths)
    try:
        vec = V.stmt_vector(S, 2023, "cum")
    except Exception as e:  # noqa
        print("   vector ERR", e)
        continue
    it = V.items_from(vec)
    print("   cols", {k: vec[k]["col"] for k in ("ins_result",)}, vec["ins_result"]["header"])
    print("   items", {k: round(v, 6) for k, v in sorted(it.items())})
    for name, d, ok in V.identities(vec):
        print(f"   identity {name}: {d:+.6f} {'OK' if ok else 'FAIL'}")
