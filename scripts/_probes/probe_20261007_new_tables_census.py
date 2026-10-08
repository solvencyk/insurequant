"""Census: per (quarter, company) PDF, which pages hold persistency / loss-ratio tables."""
import csv
import glob
import os
import re
import fitz

ROOT = r"C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "census_new_tables.csv")
KEYS = {
    "persist_channel": r"유지계약액",
    "persist_summary": r"유지율.{0,80}13회",
    "risk_vs_expected": r"위험보험료대비예상보험금",
    "claims_ae_ratio": r"예실차비율",
    "expected_lr": r"예상손해율",
    "combined_ratio": r"합산비율",
}

rows = []
for qdir in sorted(glob.glob(os.path.join(ROOT, "FY20*"))):
    q = os.path.basename(qdir)
    for pdf in sorted(glob.glob(os.path.join(qdir, "raw", "*.pdf"))):
        name = os.path.basename(pdf)[:-4]
        rec = {"quarter": q, "file": name}
        try:
            doc = fitz.open(pdf)
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)
            rows.append(rec)
            continue
        hits = {k: [] for k in KEYS}
        chars = 0
        low_text_pages = 0
        for i, page in enumerate(doc):
            t = page.get_text()
            chars += len(t)
            if len(t.strip()) < 50:
                low_text_pages += 1
            tt = re.sub(r"\s+", "", t)
            for k, pat in KEYS.items():
                if re.search(pat, tt):
                    hits[k].append(i + 1)
        rec["pages"] = doc.page_count
        rec["chars_per_page"] = chars // max(doc.page_count, 1)
        rec["low_text_pages"] = low_text_pages
        for k in KEYS:
            rec[k] = " ".join(map(str, hits[k]))
        doc.close()
        rows.append(rec)
        print(q, name, rec["chars_per_page"], {k: rec[k] for k in KEYS}, flush=True)

cols = ["quarter", "file", "pages", "chars_per_page", "low_text_pages", *KEYS, "error"]
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("WROTE", OUT, len(rows))
