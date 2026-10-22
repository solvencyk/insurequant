import re, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
F24 = R + "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
L = open(F24, encoding="utf-8").read().split("\n")
def row(ln):
    vals = []
    i = ln
    while len(vals) < 7 and i < ln + 60:
        m = re.search(r"<P>([^<]*)</P>", L[i])
        if m and i != ln - 1:
            t = m.group(1).strip().replace(",", "")
            if re.fullmatch(r"\(?\d+\)?", t):
                vals.append(-int(t.strip("()")) if t.startswith("(") else int(t))
        i += 1
    return vals
out = {}
for ln, name in ((52435, "opening restated"), (52533, "net income"), (52981, "annual dividend"), (53016, "hybrid dividend")):
    v = row(ln); out[name] = v
    print("L%d %s RE col(6th)=%s total(7th)=%s" % (ln, name, f"{v[5]:,}", f"{v[6]:,}"))
re_end = out["opening restated"][5] + out["net income"][5] + out["annual dividend"][5] + out["hybrid dividend"][5]
print("RE roll end (won):", f"{re_end:,}", " BS RE 6,427,125,882,496 diff:", re_end - 6427125882496)
print("net income FY2023 (mn):", out["net income"][5] / 1e6)
