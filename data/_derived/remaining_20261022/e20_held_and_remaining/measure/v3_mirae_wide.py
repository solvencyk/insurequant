"""v3_mirae_wide: independent re-read of the 미래에셋생명 CSM vector (issued contracts, separate basis) from the LATER filing's wide measurement-component roll-forward
(FY2025 Q2/Q3 layout: 5 products x [PV, RA, CSM(수정소급 / 공정가치 / 그 밖의)] = 25 value columns, unit 원).  CSM = sum of the three CSM sub-columns of every product.
The pair of tables (당기/전기) is told apart by the opening CSM (prior year-start 20,214.5 eok).  READ-ONLY.
usage: v3_mirae_wide.py <FY_Q> [<FY_Q> ...] -> v3_mirae_wide.txt"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code = "KR0079"
NV = 25
CSM_IDX = [p * 5 + k for p in range(5) for k in (2, 3, 4)]
ROWS = {  # key -> (list of label prefixes (normalised), which row occurrence)
    "open": ("자산인보험계약의기초장부금액", "부채인보험계약의기초장부금액"),
    "new": ("처음인식한계약의효과",),
    "adj": ("보험계약마진을조정하는변동",),
    "amort": ("보험수익,서비스의이전으로당기손익에인식한보험계약마진",),
    "int": ("당기손익인식보험금융손익",),
    "close": ("자산인보험계약의기말장부금액", "부채인보험계약의기말장부금액"),
}
out = []
JS = {}
for fy in sys.argv[1:]:
    path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    note_from = None
    for ln, tt in S.titles(lines):
        if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
            note_from = ln
    out.append(f"##### {M.rel(path)} separate notes from L{note_from}")
    for t in M.iter_tables(lines):
        if note_from and t["start"] < note_from:
            continue
        if not any(M.norm_label(r["cells"][0]["text"]).startswith("부채인보험계약의기초장부금액") for r in t["rows"] if r["cells"]):
            continue
        vals = {}
        for r in t["rows"]:
            cells = r["cells"]
            if len(cells) < NV + 1:
                continue
            lab = " ".join(M.norm_label(c["text"]) for c in cells[: len(cells) - NV])
            vs = cells[-NV:]
            csm = sum((vs[i]["val"] or 0.0) for i in CSM_IDX)
            lines_csm = [vs[i]["line"] for i in CSM_IDX]
            for key, pref in ROWS.items():
                for pf in pref:
                    if lab.replace(" ", "").endswith(pf) or lab.replace(" ", "").startswith(pf) or pf in lab.replace(" ", ""):
                        vals.setdefault(key, []).append((csm, r["tr_line"], lines_csm[0], lines_csm[-1]))
        if not vals:
            continue
        s = {k: sum(x[0] for x in v) / 1e8 for k, v in vals.items()}
        if not all(k in s for k in ("open", "new", "amort", "int", "close")):
            out.append(f"  T{t['start']}: incomplete rows {list(vals)}")
            continue
        s["assump"] = s["close"] - (s["open"] + s["new"] + s["int"] + s["amort"])
        vec = [round(s[k], 1) for k in ("open", "new", "int", "assump", "amort", "close")]
        out.append(f"  T{t['start']}-{t['end']} nrows={len(t['rows'])}: 억원 [기초,신계약,이자,가정,상각,기말]={vec}")
        JS.setdefault(fy, []).append({"file": path.name, "table_start": t["start"], "vec": vec, "rows": {k: [{"row_line": a, "cell_lines": [c, d], "eok": round(x / 1e8, 2)} for x, a, c, d in v] for k, v in vals.items()}})
        for k in ("open", "new", "int", "amort", "close"):
            out.append(f"       {k}: " + "; ".join(f"R{a} cells L{c}..L{d} sum={x / 1e8:,.2f}" for x, a, c, d in vals[k]))
M.MEASURE.joinpath("v3_mirae_wide.json").write_text(json.dumps(JS, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("v3_mirae_wide.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
