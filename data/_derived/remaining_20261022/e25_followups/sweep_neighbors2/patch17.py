s = open("p20_compile.py", encoding="utf-8").read()
old = """    elif abs(abs(new) - abs(master)) <= 1.0 and (new * master) < 0:
        cls = "SIGN\""""
assert old in s
s = s.replace(old, old + """
    elif abs(d) <= 10 and master == round(master) and master % 100 == 0:
        cls = "OTHER_COARSE_ROUNDING\"""")
old2 = "rows.sort(key=lambda r: -abs(r[\"diff_mn\"] or 0))"
new2 = """# extra (outside the 3,703 denominator): CSM blocks that the loads did not touch but whose latest comparative was readable
c03 = J("c03_csm_extra.json")
for k, rec in c03.items():
    c, q = k.split("|")
    if rec["status"] != "OK":
        continue
    for i in range(1, 7):
        m = csm.get((c, q, str(i)))
        if m is None:
            continue
        new = rec["prior"][str(i)]
        if abs(new - m) > 0.06:
            rows.append(dict(company=c, quarter=q, item="CSM" + str(i), master=round(m * 100, 1), latest=round(new * 100, 1), diff_mn=round((new - m) * 100, 1), cls="VINTAGE_CSM(extra, not in denominator)", confidence="high",
                             filing=rec["file"], line="; ".join(f"cell L{x[str(i)][0]} '{x[str(i)][1]}'" for x in rec["cites"]), source="csm:c03_extra", note=f"closure {rec['closure_eok']} eok; table(s) {rec['tables']}"))
rows.sort(key=lambda r: -abs(r["diff_mn"] or 0))"""
assert old2 in s
s = s.replace(old2, new2, 1)
open("p20_compile.py", "w", encoding="utf-8").write(s)
