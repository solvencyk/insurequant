"""validation 2026-08-30 — independent raw-XML CSM measurement-table scanner.

Parses a DART XML filing directly (no repo parser import). Finds EVERY <TABLE>
that carries the CSM-amortisation row, prints its section/caption context, and
sums the CSM columns of each waterfall stage across the 5 product groups
(each group = [PV, RA, CSM x3]; the CSM part is the last 3 of the 5 columns).

Rows are identified by their IFRS taxonomy ACODE, not by the Korean caption, so
label variants cannot change the answer.

Used to adjudicate KR0079 2025.2Q item4/item5
(inbox/validation/20260830T0400Z). Read-only.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe       scripts/_probes/probe_20260830_val_raw_csm_table_scan.py <filing.xml>
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TABLE_RE = re.compile(r"<TABLE\b.*?</TABLE>", re.S)
TR_RE = re.compile(r"<TR\b.*?</TR>", re.S)
TE_RE = re.compile(r"<TE\b([^>]*)>(.*?)</TE>|<TE\b([^>]*)/>", re.S)
TAG_RE = re.compile(r"<[^>]+>")

NEEDLE = "서비스의 이전으로 당기손익에 인식한 보험계약마진"

ITEM_BY_ACODE = {
    "ifrs-full_InsuranceContractsThatAreLiabilities": "1/6_liab",
    "ifrs-full_InsuranceContractsThatAreAssets": "1/6_asset",
    "ifrs-full_IncreaseDecreaseThroughEffectsOfContractsInitiallyRecognisedInPeriodInsuranceContractsLiabilityAsset": "2_new",
    "ifrs-full_InsuranceFinanceIncomeExpensesFromInsuranceContractsIssuedRecognisedInProfitOrLoss": "3_interest",
    "ifrs-full_IncreaseDecreaseThroughChangesInEstimatesThatAdjustContractualServiceMarginInsuranceContractsLiabilityAsset": "4_adjust",
    "ifrs-full_InsuranceRevenueContractualServiceMarginRecognisedInProfitOrLossBecauseOfTransferOfServices": "5_amort",
}


def txt(s):
    t = TAG_RE.sub("", s or "").replace("　", " ").replace("&nbsp;", " ")
    return " ".join(t.split())


def attr(a, n):
    m = re.search(n + r'="([^"]*)"', a or "")
    return m.group(1) if m else None


def num(s):
    s = (s or "").strip()
    if s in ("", "-", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s2 = re.sub(r"[(),\s]", "", s)
    if not re.fullmatch(r"-?\d+(\.\d+)?", s2):
        return None
    v = float(s2)
    return -v if neg else v


def rows_of(tbl):
    out = []
    for tr in TR_RE.findall(tbl):
        cells = []
        for m in TE_RE.finditer(tr):
            a = m.group(1) if m.group(1) is not None else (m.group(3) or "")
            cells.append({"acode": attr(a, "ACODE"), "text": txt(m.group(2) or "")})
        if cells:
            out.append(cells)
    return out


def ctx(doc, start, width=2500):
    seg = doc[max(0, start - width):start]
    ps = [txt(p) for p in re.findall(r"<(?:P|TITLE)[^>]*>(.*?)</(?:P|TITLE)>", seg, re.S)]
    ps = [p for p in ps if p and not re.fullmatch(r"[\d,().\-]+", p)]
    return " | ".join(ps[-4:])


def section_of(doc, start):
    seg = doc[:start]
    hits = re.findall(r"<TITLE[^>]*>(.*?)</TITLE>", seg, re.S)
    hits = [txt(h) for h in hits]
    keep = [h for h in hits if any(k in h for k in ("연결", "재무제표", "주석"))]
    return keep[-2:] if keep else hits[-2:]


def main():
    xml = Path(sys.argv[1])
    doc = xml.read_text(encoding="utf-8", errors="replace")
    n = 0
    for m in TABLE_RE.finditer(doc):
        tbl = m.group(0)
        if NEEDLE not in tbl:
            continue
        n += 1
        rows = rows_of(tbl)
        # determine value-column count from the widest data row
        widths = [len([c for c in r if c["acode"]]) for r in rows]
        w = max(widths) if widths else 0
        print("=" * 110)
        print(f"[{n}] charpos={m.start()} rows={len(rows)} maxvalcols={w}")
        print(f"    SECTION: {section_of(doc, m.start())}")
        print(f"    CTX: {ctx(doc, m.start())}")
        if w != 25:
            print(f"    -> not a 5x5 WIDE product table (cols={w}); skipping CSM math")
            # still show item4/5 raw when single-block
            for r in rows:
                ac = next((c["acode"] for c in r if c["acode"]), None)
                if ac in ITEM_BY_ACODE and ITEM_BY_ACODE[ac] in ("4_adjust", "5_amort"):
                    vals = [c["text"] for c in r if c["acode"]]
                    print(f"       {ITEM_BY_ACODE[ac]}: {vals}")
            continue
        agg = {}
        for r in rows:
            ac = next((c["acode"] for c in r if c["acode"]), None)
            if ac not in ITEM_BY_ACODE:
                continue
            nums = [num(c["text"]) for c in r if c["acode"]]
            if len(nums) != 25 or any(x is None for x in nums):
                continue
            tot = sum(nums[p * 5 + 2] + nums[p * 5 + 3] + nums[p * 5 + 4] for p in range(5))
            key = ITEM_BY_ACODE[ac]
            agg.setdefault(key, []).append(tot / 1e8)
        for k in sorted(agg):
            print(f"       {k}: {[round(v,2) for v in agg[k]]}")
    print(f"\n[tables with needle: {n}]")


if __name__ == "__main__":
    main()
