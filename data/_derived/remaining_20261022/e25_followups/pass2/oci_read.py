# -*- coding: utf-8 -*-
"""READ-ONLY pass2 (tickets item 6: KR0032 NH농협손해보험 / KR0082 DB생명 2023.1Q-2023.2Q OCI items 25-32).  Reads the separate-basis comprehensive income statement ('4. 재무제표' table, 원) of the filing that prints
the quarter as the PRIOR-period column (FY2024 Q1 / Q2), cumulative column (statement columns = [당기 3개월, 당기 누적, 전기 3개월, 전기 누적] -> prior cum = 4th numeric cell), and builds the production items
  25 = 기타포괄손익   26/27/28/29/30/32 = leaf rows classified by e21_read.classify_leaf (26 FVOCI 채무증권 / 27 보험계약금융손익 / 28 위험회피 파생 / 29 FVOCI 지분증권 / 30 재보험금융 / 32 residual leaf bucket)
  31 = 총포괄손익  (24 = 당기순이익 is only shown, never changed)
Checks: 25 = sum of its leaf rows, 31 = 24 + 25 (원), 25 = 26+27+28+29+30+32; 3-month prior column for the single-quarter seam."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, M = P.T, P.M
SECT_NONRECLASS = ("후속적으로당기손익으로재분류되지않는", "당기손익으로재분류되지않는", "후속적으로당기손익으로재분류되지아니하는")


def classify(lab, sect):
    n = P.nl(lab)
    if "신용손실" in n or "손상충당금" in n or "대손충당금" in n:
        return 32
    if "위험회피" in n:
        return 28
    if "재보험" in n and "금융" in n:
        return 30
    if ("보험계약" in n or "보험금융" in n) and "금융" in n:
        return 27
    if "공정가치측정" in n:
        if "채무증권" in n or "채무상품" in n:
            return 26
        if "지분증권" in n or "지분상품" in n:
            return 29
        return 26 if sect == "R" else (29 if sect == "N" else 26)
    return 32


def read(code, q, fy):
    path = P.main_path(code, fy)
    lines = P.M.read_lines(path)
    cand = []
    for t in M.iter_tables(lines):
        blob = P.nl(P._TAGRE.sub("", " ".join(lines[t["start"] - 1:t["end"]])))
        if "총포괄손익" not in blob or "기타포괄손익" not in blob or not any(k in blob for k in ("당기순이익", "반기순이익", "분기순이익")):
            continue
        if "연결" in t["title"] or "요약" in t["title"]:
            continue
        cand.append(t)
    cand = [t for t in cand if "재무제표" in t["title"]]
    if len(cand) != 1:
        raise RuntimeError(f"{code} {fy}: {len(cand)} separate statement tables {[(t['start'], t['title']) for t in cand]}")
    t = cand[0]
    rows = P.E.rows_full23(lines, t["start"], t["end"])
    unit = T.find_unit(lines, t, span=300)
    assert unit == "원", unit
    # header words: columns
    hdr = P.nl(" ".join(c["text"] for r in rows[:4] for c in r["cells"]))
    # locate the OCI rows
    labs = [P.lab(r) for r in rows]
    i25 = next(i for i, L in enumerate(labs) if re.match(r"^(Ⅷ|Ⅸ|IX|VIII|X)?\.?기타포괄손익$", L) or L.endswith(".기타포괄손익") or L == "기타포괄손익")
    i31 = next(i for i, L in enumerate(labs) if i > i25 and "총포괄손익" in L)
    r24 = [r for r, L in zip(rows, labs) if re.search(r"(당기|반기|분기)순이익", L) and "조정" not in L and "귀속" not in L and "주당" not in L][0]
    n_cols = len(P.nums(rows[i25]))
    assert n_cols in (2, 4), n_cols
    PRIOR_CUM = n_cols - 1
    PRIOR_3M = 2 if n_cols == 4 else None
    leafs, sect = [], None
    for r in rows[i25 + 1:i31]:
        L = P.lab(r)
        nn = P.nums(r)
        key = P.nl(P.rowtext(r))
        if not nn:
            continue
        if any(s in key for s in SECT_NONRECLASS) and "재분류되지않는" in key:
            sect = "N"
            continue
        if "재분류될수있는" in key or "재분류되는" in key:
            sect = "R"
            continue
        # section subtotal rows (print a number) are recognised by label
        leafs.append((r, nn))
    return dict(path=path, lines=lines, table=t, rows=rows, unit=unit, n_cols=n_cols, prior_cum=PRIOR_CUM, prior_3m=PRIOR_3M, i25=i25, i31=i31, r24=r24, leafs=leafs, labs=labs)


def build(code, q, fy):
    d = read(code, q, fy)
    rows, labs = d["rows"], d["labs"]
    pc, p3 = d["prior_cum"], d["prior_3m"]
    cellv = lambda r, col: (lambda c: dict(v=c[0], line=c[1], text=c[2]))(P.nums(r)[col])  # noqa: E731
    out = dict(file=M.rel(d["path"]), fy=fy, quarter=q, table=d["table"]["start"], n_cols=d["n_cols"], unit=d["unit"])
    out["i24"] = cellv(d["r24"], pc)
    out["i25"] = cellv(rows[d["i25"]], pc)
    out["i31"] = cellv(rows[d["i31"]], pc)
    # leaf rows: walk the rows between 25 and 31 with section tracking (N = 재분류되지 않는, R = 재분류될 수 있는)
    sect, leafs = None, []
    for r in rows[d["i25"] + 1:d["i31"]]:
        key = P.nl(P.rowtext(r))
        nn = P.nums(r)
        if "재분류되지않는" in key or "재분류되지아니하는" in key:
            sect = "N"
            sub = ("N", r)
            continue
        if "재분류될수있는" in key or "재분류되는" in key:
            sect = "R"
            continue
        if not nn:
            continue
        leafs.append((sect, r))
    items = {26: [], 27: [], 28: [], 29: [], 30: [], 32: []}
    detail = []
    for sect, r in leafs:
        cls = classify(P.rowtext(r), sect)
        c = cellv(r, pc)
        c3 = cellv(r, p3) if p3 is not None else None
        items[cls].append(dict(label=P.rowtext(r), cell=c, cell3m=c3))
        detail.append((cls, P.rowtext(r), c))
    out["leafs"] = {str(k): v for k, v in items.items()}
    mn = lambda x: x / 1e6  # noqa: E731
    vals = {25: mn(out["i25"]["v"]), 31: mn(out["i31"]["v"])}
    for k in (26, 27, 28, 29, 30, 32):
        vals[k] = sum(mn(x["cell"]["v"]) for x in items[k])
    out["vals_mn"] = vals
    out["residual_check"] = mn(out["i25"]["v"]) - sum(vals[k] for k in (26, 27, 28, 29, 30, 32))
    out["ni_oci_total_check_won"] = out["i31"]["v"] - (out["i24"]["v"] + out["i25"]["v"])
    if p3 is not None:
        out["i25_3m"] = cellv(rows[d["i25"]], p3)
        out["i31_3m"] = cellv(rows[d["i31"]], p3)
        out["i24_3m"] = cellv(d["r24"], p3)
        out["vals_3m_mn"] = {25: mn(out["i25_3m"]["v"]), 31: mn(out["i31_3m"]["v"])}
        for k in (26, 27, 28, 29, 30, 32):
            out["vals_3m_mn"][k] = sum(mn(x["cell3m"]["v"]) for x in items[k])
    return out, detail


if __name__ == "__main__":
    live = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] in ("KR0032", "KR0082")}
    res, txt = {}, []
    for code, q, fy in [("KR0032", "2023.1Q", "FY2024_Q1"), ("KR0032", "2023.2Q", "FY2024_Q2"), ("KR0082", "2023.1Q", "FY2024_Q1"), ("KR0082", "2023.2Q", "FY2024_Q2")]:
        o, detail = build(code, q, fy)
        res[f"{code}|{q}"] = o
        L = [f"##### {code} {q} <- {fy} {o['file']} table@L{o['table']} ({o['n_cols']} numeric cols, prior cum = last)"]
        L.append(f"  24 printed {o['i24']['text']}@L{o['i24']['line']} (master {live.get((code, q, 24), {}).get('값')}); 25 {o['i25']['text']}@L{o['i25']['line']}; 31 {o['i31']['text']}@L{o['i31']['line']}")
        for cls, lab, c in detail:
            L.append(f"    leaf -> {cls}: {lab[:44]:44s} {c['text']}@L{c['line']}")
        L.append("  items (mn): " + " ".join(f"{k}={v:,.6f}" for k, v in sorted(o["vals_mn"].items())))
        L.append(f"  residual 25 - sum(26..30,32) = {o['residual_check']:.6f}; 31 - (24+25) = {o['ni_oci_total_check_won']:,.0f} 원")
        L.append("  master: " + " ".join(f"{k}={live.get((code, q, k), {}).get('값')}" for k in (25, 26, 27, 28, 29, 30, 31, 32)))
        if "vals_3m_mn" in o:
            L.append("  prior 3M (mn): " + " ".join(f"{k}={v:,.6f}" for k, v in sorted(o["vals_3m_mn"].items())))
        for ln in L:
            print(ln)
            txt.append(ln)
    json.dump(res, open(f"{P.EVP}/oci_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(f"{P.EVP}/oci_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(txt) + "\n")
