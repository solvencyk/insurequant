"""Independent validation read: all separate-basis values for 2023-12-31 / 2024-12-31 from the raw filing XML (regex scan, no parser code)."""
import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/"
FILES = {
    "FY2025": R + "FY2025_Q4/raw/KR0073_교보생명보험_20260331004015/20260331004015.xml",
    "FY2024": R + "FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml",
}
CODES = ["Assets", "Liabilities", "Equity", "RetainedEarnings", "InsuranceContractsIssuedThatAreLiabilities"]
pat = re.compile(r'<TE ACODE="ifrs-full_(%s)" ACONTEXT="([^"]+)"[^>]*>(.*?)</TE>' % "|".join(CODES), re.S)
out = {}
for k, f in FILES.items():
    txt = open(f, encoding="utf-8").read()
    for m in pat.finditer(txt):
        ln = txt.count("\n", 0, m.start()) + 1
        ctxs = m.group(2)
        if "SeparateMember" not in ctxs:
            continue
        if not re.match(r"(BPFY2023eFY|PFY2023eFY|PFY2024eFY|FY2025eFY)_", ctxs):
            continue
        v = re.sub(r"<[^>]+>", "", m.group(3)).strip().replace(",", "")
        neg = v.startswith("(") or v.startswith("-")
        v = v.strip("()-")
        if not v.isdigit():
            continue
        val = -int(v) if neg else int(v)
        print(k, "L%d" % (ln + m.group(0)[:m.group(0).find(">")].count("\n")), m.group(1), ctxs.split("_")[0], "other-axes" if ctxs.count("Axis") > 1 else "plain", f"{val:,}")
        out.setdefault(k, []).append((ln, m.group(1), ctxs.split("_")[0], ctxs.count("Axis"), val))
json.dump(out, open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/v2_bs_ilp/w1_read.json", "w", encoding="utf-8"), ensure_ascii=False)
