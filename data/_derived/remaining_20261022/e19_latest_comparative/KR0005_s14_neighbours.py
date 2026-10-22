"""Read-only. Neighbour quarters outside the approved list: master vs the later filing's prior column (and the original filing) per Tier-1 item."""
import json, io
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
X = json.loads((EVD / "KR0005_s7_xml.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {}
for r in pl:
    if r["원보험사코드"] == "KR0005":
        M[(r["공시분기"], r["항목번호"])] = r.get("값")
ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32]
rows, out = [], []
for q in ("2023.1Q", "2023.2Q", "2024.3Q", "2024.4Q"):
    e = X["later|" + q]
    o = X.get("orig|" + q)
    for k in ITEMS:
        mv = M.get((q, k))
        lv = e["items"].get(str(k))
        ov = o["items"].get(str(k)) if o else None
        if lv is None and mv is None:
            continue
        diff = (mv is None) != (lv is None) or (mv is not None and lv is not None and abs(mv - lv) > 0.5)
        if diff:
            rows.append({"quarter": q, "item": k, "master": mv, "later_xml_prior_col": lv, "later_xml_line": (e["cites"].get(str(k)) or [[None, None]])[0][1], "original_xml": ov})
            out.append("%s item %2d master %12s later-prior %12s (line %s) original %s" % (q, k, mv, lv, rows[-1]["later_xml_line"], ov))
(EVD / "KR0005_s14_neighbours.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
(EVD / "KR0005_s14_neighbours.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows))
