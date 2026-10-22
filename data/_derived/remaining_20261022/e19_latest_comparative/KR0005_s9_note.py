from KR0005_common import *
import re
START = {"FY2024_Q3": 25300, "FY2024_Q4": 36584, "FY2025_Q1": 24075, "FY2025_Q2": 70288}
for fy, s in START.items():
    p = main_xml(fy)
    L = P.read_lines(p)
    # end: next numbered note heading "NN. " after s+5 in a <P>/<SPAN> beginning, else s+1500
    e = s + 1500
    for i in range(s + 5, min(len(L), s + 3000)):
        t = P.clean(L[i-1])
        if re.match(r"^(4[2-9]|5\d)\.\s", t) and ("<SPAN" in L[i-1] or "<P" in L[i-1]):
            e = i; break
    out = io.open(EVD/f"KR0005_s9_note_{fy}.txt","w",encoding="utf-8")
    out.write(f"{rel(p)} note window L{s}-L{e}\n")
    rows = P.rows_in_range(L, s, e)
    inrow = set()
    for r in rows:
        inrow.update(range(r["tr"], max(r["tr"], max((ln for _, ln in r["cells"]), default=r["tr"])) + 1))
    for i in range(s, e):
        if i in inrow: continue
        t = P.clean(L[i-1])
        if t and len(t) > 12:
            out.write(f"  P L{i}: {t[:500]}\n")
    for r in rows:
        if not r["cells"]: continue
        lab = r["cells"][0][0]
        vals = " | ".join(f"{t}@L{ln}" for t, ln in r["cells"][1:])
        out.write(f"TR{r['tr']}: {lab[:70]} :: {vals}\n")
    out.close()
