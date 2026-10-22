"""Independent RE roll for 2023 from the FY2024 annual report SOCE (separate): RE opening 2023-01-01, net income, dividends, other."""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
f = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
txt = open(f, encoding="utf-8").read()
# TE with ACONTEXT containing RetainedEarningsMember axis or RetainedEarnings concept, from SOCE (PFY2023eFY duration / instant)
pat = re.compile(r'<TE ACODE="([^"]+)" ACONTEXT="([^"]+)"[^>]*>(.*?)</TE>', re.S)
rows = []
for m in pat.finditer(txt):
    ctx = m.group(2)
    if "SeparateMember" not in ctx or "RetainedEarningsMember" not in ctx:
        continue
    if not re.match(r"(PFY2023|BPFY2023|PFY2022|FY2024)", ctx):
        continue
    ln = txt.count("\n", 0, m.start()) + 1
    v = re.sub(r"<[^>]+>", "", m.group(3)).strip()
    rows.append((ln, m.group(1), ctx.split("_")[0], v))
for r in rows:
    print(r)
