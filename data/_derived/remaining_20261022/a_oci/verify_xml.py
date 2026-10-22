"""Read-only. For the 3 quarters (2024.4Q, 2025.1Q, 2025.2Q) read the OCI block of the SEPARATE-basis comprehensive income statement
(a) of the ORIGINAL filing (current cumulative column = the live master basis) and (b) of the LATER filing (prior cumulative column = latest comparative),
with the raw line number of every cell, and derive items 24,25,26,27,28,29,30,31,32 from the leaf rows.  Writes verify_xml.txt / verify_xml.json."""
import json, re, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"
sys.path.insert(0, str(EVD))
import stmt_parse as P
import stmt_lines as SL
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent

def num(t):
    t = t.strip().replace(",", "")
    if t in ("", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v

SPEC = {
 # quarter: (original dir, orig col index among numeric cells, later dir, later col idx, later sep range override)
 "2024.4Q": ("FY2024_Q4", 0, "FY2025_Q4", 1, None),
 "2025.1Q": ("FY2025_Q1", 1, "FY2026_Q1", 3, None),
 "2025.2Q": ("FY2025_Q2", 1, "FY2026_Q2", 3, (31094, 32494)),
}
def read_block(fy, colidx, override):
    path = SL.main_xml(fy)
    L = P.read_lines(path)
    lo, hi = override or P.sections(L)["sep_fs"]
    rows = P.rows_in_range(L, lo, hi)
    out, on = [], False
    for r in rows:
        if not r["cells"]:
            continue
        lab = r["cells"][0][0].replace("\u3000", "").strip()
        vals = r["cells"][1:]
        if lab.replace(" ", "") in ("당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익", "분기순이익(손실)", "반기순이익(손실)"):
            out.append(("NI", lab, num(vals[colidx][0]), vals[colidx][1]))
        if lab == "기타포괄손익":
            on = True
        if on:
            if colidx < len(vals):
                out.append(("ROW", lab, num(vals[colidx][0]), vals[colidx][1]))
            if lab.replace(" ", "").endswith("총포괄손익"):
                break
    return str(path.relative_to(ROOT)).replace("\\", "/"), out

def derive(rows):
    items, cites, leaf32 = {}, {}, []
    sect = None
    for kind, lab, v, ln in rows:
        if kind == "NI":
            items[24], cites[24] = v, ln
            continue
        l = lab.replace(" ", "")
        if l == "기타포괄손익":
            items[25], cites[25] = v, ln
        elif l.startswith("당기손익으로재분류되는"):
            sect = "R"
        elif l.startswith("당기손익으로재분류되지않는"):
            sect = "N"
        elif l.endswith("총포괄손익"):
            items[31], cites[31] = v, ln
        elif "채무증권평가손익" in l or "금융자산관련손익" in l:
            items[26], cites[26] = v, ln
        elif l.startswith("보험계약자산"):
            items[27], cites[27] = v, ln
        elif l.startswith("재보험계약자산"):
            items[30], cites[30] = v, ln
        elif sect == "R" and ("위험회피" in l):
            items[28], cites[28] = v, ln
        elif sect == "N" and ("지분증권평가손익" in l or "유가증권평가손익" in l):
            items[29], cites[29] = v, ln
        else:
            leaf32.append((lab, v, ln))
    items[32] = sum(v or 0 for _, v, _ in leaf32)
    cites[32] = [(lab, v, ln) for lab, v, ln in leaf32]
    return items, cites

res = {}
lines = []
for q, (ofy, oc, lfy, lc, ov) in SPEC.items():
    of, orows = read_block(ofy, oc, None)
    lf, lrows = read_block(lfy, lc, ov)
    oi, oc_ = derive(orows)
    li, lc_ = derive(lrows)
    res[q] = {"orig_file": of, "later_file": lf, "orig": {k: v / 1e6 if v is not None else None for k, v in oi.items()},
              "later": {k: v / 1e6 if v is not None else None for k, v in li.items()},
              "orig_cites": {str(k): c for k, c in oc_.items()}, "later_cites": {str(k): c for k, c in lc_.items()}}
    lines.append(f"== {q}  ORIGINAL {of} (col idx {oc})   LATER {lf} (col idx {lc})")
    for it in (24, 25, 26, 27, 28, 29, 30, 31, 32):
        o, l = oi.get(it), li.get(it)
        oc2 = oc_.get(it); lc2 = lc_.get(it)
        lines.append(f"  item {it:2d}: orig {('None' if o is None else f'{o/1e6:,.6f}'):>18s} L{oc2 if it != 32 else [x[2] for x in oc2]}   later {('None' if l is None else f'{l/1e6:,.6f}'):>18s} L{lc2 if it != 32 else [x[2] for x in lc2]}")
    for tag, rr in (("orig", orows), ("later", lrows)):
        pass
    lines.append("  leaf rows of item 32 (orig): " + "; ".join(f"{a}={b/1e6:,.3f}@L{c}" for a, b, c in oc_[32]))
    lines.append("  leaf rows of item 32 (later): " + "; ".join(f"{a}={b/1e6:,.3f}@L{c}" for a, b, c in lc_[32]))
    for tag, ii in (("orig", oi), ("later", li)):
        parts = sum(ii.get(k) or 0 for k in (26, 27, 28, 29, 30, 32))
        lines.append(f"  {tag}: 25 - (26+27+28+29+30+32) = {(ii[25] - parts)/1e6:+.6f} mn;  31 - (24+25) = {(ii[31] - ii[24] - ii[25])/1e6:+.6f} mn")
(OUT / "verify_xml.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
(OUT / "verify_xml.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\n".join(lines))
