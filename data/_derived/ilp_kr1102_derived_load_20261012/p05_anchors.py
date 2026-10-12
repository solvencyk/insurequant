# -*- coding: utf-8 -*-
"""Independent anchors for KR1102 2026.1Q: CSM_waterfall closing CSM, IFRS17_BS items, amortization schedule total (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
def load(name):
    with open(ROOT + name, "r", encoding="utf-8") as f:
        return json.load(f)

wf = load("CSM_waterfall.json")
print("CSM_waterfall rows:", len(wf), "sample keys:", sorted(wf[0].keys()))
rows = [r for r in wf if r.get("원보험사코드") == "KR1102"]
print("KR1102 waterfall rows:", len(rows))
for q in ("2025.4Q", "2026.1Q", "2026.2Q"):
    print("==", q)
    for r in sorted((r for r in rows if r["공시분기"] == q), key=lambda r: r["항목번호"]):
        print("   ", r["항목번호"], r.get("항목명"), "값=", r.get("값"), "값_당분기=", r.get("값_당분기"))

bs = load("IFRS17_BS.json")
rows = [r for r in bs if r.get("원보험사코드") == "KR1102" and r["공시분기"] in ("2025.4Q", "2026.1Q", "2026.2Q")]
print("\nIFRS17_BS KR1102 rows (2025.4Q/2026.1Q/2026.2Q):", len(rows))
for r in sorted(rows, key=lambda r: (r["공시분기"], r["항목번호"])):
    print("   ", r["공시분기"], r["항목번호"], r.get("항목명"), r.get("값"))

am = load("CSM_amortization.json")
print("\nCSM_amortization rows:", len(am), "keys:", sorted(am[0].keys()))
rows = [r for r in am if r.get("원보험사코드") == "KR1102" and r["공시분기"] in ("2025.4Q", "2026.1Q", "2026.2Q")]
tot = {}
for r in rows:
    tot.setdefault(r["공시분기"], 0.0)
    tot[r["공시분기"]] += float(r.get("상각액") or 0)
print("KR1102 amort rows:", len(rows), "sum by quarter:", tot)
