"""k5: KR0104 2023.1Q / 2023.2Q -- read the separate-basis income statement of the ORIGINAL filing (FY2023_Q1/Q2, old dialect, 백만원)
and of the LATER filing (FY2024_Q1/Q2 prior YTD column, 원) with filing line numbers.  READ-ONLY -> k5_kr0104_read.json/.txt"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
import stmtlib as S

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0104"
out = {}
txt = []
for q in ("2023.1Q", "2023.2Q"):
    res = {}
    for kind, fy in (("orig", M.fy_of(q)), ("later", M.later_fy(q))):
        xmls = M.main_xmls(CODE, fy)
        path = xmls[0]
        lines = M.read_lines(path)
        tabs = S.statement_tables(lines)
        txt.append(f"=== {q} {kind} {M.rel(path)} lines={len(lines)} sep={S.sep_section(lines)} stmt_tables={[(t['start'], t['end']) for t in tabs]}")
        t = tabs[0]
        rows = S.read_statement(lines, t)
        res[kind] = {"file": M.rel(path), "table": [t["start"], t["end"]], "rows": []}
        for r in rows:
            nums = [v for v in r["vals"] if v[0] is not None]
            res[kind]["rows"].append({"label": r["label"], "tr": r["tr_line"], "vals": [[v[0], v[1], v[2]] for v in r["vals"]]})
            if nums:
                txt.append(f"  R{r['tr_line']} [{r['label'][:34]}] " + " | ".join(f"{v[2]}@{v[1]}" for v in r["vals"]))
    out[q] = res
M.MEASURE.joinpath("k5_kr0104_read.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("k5_kr0104_read.txt").write_text("\n".join(txt), encoding="utf-8")
print(len(txt), "lines")
