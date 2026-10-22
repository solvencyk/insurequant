import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
out = []
for c in ["KR0005","KR0032","KR0070","KR0082","KR0083","KR0087","KR0104"]:
    p = json.loads((E / f"plan_{c}.json").read_text(encoding="utf-8"))
    for k in ("auto_follow_cells", "neighbour_effects", "side_effect_single_quarters"):
        if k in p and p[k]:
            out.append(f"{c} {k}: n={len(p[k])} keys={list(p[k][0].keys())}")
            out.append("    " + json.dumps(p[k][0], ensure_ascii=False)[:300])
    if c == "KR0082":
        out.append("KR0082 seam keys: " + json.dumps(p["seam_cells"][0], ensure_ascii=False)[:600])
        out.append("KR0082 neighbour: " + json.dumps(p["neighbour_effects"], ensure_ascii=False)[:800])
Path("peek6.txt").write_text("\n".join(out), encoding="utf-8")
