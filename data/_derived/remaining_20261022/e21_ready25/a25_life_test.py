"""a25_life_test: independent life IS-line items (3, 8, 2) and derived 7 / 12 vs the READY candidate cells (READ-ONLY)"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_life as L  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(ROOT + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(ROOT + "PL_breakdown.json", encoding="utf-8").read())}
cand = {(c["code"], c["q"], c["item"]): c["new"] for c in d["pl_cells"]}
BUCKETS = [("KR0104", "2023.1Q", "FY2024_Q1", "prior"), ("KR0104", "2023.2Q", "FY2024_Q2", "prior"), ("KR0083", "2024.4Q", "FY2025_Q4", "prior"),
           ("KR0079", "2023.4Q", "FY2024_Q4", "prior"), ("KR0079", "2024.1Q", "FY2025_Q1", "prior"), ("KR0079", "2024.2Q", "FY2025_Q2", "prior"), ("KR0079", "2024.3Q", "FY2025_Q3", "prior"),
           ("KR0068", "2023.1Q", "FY2024_Q1", "prior"), ("KR0068", "2023.2Q", "FY2024_Q2", "prior"), ("KR0068", "2023.3Q", "FY2024_Q3", "prior"),
           ("KR0099", "2024.1Q", "FY2024_Q1", "cur")]
for code, q, fy, role in BUCKETS:
    st = R.Stmt(code, fy)
    r = L.life_is_items(code, fy, role, "cum", st=st)
    m = lambda i: cand.get((code, q, i), pl.get((code, i, q)))  # noqa: E731  (candidate if any else master)
    v = {i: r[i]["val"] for i in (2, 3, 8)}
    v[7] = None if None in (m(4), m(5), m(6)) else v[3] - (m(4) + m(5) + m(6))
    v[12] = None if None in (m(9), m(10), m(11)) else v[8] - (m(9) + m(10) + m(11))
    p015 = L.presence_015(st, role, "cum")
    print(f"== {code} {q} {fy} role={role} unit={st.unit}: 15 -> {p015['val']} present={p015['present']}")
    for i in (2, 3, 7, 8, 12):
        got = v[i]
        c = cand.get((code, q, i)); old = pl.get((code, i, q))
        ref = c if c is not None else old
        tag = "CAND" if c is not None else "keep"
        ok = got is not None and ref is not None and abs(got - ref) < 1e-3
        print(f"   item{i:>2} read={None if got is None else round(got, 6)} {tag}={ref} master={old} {'OK' if ok else 'DIFF'}")
    for k in (3, 8):
        print("      parts", k, [(p['label'][:18], p['line'], p['printed'], p['sign'], p['abs']) for p in r[k]['parts']])
