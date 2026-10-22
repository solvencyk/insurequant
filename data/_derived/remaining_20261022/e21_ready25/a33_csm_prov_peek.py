"""a33: peek at CSM_waterfall_provenance.json blocks of READY companies (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "CSM_waterfall_provenance.json", encoding="utf-8").read())
print("top keys:", [k for k in d.keys()])
cells = d["cells"]
print("n blocks", len(cells), "example keys", list(cells[0].keys()))
for c in cells:
    if c["company_code"] in ("KR0003", "KR0079", "KR0001", "KR0068") and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
        print(json.dumps({k: (v if k != "note" else str(v)[:80]) for k, v in c.items()}, ensure_ascii=False)[:400])
for k in d:
    if k.startswith("merge_note") or k.startswith("_"):
        print(k, str(d[k])[:200])
