import json, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
p = json.load(open(REPO + "/data/compare/panel_compare.json", encoding="utf-8"))
out = open(os.path.dirname(os.path.abspath(__file__)) + "/j5_peek.txt", "w", encoding="utf-8")
out.write(str(list(p.keys())) + "\n")
out.write(json.dumps({k: v for k, v in p.items() if k != "metrics"}, ensure_ascii=False)[:1500] + "\n")
for i, m in enumerate(p["metrics"]):
    out.write(f"[{i}] " + json.dumps({k: (v if k not in ("v", "v_pre", "med") else "...") for k, v in m.items()}, ensure_ascii=False)[:400] + "\n")
