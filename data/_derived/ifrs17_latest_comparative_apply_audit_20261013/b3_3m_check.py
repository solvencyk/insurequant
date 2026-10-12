import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
cells = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["kind"] == "3m_as_cumulative"]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/b3_3m_check.txt", "w", encoding="utf-8")
by = {}
for c in cells: by.setdefault((c["code"], re.search(r"rcept (\d+)", c["source_ref"]).group(1)), []).append(c)
for (code, rc), cs in by.items():
    p = find_xml(code, "FY2023_Q2", rc)[0]
    tabs = [t for t in load_tables(p) if is_statement(t)]
    out.write(f"===== {code} {rc}: {len(tabs)} statement-like tables: idx {[t['idx'] for t in tabs]}\n")
    for c in cs:
        it = int(c["item"]); new = float(c["new"]); old = float(c["old"])
        q1 = master.get((code, "2023.1Q", it)); q1v = float(q1["값"]) if q1 and q1.get("값") not in (None, "") else None
        out.write(f" item{it} {c['item_name']}: old={old} new={new} Q1master={q1v}\n")
        for t in tabs:
            rows = stmt_rows(t)
            v = define(rows, it)
            if v is None: out.write(f"    table{t['idx']}: definition not found\n"); continue
            # unit: values likely in won -> convert to million won
            mx = max(abs(x) for x in v) if v else 0
            scale = 1.0
            for s in (1e-6, 1e-3, 1.0):
                if mx * s < 1e9 and mx * s > 0: pass
            # choose scale so cumulative col matches new in magnitude
            out.write(f"    table{t['idx']} line{t['line']} cols={[round(x) for x in v]}\n")
