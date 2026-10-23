import json
for n in ("user_pl_cells", "user_csm_cells"):
    d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/%s.json" % n, encoding="utf-8"))
    print(n, type(d).__name__, list(d)[:8] if isinstance(d, dict) else len(d))
    if isinstance(d, dict):
        for k, v in d.items():
            print(" ", k, type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
            if isinstance(v, list) and v: print("   sample", json.dumps(v[0], ensure_ascii=False)[:500])
            if isinstance(v, str): print("   ", v[:300])
