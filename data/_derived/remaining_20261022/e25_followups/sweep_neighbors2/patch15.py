s = open("p20_compile.py", encoding="utf-8").read()
s = s.replace("    if abs(d) <= 1.0:\n        cls = \"ROUNDING_PM1\"", "    if abs(d) <= (3.5 if src.startswith('derived') else 1.0 + 1e-6):\n        cls = \"ROUNDING_PM1\"")
old = s[s.index("# ---------- WRONG_LEG detection"):s.index("rows.sort(")]
new = '''# ---------- WRONG_LEG detection: master equals (or sits within 2%+1 of) the paired reinsurance/direct latest value
PAIR = {"4": "9", "5": "10", "6": "11", "9": "4", "10": "5", "11": "6"}
g2 = json.load(open(S1 + "p2_generic.json", encoding="utf-8"))
for r in rows:
    if r["cls"].startswith(("VINTAGE", "SIGN", "HELD")) and r["item"] in PAIR and r["master"] is not None:
        c, q = r["company"], r["quarter"]
        cands = []
        lv = latest_pl[(c, q)].get(PAIR[r["item"]])
        if lv is not None:
            cands.append((lv, "this sweep"))
        for x in (g2.get(f"{c}|{q}", {}).get("prior", {}) or {}).get(PAIR[r["item"]], []) or []:
            cands.append((x["val"], f"first sweep p2_generic L{x['line']}"))
        for lv, srcn in cands:
            if abs(abs(lv) - abs(r["master"])) <= 0.02 * abs(lv) + 1.0 and abs(r["master"]) > 5 and abs(abs(r["latest"]) - abs(r["master"])) > 0.05 * abs(r["latest"]):
                r["cls"] = r["cls"].replace("VINTAGE_NOTE", "WRONG_LEG").replace("VINTAGE_STATEMENT", "WRONG_LEG")
                r["note"] += f"; master {r['master']} is within 2% of the paired item {PAIR[r['item']]} printed {lv} ({srcn})"
                break
'''
s = s.replace(old, new)
open("p20_compile.py", "w", encoding="utf-8").write(s)
