# -*- coding: utf-8 -*-
"""Read-only: balance-sheet identity proof for the SA (특별계정부채) reading.
residual = 부채총계 - 보험계약부채(D1) - 재보험계약부채 - 특별계정부채 must equal 기타부채 + 계약자지분조정 (two printed tokens of the same BS pages).
Prints the matching token pairs; a hit proves that D1 and SA are exactly the liability-side lines of that balance sheet."""
import json, re, sys, itertools
sys.stdout.reconfigure(encoding="utf-8")
import fitz
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
D = R + "data/disclosure/"
tok = json.loads(open(R + "data/_derived/ifrs17_owner_followups_20261012/chubb_token_presence.json", "rb").read().decode("utf-8"))
tab = {r["quarter"]: r for r in json.loads(open(R + "data/_derived/bspl_followup_20261011/kr0100_item20_table.json", "rb").read().decode("utf-8"))}
bs = json.loads(open(R + "IFRS17_BS.json", "rb").read().decode("utf-8"))
re21 = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0100" and r["항목번호"] == 21}
NUM = re.compile(r"[(\-−△]?\s?\d{1,3}(?:,\d{3}){2,}\)?")
def val(s):
    neg = s.strip().startswith(("(", "-", "−", "△"))
    n = int(re.sub(r"[^\d]", "", s))
    return -n if neg else n
res = {}
for q, t in tok.items():
    doc = fitz.open(D + t["pdf"])
    pages = sorted(set(t["D1_pages"] + t["SA_pages"] + t["liab_pages"]))
    toks = set()
    for p in pages:
        for p2 in (p - 1, p, p + 1):
            if 1 <= p2 <= len(doc):
                for m in NUM.finditer(doc[p2 - 1].get_text("text")):
                    toks.add(val(m.group(0)))
    d1, sa, liab = t["D1_won"], t["SA_won"], t["liab_total_won"]
    re_won = round(re21[q] * 1e6)
    resid = liab - d1 - re_won - sa
    hits = []
    cand = sorted(toks | {0})
    cs = set(cand)
    for a in cand:
        b = resid - a
        if b in cs and a <= b:
            hits.append((a, b))
    res[q] = dict(resid=resid, hits=hits[:4], n_tokens=len(toks), RE_won=re_won)
    print(q, "residual", f"{resid:,}", "-> 기타부채+계약자지분조정 token pairs:", [(f"{a:,}", f"{b:,}") for a, b in hits[:3]] or "NONE")
json.dump(res, open(R + "data/_derived/ifrs17_owner_followups_20261012/chubb_identity.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
