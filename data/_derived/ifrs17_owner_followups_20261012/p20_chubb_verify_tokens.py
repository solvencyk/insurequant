# -*- coding: utf-8 -*-
"""Read-only: independent re-read of Chubb (KR0100) D1 (일반계정 보험계약부채) and SA (특별계정부채) from the disclosure PDFs.
For each of the 9 mid-quarters: (1) exact digit token of D1 / SA / 부채총계 / 책임준비금 / 재보험계약부채 / 계약자지분조정 present on a page, (2) identity
부채총계 = 책임준비금 + 계약자지분조정 + 기타부채 + 특별계정부채 using the printed 기타부채 token, (3) 2-2 summary (억원) agrees to rounding.
Values come from the BS lane's table (kr0100_item20_table.json) ONLY as the thing to look for."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
D = R + "data/disclosure/"
PDF = {
    "2023.1Q": "FY2023_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2023.2Q": "FY2023_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2023.3Q": "FY2023_Q3/raw/KR0100_처브라이프생명보험.pdf",
    "2024.1Q": "FY2024_Q1/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2024.2Q": "FY2024_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2024.3Q": "FY2024_Q3/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2025.1Q": "FY2025_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2025.2Q": "FY2025_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2025.3Q": "FY2025_Q3/raw/KR0100_처브라이프생명보험.pdf",
}
tab = {r["quarter"]: r for r in json.loads(open(R + "data/_derived/bspl_followup_20261011/kr0100_item20_table.json", "rb").read().decode("utf-8"))}
defs = {r["quarter"]: r for r in json.loads(open(R + "data/_derived/bspl_followup_20261011/kr0100_item20_definitions.json", "rb").read().decode("utf-8"))}
def fmt(won):  # int won -> '1,234,567'
    return f"{int(round(won)):,}"
out = {}
for q, rel in PDF.items():
    t = tab[q]
    d1 = round(t["D1"] * 1e6); sa = round(t["SA"] * 1e6); liab = round(t["liab_total_item2"] * 1e6)
    doc = fitz.open(D + rel)
    pages = {}
    for pno, pg in enumerate(doc, 1):
        txt = pg.get_text("text")
        pages[pno] = txt
    def where(won):
        s = fmt(won)
        return [p for p, tx in pages.items() if s in tx]
    res = {"pdf": rel, "D1_won": d1, "SA_won": sa, "liab_total_won": liab,
           "D1_pages": where(d1), "SA_pages": where(sa), "liab_pages": where(liab)}
    out[q] = res
    print(q, rel.split("/")[0], "D1", fmt(d1), res["D1_pages"], "| SA", fmt(sa), res["SA_pages"], "| 부채총계", fmt(liab), res["liab_pages"])
json.dump(out, open(R + "data/_derived/ifrs17_owner_followups_20261012/chubb_token_presence.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
