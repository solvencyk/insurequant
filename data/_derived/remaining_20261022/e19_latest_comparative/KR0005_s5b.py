from KR0005_common import *
for fy in ("FY2025_Q3","FY2025_Q4"):
    p = main_xml(fy)
    L = P.read_lines(p)
    lo, hi = P.sections(L)["sep_fs"]
    rows = P.rows_in_range(L, lo, hi)
    out = io.open(EVD/f"KR0005_s5_stmt_{fy}.txt","w",encoding="utf-8")
    out.write(f"file={rel(p)} sep_fs=L{lo}-L{hi} rows={len(rows)}\n")
    for r in rows:
        if not r["cells"]: continue
        lab = r["cells"][0][0]
        vals = " | ".join(f"{t}@L{ln}" for t,ln in r["cells"][1:])
        out.write(f"TR{r['tr']}: {lab[:50]} :: {vals}\n")
    out.close()
