# -*- coding: utf-8 -*-
"""Full detail of KR1102 provenance entries: lrc_model_not_loaded + one full lrc_model_cells entry (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
with open(ROOT + "insurance_liability_portfolio_provenance.json", "r", encoding="utf-8") as f:
    p = json.load(f)
print("== lrc_model_not_loaded: KR1102")
for e in p["lrc_model_not_loaded"]:
    if e.get("company_code") == "KR1102":
        print(json.dumps(e, ensure_ascii=False, indent=1))
print("\n== all keys in lrc_model_not_loaded entries:", sorted({k for e in p["lrc_model_not_loaded"] for k in e}))
print("\n== KR1102 2026.2Q lrc_model_cells full entry")
for e in p["lrc_model_cells"]:
    if e.get("company_code") == "KR1102" and e.get("quarter") == "2026.2Q":
        print(json.dumps(e, ensure_ascii=False, indent=1))
print("\n== KR1102 2025.1Q lrc_model_cells full entry")
for e in p["lrc_model_cells"]:
    if e.get("company_code") == "KR1102" and e.get("quarter") == "2025.1Q":
        print(json.dumps(e, ensure_ascii=False, indent=1))
print("\n== distinct keys in lrc_model_cells entries:", sorted({k for e in p["lrc_model_cells"] for k in e}))
print("\n== distinct item_block values:", sorted({e.get("item_block") for e in p["lrc_model_cells"]}))
print("\n== distinct basis values:", sorted({str(e.get("basis")) for e in p["lrc_model_cells"]}))
print("\n== distinct flags:", sorted({f for e in p["lrc_model_cells"] for f in (e.get("flags") or [])}))
