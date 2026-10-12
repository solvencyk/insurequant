import sys, os, re, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = [r for r in csv.DictReader(open(here + "/h3_undecided.csv", encoding="utf-8-sig")) if r["verdict"] in ("NOROW", "MISMATCH")]
seen = set(); out = open(here + "/h4_norow.txt", "w", encoding="utf-8")
for r in rows:
    key = r["pdf"] if r["pdf"] else None
    k = (r["code"], r["quarter"])
    if k in seen: continue
    seen.add(k)
    doc = fitz.open(REPO + "/" + r["pdf"])
    out.write(f"#### {r['code']} {r['quarter']} {os.path.basename(r['pdf'])} pages={len(doc)} master item{r['item']}={r['master(백만원)']}\n")
    shown = 0
    for pn in range(1, min(len(doc), 14) + 1):
        txt = doc[pn - 1].get_text()
        flat = re.sub(r"\s+", "", txt)
        if re.search(r"순이익|순손실|세전|법인세|손익", flat) and re.search(r"\d", flat):
            rws = page_rows(doc, pn)
            hits = []
            for y, ws in rws:
                line = " ".join(t for _, _, t in ws)
                if re.search(r"순이익|순손실|순손익|세전|법인세|보험손익|기타사업비용|영업이익|영업손익|구\s*분|\(\d\d\.\dQ\)|\d{4}\.\dQ|전년|당기|당분기", line):
                    hits.append(f"      p{pn} {y:5.0f} | {line[:150]}")
            if hits and shown < 1:
                out.write("\n".join(hits[:28]) + "\n"); shown += 1
    if shown == 0: out.write(f"      (no PL-like text in first 14 pages; chars on p4: {len(doc[3].get_text()) if len(doc)>3 else 0})\n")
