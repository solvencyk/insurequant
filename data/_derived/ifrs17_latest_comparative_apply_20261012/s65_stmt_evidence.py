"""Read-only: statement-level (Tier-1) evidence from the RAW XML, independent reader xmltab.py.

(a) latest-comparative PL blocks of KR0008 / KR0011 (later filing, 전기 누적 = 4th numeric column of the 포괄손익계산서 [당3M, 당누적, 전3M, 전누적]):
    every Tier-1 item (1, 15-32) of the plan is re-computed from the printed statement lines with the builder's documented formulas and compared with the plan value.
(b) the 3-month-as-cumulative corrections of the original 2023.2Q filings (흥국화재, 롯데손해보험, 한화손해보험, 한화생명, 푸본현대생명): current cumulative column (2nd numeric).
Output evidence_pl_tier1.json / .txt   (per cell: derived value, plan/new value, ok flag, XML file, table index and the XML lines of every printed row used)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
plan = json.loads((HERE / "plan_diff.json").read_text(encoding="utf-8"))


def norm(s):
    return re.sub(r"\s+", "", s or "")


def clean(s):
    s = norm(s)
    return re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?|^[IVXlvx]+\.|^\d+\.|^\(\d+\)|^\d+\)", "", s)


def xml_of(kr, fy_q):
    d = sorted((ROOT / "data/dart" / fy_q / "raw").glob(f"{kr}_*"))[0]
    return sorted(d.glob("*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]


def stmt_tables(xml):
    out = []
    for t in X.load_tables(str(xml)):
        labs = [clean(r.cells[0]) for r in t.rows if r.cells]
        if not any(re.search(r"법인세(비용)?차감전", l) for l in labs):
            continue
        hdr = "".join(norm(c) for r in t.rows[:4] for c in r.cells)
        if "3개월" not in hdr or "누적" not in hdr:
            continue
        out.append((t, any(norm(c) == "주석" for r in t.rows[:3] for c in r.cells)))
    return out


def nums_of(r, has_note):
    cells = r.cells[1:]
    if has_note and cells:
        cells = cells[1:]
    n = []
    for c in cells:
        v = X.printed_to_float(c)
        if v is not None:
            n.append((v, c))
        elif c.strip() in ("-", "0"):
            n.append((0.0, c))
    return n


def line_map(t, has_note):
    m = {}
    for r in t.rows:
        if not r.cells:
            continue
        lab = clean(r.cells[0])
        n = nums_of(r, has_note)
        if len(n) >= 4:
            m.setdefault(lab, (n, r.line, r.cells[0]))
    return m


PICK = {
    1: ["보험손익", "보험서비스결과"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익", "영업이익(손실)"], 22: ["법인세비용차감전순이익", "법인세차감전순이익", "법인세차감전순이익(손실)"],
    23: ["법인세비용"], 24: ["분기순이익", "반기순이익", "3분기순이익", "당기순이익"], 25: ["기타포괄손익"], 31: ["총포괄손익", "분기총포괄손익", "반기총포괄손익", "3분기총포괄손익"],
    26: ["기타포괄손익-공정가치측정금융자산관련손익"], 27: ["보험계약자산(부채)순금융손익"], 28: ["현금흐름위험회피파생상품평가손익"], 29: ["기타포괄손익-공정가치측정유가증권평가손익"],
    30: ["재보험계약자산(부채)순금융손익"],
}


def get(m, labels, col):
    for lb in labels:
        if lb in m:
            n, line, orig = m[lb]
            return n[col][0], n[col][1], line, orig
    return None


def unit_div(m, col):
    """printed unit of the statement: 원 (values ~1e9..1e12) -> 1e6 ; 백만원 -> 1"""
    g = get(m, ["법인세비용차감전순이익", "법인세차감전순이익", "법인세차감전순이익(손실)", "영업이익", "영업이익(손실)", "분기순이익", "반기순이익"], col)
    return 1e6 if (g is not None and abs(g[0]) >= 5e7) else 1.0


def derive(m, col):
    """-> {item: (value_in_백만원, [(line, label, printed), ...])}"""
    D = unit_div(m, col)
    out = {}
    for it, labs in PICK.items():
        g = get(m, labs, col)
        if g is not None:
            v, pr, line, orig = g
            out[it] = (abs(v) / D if it in (16, 23) else v / D, [(line, orig, pr)])
    comp = []
    tot = 0.0
    for lab, sg in (("보험금융수익", +1), ("보험금융비용", -1), ("재보험금융수익", +1), ("재보험금융비용", -1)):
        g = get(m, [lab], col)
        if g is not None:
            v, pr, line, orig = g
            tot += sg * abs(v) if sg < 0 else v
            comp.append((line, orig, pr))
    if comp:
        out[19] = (tot / D, comp)
        if 17 in out:
            out[18] = (out[17][0] - out[19][0], out[17][1] + comp)
    g = get(m, ["영업외손익"], col)
    if g is not None:
        out[21] = (g[0] / D, [(g[2], g[3], g[1])])
    else:
        a, b = get(m, ["영업외수익"], col), get(m, ["영업외비용"], col)
        if a is not None and b is not None:
            out[21] = ((a[0] - abs(b[0])) / D, [(a[2], a[3], a[1]), (b[2], b[3], b[1])])
    if all(i in out for i in (25, 26, 27, 28, 29, 30)):
        out[32] = (out[25][0] - sum(out[i][0] for i in (26, 27, 28, 29, 30)), [])
    if 15 not in out and any(i in out for i in (20, 22)):
        out[15] = (0.0, [])          # no 기타영업수익 line in the statement -> builder convention 0.0
    return out


res = {}
lines = []
# (a) latest-comparative blocks (KR0008, KR0011): prior cumulative column = numeric index 3
blocks = sorted({c["block"] for c in plan["PL"] if c["code"] in ("KR0008", "KR0011")})
for blk in blocks:
    kr, q = blk.split("|")
    xml = xml_of(kr, f"FY{int(q[:4]) + 1}_Q{q[5]}")
    cells = {c["item"]: c for c in plan["PL"] if c["block"] == blk}
    sts = stmt_tables(xml)
    best = None
    for t, hn in sts:
        m = line_map(t, hn)
        d = derive(m, 3)
        match = sum(1 for it, c in cells.items() if it in d and abs(d[it][0] - c["new"]) <= 0.51)
        if best is None or match > best[0]:
            best = (match, t, d)
    match, t, d = best
    lines.append(f"=== {blk} <- {xml.name} table #{t.index} line {t.line}  (statement items matched {match}/{len([i for i in cells if i in d])})")
    res[blk] = {"xml": str(xml.relative_to(ROOT)).replace("\\", "/"), "table": t.index, "tline": t.line, "items": {}}
    for it in sorted(cells):
        c = cells[it]
        if it in d:
            ok = abs(d[it][0] - c["new"]) <= 0.51
            lines.append(f"  item {it:>2} plan {c['new']:>16,.6f}  statement-derived {d[it][0]:>16,.6f}  {'OK ' if ok else 'DIFF'} rows={[(l, lab[:14], pr) for l, lab, pr in d[it][1]]}")
            res[blk]["items"][it] = {"derived": d[it][0], "plan": c["new"], "ok": ok, "rows": [{"line": l, "label": lab, "printed": pr} for l, lab, pr in d[it][1]]}
        else:
            lines.append(f"  item {it:>2} plan {c['new']:>16,.6f}  (not a statement item: Tier-2 note item, see evidence_pl_notes)")

# (b) 3-month-as-cumulative corrections (original filings, current cumulative column = numeric index 1)
FIX = {
    "KR0005|2023.2Q": [1, 19, 20, 21, 22, 23, 24],
    "KR0003|2023.2Q": [19, 18],
    "KR0002|2023.2Q": [21],
    "KR0068|2023.2Q": [21],
    "KR0083|2023.2Q": [19, 18, 21],
}
live = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
fixplan = {}
for blk, items in FIX.items():
    kr, q = blk.split("|")
    xml = xml_of(kr, f"FY{q[:4]}_Q{q[5]}")
    sts = stmt_tables(xml)
    # the statement the master follows: the table whose cumulative column matches the master item 20 or 22 (same company/quarter)
    best = None
    for t, hn in sts:
        m = line_map(t, hn)
        d = derive(m, 1)
        match = 0
        for it in (20, 22, 24, 16, 17):
            if it in d and live.get((kr, q, it)) is not None:
                tol = 0.51 if float(live[(kr, q, it)]).is_integer() else 0.0012
                if abs(d[it][0] - abs(live[(kr, q, it)]) if it in (16, 23) else d[it][0] - live[(kr, q, it)]) <= tol:
                    match += 1
        if best is None or match > best[0]:
            best = (match, t, d, m)
    match, t, d, m = best
    lines.append(f"=== 3M-fix {blk} <- {xml.name} table #{t.index} line {t.line} (cumulative-column anchors matched {match})")
    res[blk + "|3Mfix"] = {"xml": str(xml.relative_to(ROOT)).replace("\\", "/"), "table": t.index, "tline": t.line, "items": {}}
    for it in items:
        old = live.get((kr, q, it))
        if it in d:
            new = d[it][0]
            lines.append(f"  item {it:>2} master-old {old!s:>16}  statement cumulative {new:>16,.6f}  rows={[(l, lab[:14], pr) for l, lab, pr in d[it][1]]}")
            res[blk + "|3Mfix"]["items"][it] = {"old": old, "derived_cum": new, "rows": [{"line": l, "label": lab, "printed": pr} for l, lab, pr in d[it][1]]}
        elif it == 18:
            lines.append("  item 18 = item 17 - item 19 (derived by the builder, recomputed after the item 19 correction)")
        else:
            lines.append(f"  item {it:>2} NOT derivable from the statement")
(HERE / "evidence_pl_tier1.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
(HERE / "evidence_pl_tier1.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
