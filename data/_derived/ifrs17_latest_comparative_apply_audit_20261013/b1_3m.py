"""Re-read the 3-month-vs-cumulative PL cells (14) from the ORIGINAL FY2023_Q2 filings (own reader)."""
import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
cells = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["kind"] == "3m_as_cumulative"]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/b1_3m.txt", "w", encoding="utf-8")
LABS = {  # label regex -> key
    "ins": r"^(Ⅰ|I)?\.?\s*보험손익$", "inv": r"^(Ⅱ|II)\.?\s*투자손익$", "opinc": r"^(Ⅲ|III)\.?\s*영업이익$",
    "nonop_rev": r"영업외수익$", "nonop_exp": r"영업외비용$", "pretax": r"법인세(비용)?\s*차감전\s*순?이익", "tax": r"^(Ⅶ|VII|Ⅵ|VI)\.?\s*법인세비용$|^\(?[Ⅶ\w]*\)?\.?\s*법인세비용$",
    "ni": r"(분기|반기|당기)?\s*순이익$|당기순이익", "fin_rev": r"^\(1\)\s*보험금융수익$", "fin_exp": r"^\(1\)\s*보험금융비용$",
    "re_rev": r"^\(2\)\s*재보험금융수익$", "re_exp": r"^\(2\)\s*재보험금융비용$",
}
def rowkey(label):
    l = label.replace(" ", "")
    for k, rx in LABS.items():
        if re.search(rx.replace(r"\s*", ""), l): return k
    return None
by_file = {}
for c in cells:
    rc = re.search(r"rcept (\d+)", c["source_ref"]).group(1)
    by_file.setdefault((c["code"], rc), []).append(c)
for (code, rc), cs in by_file.items():
    p = find_xml(code, "FY2023_Q2", rc)[0]
    tabs = load_tables(p)
    out.write(f"===== {code} {rc} {os.path.basename(os.path.dirname(p))}\n")
    for t in tabs:
        hits = {}
        for r in t["rows"]:
            lab, vals = row_vals(r)
            k = rowkey(lab)
            if k and len(vals) >= 3 and k not in hits: hits[k] = (lab, vals)
        if len(hits) >= 5 and "ni" in hits and "ins" in hits:
            out.write(f"  table {t['idx']} line {t['line']} cap={t['caption'][:50]!r}\n")
            for k, (lab, vals) in hits.items(): out.write(f"     {k:9s} {lab[:30]!r}: {vals}\n")
    for c in cs:
        m1 = master.get((code, "2023.1Q", int(c["item"])))
        out.write(f"  CELL item{c['item']} {c['item_name']}: old={c['old']} new={c['new']} | master 2023.1Q item value = {m1 and m1.get('값')}\n")
