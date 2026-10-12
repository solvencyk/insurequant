import json, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
d = json.load(open(REPO + "/NB_CSM_multiple.json", encoding="utf-8"))
recs = d if isinstance(d, list) else d.get("records") or d.get("rows") or d
out = open(os.path.dirname(os.path.abspath(__file__)) + "/j1_nb_peek.txt", "w", encoding="utf-8")
out.write(f"type {type(d)} len {len(recs)}\n")
for i in (107, 108, 149, 150):
    out.write(f"[{i}] " + json.dumps(recs[i], ensure_ascii=False) + "\n")
