import sys, os, json
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
import validate_kics_disclosure as G
out = open(os.path.dirname(os.path.abspath(__file__)) + "/i1_registry.txt", "w", encoding="utf-8")
reg = G._TIER2_ISSUER_INCONSISTENT
out.write(f"registry size {len(reg)}\n")
for k, v in sorted(reg.items()):
    fl = {r: d.get("flag") for r, d in v["findings"].items()}
    out.write(f"{k}: cells={ {i: list(c) for i, c in v['cells'].items()} } findings={fl}\n")
