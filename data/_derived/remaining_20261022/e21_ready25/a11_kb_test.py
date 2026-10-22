import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
cand = {}
for c in d["pl_cells"]:
    cand[(c["code"], c["q"], c["item"])] = c["new"]
for q in ("2023.1Q", "2023.2Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"):
    r = T.kb_read("KR0010", q)
    m = lambda i: pl.get(("KR0010", i, q))  # noqa: E731
    der = T.derive_2_3_7_8_12(r, m(4), m(5), m(6), m(9), m(10), m(11))
    print("=====", q, r[3]["src"])
    for i in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
        got = r[i]["val"] if i in r else der.get(i)
        c = cand.get(("KR0010", q, i))
        old = m(i)
        tag = "CAND" if c is not None else "keep"
        ref = c if c is not None else old
        ok = (got is not None and ref is not None and abs(got - ref) < 1e-3)
        print(f"  item{i:>2} read={None if got is None else round(got, 3)} {tag}={ref} master_old={old} {'OK' if ok else 'DIFF'}")
