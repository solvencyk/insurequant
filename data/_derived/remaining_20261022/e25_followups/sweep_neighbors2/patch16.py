s = open("b01_stmt.py", encoding="utf-8").read()
old = """def pick_cell(self, row, role, kind):
    nums = row.cells
    r = _orig(self, row, role, kind)"""
new = """AMBIG = set()
def pick_cell(self, row, role, kind):
    nums = row.cells
    if not any(R.RE_CTX.match(c["ctx"] or "") for c in nums):
        from collections import Counter
        if not hasattr(self, "_modal"):
            cnt = Counter(sum(1 for c in r.cells if c["val"] is not None or c["text"].strip() == "-") for r in self.rows if r.cells)
            self._modal = cnt.most_common(1)[0][0] if cnt else 0
        nv = sum(1 for c in nums if c["val"] is not None or c["text"].strip() == "-")
        if kind == "cum" and self._modal == 4 and nv == 3:
            for c in nums:
                AMBIG.add(c["line"])
    r = _orig(self, row, role, kind)"""
assert old in s
s = s.replace(old, new)
old2 = """                rec["items"][str(i)] = dict(val=v["val"], line=[p["line"] for p in v["parts"]], printed=[p["printed"] for p in v["parts"]], absent=bool(v.get("absent")))"""
new2 = """                rec["items"][str(i)] = dict(val=v["val"], line=[p["line"] for p in v["parts"]], printed=[p["printed"] for p in v["parts"]], absent=bool(v.get("absent")),
                                            ambiguous=any(p["line"] in AMBIG for p in v["parts"]))"""
assert old2 in s
s = s.replace(old2, new2)
s = s.replace("        BLANK[\"n\"] = 0\n        t1 = X.read_tier1(", "        BLANK[\"n\"] = 0\n        AMBIG.clear()\n        t1 = X.read_tier1(")
open("b01_stmt.py", "w", encoding="utf-8").write(s)
c = open("p20_compile.py", encoding="utf-8").read()
old3 = """        latest_pl[(c, q)][i] = v["val"]
        m = pl.get((c, q, i))"""
new3 = """        if v.get("ambiguous"):
            rows.append(dict(company=c, quarter=q, item=i, master=pl.get((c, q, i)), latest=round(v["val"], 3), diff_mn=None, cls="UNREADABLE_LAYOUT", confidence="none", filing=rec["file"],
                             line=",".join(str(x) for x in v["line"]), source="stmt:b01", note="statement row prints 3 value cells in a 4-column (3M/cumulative x current/prior) layout: empty cell dropped, column ambiguous; not compared"))
            continue
        latest_pl[(c, q)][i] = v["val"]
        m = pl.get((c, q, i))"""
assert old3 in c
c = c.replace(old3, new3)
open("p20_compile.py", "w", encoding="utf-8").write(c)
