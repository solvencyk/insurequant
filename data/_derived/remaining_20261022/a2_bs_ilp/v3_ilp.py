import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
F24 = R + "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
L = open(F24, encoding="utf-8").read().split("\n")
for ln in range(63744, 63776):
    s = L[ln - 1]
    t = re.sub(r"<[^>]+>", "", s).strip()
    if t: print(ln, t)
# which table: header of the 2) 전기 table (line 63530)
print("caption 63530:", re.sub(r"<[^>]+>", "", L[63530 - 1]).strip(), "| 63279:", re.sub(r"<[^>]+>", "", L[63279 - 1]).strip())
for ln in range(63531, 63575):
    t = re.sub(r"<[^>]+>", "", L[ln - 1]).strip()
    if t and not t.startswith("<") and ln < 63560: print(ln, t)
lrc, lc, lic, tot = 83536489, 1013643, 2692746, 87242879
print("LRC incl LC (mn):", lrc + lc, "-> eok", (lrc + lc) / 100)
print("LIC printed (mn):", lic, "-> eok", lic / 100)
print("sum printed:", lrc + lc + lic, "vs printed total", tot)
bs20 = 87242878.594424
print("BS20/100 =", bs20 / 100, "round2 =", round(bs20 / 100, 2))
print("LIC implied (BS20 - LRC) mn:", bs20 - (lrc + lc), "-> eok", round((bs20 - (lrc + lc)) / 100, 2))
print("10+14 =", round(26927.47 + 845501.32, 2), " vs 15 =", 872428.79)
