import json, collections
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
ae = json.load(open(R/"data/loss_ratio/claims_ae_ratio.json", encoding="utf-8"))
print(type(ae), len(ae))
rows = ae if isinstance(ae, list) else ae.get("rows", ae)
if isinstance(rows, dict):
    print(list(rows.keys())[:10])
else:
    print(json.dumps(rows[0], ensure_ascii=False))
    print(json.dumps(rows[-1], ensure_ascii=False))
    keys = collections.Counter()
    for r in rows: keys.update(r.keys())
    print(keys)
    print(collections.Counter((r.get("원보험사코드"), r.get("공시분기")) for r in rows).most_common(5))
    print(sorted({r.get("공시분기") for r in rows}))
    print(len({r.get("원보험사코드") for r in rows}))
    for k in ("플래그","identity_break","단위"):
        print(k, collections.Counter(str(r.get(k)) for r in rows).most_common(6))
