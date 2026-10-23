# -*- coding: utf-8 -*-
import io
p = "x01_verify_p2.py"
s = io.open(p, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (s.count(old), old[:80])
    s = s.replace(old, new)


# --- ABL helper bug: the section dict is already selected
rep("""        def cv_(d, sec, lab):
            r = d[sec][lab]
            n = r["nums"][col]
            return n[0], n[1], n[2]""", """        def cv_(d, lab):
            r = d[lab]
            n = r["nums"][col]
            return n[0], n[1], n[2]""")
rep("""        val = lambda d, lab: cv_(d, d_name[id(d)], lab)[0]  # noqa: E731
        d_name = {id(R): "보험수익", id(RR): "재보험수익", id(Cc): "보험서비스비용", id(RC): "재보험비용"}
        g = lambda d, lab: (cv_(d, d_name[id(d)], lab)[0] if lab in d else 0.0)  # noqa: E731""", """        g = lambda d, lab: (cv_(d, lab)[0] if lab in d else 0.0)  # noqa: E731""")

# --- row label count (to tell the section total row from the first detail row in the 동양 classic dialect)
rep("""            rows.append(dict(tr=k + 1, label=(lab_cells[0]["text"] if lab_cells else ""), key=ns(" ".join(c["text"] for c in lab_cells[:2])), key1=ns(lab_cells[0]["text"]) if lab_cells else "", cells=cells, nums=nums))""",
    """            rows.append(dict(tr=k + 1, label=(lab_cells[0]["text"] if lab_cells else ""), key=ns(" ".join(c["text"] for c in lab_cells[:2])), key1=ns(lab_cells[0]["text"]) if lab_cells else "", nlab=len(lab_cells), cells=cells, nums=nums))""")
rep("""        tot_rev = [r for r in rev_rows if r["key1"] in ("보험수익",) and len(r["nums"]) == 2][-1] if q == "2024.2Q" else rowby(rev_rows, "보험수익", excl=(",",)) if False else [r for r in rev_rows if r["key"] == "보험수익" and len(r["nums"]) == 2][-1]""",
    """        tot_rev = [r for r in rev_rows if r["key1"] == "보험수익" and r["nlab"] == 1 and len(r["nums"]) == 2][0] if q == "2024.2Q" else [r for r in rev_rows if r["key"] == "보험수익" and len(r["nums"]) == 2][-1]""")
rep("""            tot_cost = rowby(cost_rows, "발행한보험계약에서생기는보험서비스비용") if False else [r for r in cost_rows if "보험서비스비용" in r["key"] and r["key"].count("보험서비스비용") >= 1 and "실제" not in r["key"] and len(r["nums"]) == 2][0]""",
    """            tot_cost = [r for r in cost_rows if r["key1"] == "발행한보험계약에서생기는보험서비스비용" and r["nlab"] == 1 and len(r["nums"]) == 2][0]""")

# --- 현대해상: quarters that are not planned must equal the master
rep("""        for itm, v in ((5, v5), (9, v9), (10, v10)):
            e = PLANNED[("KR0009", itm, q)]
            check(abs(e["value"] - v) < 5e-7, f"현대해상 {q} item {itm}: planned {e['value']} != re-read {v}")""",
    """        for itm, v in ((5, v5), (9, v9), (10, v10)):
            e = PLANNED.get(("KR0009", itm, q))
            if e is not None:
                check(abs(e["value"] - v) < 5e-7, f"현대해상 {q} item {itm}: planned {e['value']} != re-read {v}")
            else:
                check(abs(mv("KR0009", itm, q) - v) < 5e-7, f"현대해상 {q} item {itm}: not planned and master {mv('KR0009', itm, q)} != re-read {v}")""")
rep("""        if "three_month" in rec:
            tm = rec["three_month"][0]""", """        if "three_month" in rec and q in ("2023.2Q", "2023.3Q"):
            tm = rec["three_month"][0]""")
rep("""            prev = "2023.1Q" if q == "2023.2Q" else "2023.2Q"
            pv = {5: PLANNED[("KR0009", 5, prev)]["value"] if ("KR0009", 5, prev) in PLANNED else mv("KR0009", 5, prev),""", """            prev = "2023.1Q" if q == "2023.2Q" else "2023.2Q"
            pv = {5: PLANNED[("KR0009", 5, prev)]["value"] if ("KR0009", 5, prev) in PLANNED else mv("KR0009", 5, prev),""")

# --- OCI: only the planned buckets (KR0032 2023.2Q is held)
rep("""    for key, o in oci.items():
        code, q = key.split("|")
        rel = o["file"]""", """    for key, o in oci.items():
        code, q = key.split("|")
        if (code, 25, q) not in PLANNED:
            print(f"  OCI {key}: held (not planned) - skipped")
            continue
        rel = o["file"]""")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
