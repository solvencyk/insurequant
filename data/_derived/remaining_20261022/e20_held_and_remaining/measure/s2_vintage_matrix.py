"""s2: CSM vintage matrix per company x fiscal year from the 2026-10-12 dry-run prior scan + the live-master snapshot (READ-ONLY).
For each company and FY, for Q1..Q4: master (original) open/close, later-filing comparative (prior column) open/close, status, fidelity.
Also evaluates the within-FY opening spread (WFY) and cross-FY continuity of three combinations: ORIGINAL (status quo), LATEST (per quarter, where readable),
and writes the table to s2_vintage_matrix.txt/.csv"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
P = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/csm_prior_scan_v2.csv")
want = sys.argv[1].split(",")
with open(P, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
csm = M.load_csm()


def fl(x):
    try:
        return float(x)
    except Exception:
        return None


out, csvrows = [], []
for code in want:
    name = None
    scan = {}
    for r in rows:
        if r["kr"] == code:
            name = r["name"]
            scan[r["prior_q"]] = r
    out.append(f"##### {code} {name}")
    for fy in ("2023", "2024"):
        out.append(f"  FY{fy}:  q | master open->close | later-comparative open->close (status/fid/diff) | later filing")
        for qn in "1234":
            q = f"{fy}.{qn}Q"
            m = csm.get((code, q), {})
            r = scan.get(q)
            mo, mc = m.get(1), m.get(6)
            if r:
                po, pc = fl(r["p1"]), fl(r["p6"])
                s = f"{r['status']}/{r['fidelity']}/{r['diff_items'] or '-'}"
                lf = r["later_q"]
            else:
                po = pc = None
                s, lf = "-", "-"
            out.append(f"     {q}  master {mo} -> {mc} | later {po} -> {pc}  ({s}) [{lf}]")
            csvrows.append([code, name, q, mo, mc, po, pc, s, lf])
txt = "\n".join(out)
M.MEASURE.joinpath("s2_vintage_matrix.txt").write_text(txt, encoding="utf-8")
with open(M.MEASURE / "s2_vintage_matrix.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["code", "name", "quarter", "master_open", "master_close", "later_open", "later_close", "status/fid/diff", "later_filing"])
    w.writerows(csvrows)
print(txt)
