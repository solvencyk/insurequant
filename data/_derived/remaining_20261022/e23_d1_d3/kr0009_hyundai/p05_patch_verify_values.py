# -*- coding: utf-8 -*-
"""patch the verifier: also write kr0009_verify_values.json (the independently re-read values, used by the post-apply diff checker)"""
from pathlib import Path

p = Path(__file__).resolve().parent / "kr0009_verify.py"
s = p.read_text(encoding="utf-8")
a = '    say("\\n== RESULT: " + ("ALL OK, problems 0" if not PROBLEMS else f"{len(PROBLEMS)} PROBLEM(S)"))\n'
b = '''    # ---- the independently re-read values (written for kr0009_diff_vs_backup.py)
    vals = {"pl": {}, "csm": {}, "printed_3m": {}}
    for q in QUARTERS:
        d = {}
        for (qq, i), c in plan_pl.items():
            if qq != q:
                continue
            if i in IR_ITEM:
                d[str(i)] = NEW[q]["ir"]["cells"][IR_ITEM[i]]["value_mn"]
            elif i == 4:
                d[str(i)] = NEW[q]["n4"]["mn"]
            elif i == 15:
                d[str(i)] = 0.0
            else:
                d[str(i)] = NEW[q]["items"][i]
        vals["pl"][q] = d
        rows = NEW[q]["csm"]["rows"]
        vals["csm"][q] = [round(rows[i]["mn"] / 100.0, 1) for i in range(1, 7)]
    for q in ("2023.2Q", "2023.3Q"):
        v3 = items_from(stmt_vector(NEW[q]["S"], 2023, "3m"))
        vals["printed_3m"][q] = {str(i): v for i, v in v3.items()}
        vals["printed_3m"][q]["4"] = NEW[q]["n4_3m"]["mn"]
        if q == "2023.2Q":
            for name, it in (("장기", 2), ("자동차", 13), ("일반", 14)):
                vals["printed_3m"][q][str(it)] = NEW[q]["ir"]["cells"][name]["k_value"]
    (HERE / "kr0009_verify_values.json").write_text(json.dumps(vals, ensure_ascii=False, indent=1), encoding="utf-8", newline="\\n")
    say("\\n== RESULT: " + ("ALL OK, problems 0" if not PROBLEMS else f"{len(PROBLEMS)} PROBLEM(S)"))
'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
