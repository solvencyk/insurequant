"""v4_meritz_csm: independent re-read of the 메리츠화재 CSM vector (원수 일반모형, separate basis) from the LATER filing: the table '원수 일반모형 보험부채 상세변동내역' has columns
[PV, RA, 보험계약마진(수정소급법), 보험계약마진(공정가치법), 보험계약마진(그 외), 합계]; CSM = sum of the three CSM columns.  The prior-period table is told apart by the opening CSM
(2023 start 96,376.4 eok).  READ-ONLY.   usage: v4_meritz_csm.py <FY_Q> [<FY_Q> ...] -> v4_meritz_csm.txt"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code = "KR0001"
ROWS = {"open": ("기초순장부금액",), "new": ("신계약효과",), "adj": ("보험계약마진을조정하는추정치변동",), "amort": ("당기손익으로인식한보험계약마진금액",), "int": ("순보험금융손익",),
        "close": ("분기말순장부금액", "반기말순장부금액")}
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
        hdr = " ".join(c["text"] for r in t["rows"][:2] for c in r["cells"])
        if "보험계약마진 (수정소급법)" not in hdr or "원수 일반모형" not in (t["caption"] or ""):
            continue
        vals = {}
        for r in t["rows"]:
            cells = r["cells"]
            if len(cells) < 7:
                continue
            lab = M.norm_label(cells[0]["text"])
            vs = cells[-6:]
            csm = sum((vs[i]["val"] or 0.0) for i in (2, 3, 4))
            for key, pref in ROWS.items():
                if lab in pref:
                    vals[key] = (csm, r["tr_line"], vs[2]["line"], vs[4]["line"])
        if not all(k in vals for k in ("open", "new", "adj", "amort", "int", "close")):
            out.append(f"  T{t['start']}: incomplete {list(vals)}")
            continue
        v = [vals[k][0] / 100.0 for k in ("open", "new", "int", "adj", "amort", "close")]
        out.append(f"  T{t['start']}-{t['end']}: 억원 [기초,신계약,이자,조정,상각,기말]={[round(x, 1) for x in v]}  (잔차 기말-합={v[5] - sum(v[:5]):+.2f})")
        JS.setdefault(fy, []).append({"file": path.name, "table_start": t["start"], "vec": [round(x, 1) for x in v], "rows": {k: {"row_line": vals[k][1], "cell_lines": [vals[k][2], vals[k][3]], "eok": round(vals[k][0] / 100.0, 2)} for k in vals}})
        for k in ("open", "new", "int", "adj", "amort", "close"):
            c, tr, l0, l1 = vals[k]
            out.append(f"       {k}: row L{tr} CSM cells L{l0}..L{l1} = {c / 100.0:,.2f} eok")
M.MEASURE.joinpath("v4_meritz_csm.json").write_text(json.dumps(JS, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("v4_meritz_csm.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
