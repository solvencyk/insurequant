"""stmt_rows: print statement rows of the LATER filing (separate) whose label contains any of the given substrings, with cells+lines (READ-ONLY)
usage: stmt_rows.py <code> <FY_Q> <sub1,sub2,..>"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M, stmtlib as S
sys.stdout.reconfigure(encoding="utf-8")
code, fy, subs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
lines = M.read_lines(path)
tabs = S.statement_tables(lines)
print("#####", M.rel(path), "statement tables:", [(t["start"], t["end"]) for t in tabs])
t = tabs[0]
for r in S.read_statement(lines, t):
    if any(s in r["label"] for s in subs):
        print(f"  R{r['tr_line']} [{r['label'][:40]}] " + " | ".join(f"{v[2]}@{v[1]}" for v in r["vals"]))
