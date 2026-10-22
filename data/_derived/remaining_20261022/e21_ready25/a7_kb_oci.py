import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
print("candidate:", {c["item"]: (c["old"], c["new"]) for c in d["pl_cells"] if c["code"] == "KR0010" and c["q"] == "2023.4Q" and c["item"] in (25, 26, 27, 28, 29, 30, 31, 32)})
st = R.Stmt("KR0010", "FY2024_Q4")
vec = R.read_vector(st, "prior", "cum")
for i in (25, 26, 27, 28, 29, 30, 31, 32):
    print(i, vec[i]["val"], [(p.label[:40], p.line, p.printed, p.sign) for p in vec[i]["parts"]][:6])
print("leaf rows:")
for r in st.leafs():
    c = st.pick_cell(r, "prior", "cum")
    print("  ", r.line, r.raw.strip()[:50], R.classify_leaf(r), c["text"] if c else None)
