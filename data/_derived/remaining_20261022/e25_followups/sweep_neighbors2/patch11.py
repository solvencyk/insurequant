s = open("p20_compile.py", encoding="utf-8").read()
# 1. custom cells: merge x02, x03, b04
s = s.replace('x01 = J("x01_custom.json")    # custom readers (list of cell dicts)',
 'x01 = dict(cells=[])\nfor _n in ("x02_kr0082.json", "x03_kr0079.json", "b04_life_is.json", "x04_kr0087.json"):\n    x01["cells"] += J(_n).get("cells", [])\nS1 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors/"\np1 = json.load(open(S1 + "p1_stmt.json", encoding="utf-8"))\nOVR = {("KR0099", "2023.1Q", "17"): (119675.0, "L25618 (투자영업손익 583,923) + L25904 (보험금융손익 (464,248)) = 119,675", "reader fix: 17 = 투자영업손익 + 보험금융손익 in the FY2024 KB라이프 statement layout"),\n       ("KR0099", "2023.1Q", "18"): (583923.0, "L25618 + L25904 (18 = 17 - 19 = 119,675 + 464,248)", "reader fix, see item 17")}')
# 2. override in b01 loop
s = s.replace('        m = pl.get((c, q, i))\n        note = f"calib',
 '        m = pl.get((c, q, i))\n        if (c, q, i) in OVR:\n            v = dict(v, val=OVR[(c, q, i)][0], line=[OVR[(c, q, i)][1]])\n        note = f"calib')
# 3. derived items before the CSM block
marker = "# ---------- CSM\n"
derived = '''# ---------- supplementary legs from the first sweep (not counted as compared)
for k, v in p1.items():
    c, q = k.split("|")
    for i in ("2", "3", "8"):
        d = v.get("prior", {}).get(i) if v.get("prior") else None
        if isinstance(d, dict) and i not in latest_pl[(c, q)]:
            latest_pl[(c, q)][i] = d["val"]
# ---------- derived items 2 / 7 / 12 from the latest legs (production definitions)
for (c, q), L in sorted(latest_pl.items()):
    cand = {}
    if "3" in L and "8" in L:
        cand["2"] = (L["3"] + L["8"], "2 = 3 + 8")
    if all(x in L for x in ("3", "4", "5", "6")):
        cand["7"] = (L["3"] - (L["4"] + L["5"] + L["6"]), "7 = 3 - (4+5+6)")
    if all(x in L for x in ("8", "9", "10", "11")):
        cand["12"] = (L["8"] - (L["9"] + L["10"] + L["11"]), "12 = 8 - (9+10+11)")
    for i, (val, f) in cand.items():
        if (c, q, i) in unc and (c, q, i) not in compared:
            add(c, q, i, pl.get((c, q, i)), val, 1, "derived from the latest legs of this sweep", "-", "derived:" + f, conf="medium", note=f"{f}; legs " + ", ".join(f"{x}={round(L[x], 1)}" for x in sorted(L, key=int) if x in f.replace("(", " ").replace(")", " ").replace("+", " ").replace("-", " ").replace("=", " ").split()))
'''
s = s.replace(marker, derived + marker, 1)
# 4. structural life 13/14
s = s.replace("# ---------- coverage\n", '''# ---------- structural (not source-read): life companies carry 0 in items 13 and 14 by construction of assemble()
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}
structural = {k for k in unc if k[0] in LIFE and k[2] in ("13", "14") and k not in compared}
struct_bad = [k for k in structural if pl.get((k[0], k[1], k[2])) not in (0, 0.0)]
print("structural life 13/14 cells", len(structural), "non-zero in master:", struct_bad)
# ---------- coverage
''', 1)
s = s.replace('print("uncovered cells (first sweep)"', 'print("structural (not counted):", len(structural))\nprint("uncovered cells (first sweep)"')
open("p20_compile.py", "w", encoding="utf-8").write(s)
