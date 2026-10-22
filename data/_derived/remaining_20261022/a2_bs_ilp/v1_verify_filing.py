"""Independent re-read of the 9 tier-A values (+ closure) straight from the filing XML, with line numbers."""
import re, sys, io
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
F25 = R + "data/dart/FY2025_Q4/raw/KR0073_교보생명보험_20260331004015/20260331004015.xml"
F24 = R + "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
L25 = open(F25, encoding="utf-8").read().split("\n")
L24 = open(F24, encoding="utf-8").read().split("\n")
def num(s):
    s = re.sub(r"<[^>]+>", "", s).strip().replace(",", "")
    neg = s.startswith("(")
    s = s.strip("()")
    return -int(s) if neg else int(s)
def ctx(s):
    m = re.search(r'ACONTEXT="([^"]+)"', s); return m.group(1) if m else None
res = {}
# FY2025: TE lines carry ACODE+ACONTEXT
want25 = {46627: ("Assets", "BPFY2023eFY"), 46648: ("InsuranceContractsIssuedThatAreLiabilities", "BPFY2023eFY"),
          46718: ("Liabilities", "BPFY2023eFY"), 46767: ("RetainedEarnings", "BPFY2023eFY"), 46774: ("Equity", "BPFY2023eFY"),
          46626: ("Assets", "PFY2024eFY")}
for ln, (code, c0) in want25.items():
    s = L25[ln - 1]
    assert f'ACODE="ifrs-full_{code}"' in s and ctx(s).startswith(c0 + "_") and "SeparateMember" in s, (ln, s[:200])
    res[("25", ln)] = num(s)
    print("FY2025 L%d %s %s separate -> %s" % (ln, code, c0, f"{num(s):,}"))
# FY2024: <P> values, preceded by a TE carrying the context
want24 = {49707: ("Assets", "PFY2023eFY"), 49746: ("InsuranceContractsIssuedThatAreLiabilities", "PFY2023eFY"),
          49974: ("Liabilities", "PFY2023eFY"), 50098: ("RetainedEarnings", "PFY2023eFY"), 50117: ("Equity", "PFY2023eFY")}
for ln, (code, c0) in want24.items():
    te = L24[ln - 2]
    assert f'ACODE="ifrs-full_{code}"' in te and ctx(te).startswith(c0 + "_") and "SeparateMember" in te, (ln, te[:200])
    res[("24", ln)] = num(L24[ln - 1])
    print("FY2024 L%d %s %s separate -> %s" % (ln, code, c0, f"{num(L24[ln-1]):,}"))
pairs = [(46627, 49707), (46648, 49746), (46718, 49974), (46767, 50098), (46774, 50117)]
for a, b in pairs:
    assert res[("25", a)] == res[("24", b)], (a, b)
print("FY2024 prior col == FY2025 3rd col for 5 items: OK")
A, L, E, RE, IC = (res[("25", 46627)], res[("25", 46718)], res[("25", 46774)], res[("25", 46767)], res[("25", 46648)])
print("1 = 2 + 3 residual (won):", A - L - E)
A24 = res[("25", 46626)]
print("FY2025 PFY2024 assets:", f"{A24:,}", " (master 2024.4Q item 2 + 3 =", )
# SOCE RE roll from FY2024 filing
def soce(ln):
    return [num(x) for x in re.findall(r"<P>([^<]+)</P>", "".join(L24[ln - 1:ln + 12]))]
for ln in (52435, 52533, 52981, 53016):
    print("SOCE", ln, re.sub(r"<[^>]+>", "|", L24[ln-1])[:80].strip())
