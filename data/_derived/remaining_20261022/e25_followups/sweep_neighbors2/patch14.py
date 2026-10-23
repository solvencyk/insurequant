s = open("p20_compile.py", encoding="utf-8").read()
old = """            pm = pl.get((r["company"], pq, r["item"]))
            if pm is not None and abs((r["latest"] - pm) - r["master"]) <= 1.5 and abs(pm) > 5:"""
new = """            pms = [x for x in (pl.get((r["company"], pq, r["item"])), latest_pl.get((r["company"], pq), {}).get(r["item"])) if x is not None]
            pm = next((x for x in pms if abs((r["latest"] - x) - r["master"]) <= 1.5 and abs(x) > 5), None)
            if pm is not None:"""
assert old in s
open("p20_compile.py", "w", encoding="utf-8").write(s.replace(old, new))
