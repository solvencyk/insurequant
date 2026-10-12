# -*- coding: utf-8 -*-
"""Inspect insurance_liability_portfolio_provenance.json structure; KR1102 entries (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
with open(ROOT + "insurance_liability_portfolio_provenance.json", "r", encoding="utf-8") as f:
    p = json.load(f)
for k, v in p.items():
    if isinstance(v, (dict, list)):
        print(f"[{k}] {type(v).__name__} len={len(v)}")
    else:
        print(f"[{k}] {type(v).__name__}: {str(v)[:400]}")
print()
for k in ("key", "source_id_values", "inputs"):
    print(k, "=", json.dumps(p.get(k), ensure_ascii=False)[:1200])
print()
for sec in ("cells", "not_loaded", "lrc_model_cells"):
    v = p.get(sec)
    if isinstance(v, dict):
        ks = list(v.keys())
        print(f"== {sec}: dict len {len(ks)}; sample keys {ks[:5]}")
        for k in ks[:2]:
            print("   ", k, json.dumps(v[k], ensure_ascii=False)[:500])
        kr = [k for k in ks if "KR1102" in k]
        print(f"   KR1102 keys in {sec}: {len(kr)}")
        for k in sorted(kr):
            print("    ", k, json.dumps(v[k], ensure_ascii=False)[:900])
    elif isinstance(v, list):
        print(f"== {sec}: list len {len(v)}")
        print("   sample:", json.dumps(v[:2], ensure_ascii=False)[:700])
        kr = [e for e in v if "KR1102" in json.dumps(e, ensure_ascii=False)]
        print(f"   KR1102 entries in {sec}: {len(kr)}")
        for e in kr[:40]:
            print("    ", json.dumps(e, ensure_ascii=False)[:900])
