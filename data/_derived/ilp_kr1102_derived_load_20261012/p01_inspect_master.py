# -*- coding: utf-8 -*-
"""Inspect insurance_liability_portfolio.json structure + KR1102 rows (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
with open(ROOT + "insurance_liability_portfolio.json", "r", encoding="utf-8") as f:
    d = json.load(f)
print("type:", type(d).__name__, "len:", len(d))
if isinstance(d, dict):
    print("keys:", list(d.keys())[:20])
    for k, v in d.items():
        if isinstance(v, list):
            print(k, "list len", len(v))
            print(json.dumps(v[:2], ensure_ascii=False)[:1200])
        else:
            print(k, type(v).__name__, str(v)[:300])
else:
    print(json.dumps(d[:2], ensure_ascii=False)[:1200])
